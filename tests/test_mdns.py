# -*- coding: utf-8 -*-
"""Tests for mDNS discovery."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import denonavr
from denonavr.mdns import (
    FoundReceiver,
    MDNSListener,
    ServiceInfoRecord,
    async_query_receivers,
)

SERVICE_TYPE = "_heos-audio._tcp.local."
SERVICE_NAME = "Living Room._heos-audio._tcp.local."


def test_listener_add_update_remove_service():
    """Test that the listener tracks service changes."""
    zeroconf = MagicMock()
    first_info = MagicMock()
    second_info = MagicMock()
    zeroconf.get_service_info.side_effect = [first_info, second_info]
    listener = MDNSListener()

    listener.add_service(zeroconf, SERVICE_TYPE, SERVICE_NAME)
    assert [s.info for s in listener.services] == [first_info]

    listener.update_service(zeroconf, SERVICE_TYPE, SERVICE_NAME)
    assert [s.info for s in listener.services] == [second_info]

    listener.remove_service(zeroconf, SERVICE_TYPE, SERVICE_NAME)
    assert not listener.services


def test_listener_update_unknown_service_adds_it():
    """Test that updating an unknown service records it."""
    zeroconf = MagicMock()
    listener = MDNSListener()

    listener.update_service(zeroconf, SERVICE_TYPE, SERVICE_NAME)

    assert [s.name for s in listener.services] == [SERVICE_NAME]


@pytest.mark.asyncio
async def test_discover_combines_mdns_and_ssdp():
    """Test that SSDP data is preferred when both find the same host."""
    mdns_receivers = [
        FoundReceiver(
            name="Living Room",
            ip_address="192.168.1.10",
            model="AVR-X",
            network_id="id",
            did="did-1",
            serial_number=None,
        ),
        FoundReceiver(
            name="Bedroom",
            ip_address="192.168.1.11",
            model="AVR-S",
            network_id="id",
            did="did-2",
            serial_number="serial-2",
        ),
    ]
    ssdp_receivers = [
        {
            "host": "192.168.1.10",
            "modelName": "AVR-X",
            "friendlyName": "Living Room SSDP",
            "presentationURL": "http://192.168.1.10",
            "serialNumber": "serial-1",
        }
    ]
    with (
        patch("denonavr.async_query_receivers", AsyncMock(return_value=mdns_receivers)),
        patch(
            "denonavr.async_identify_denonavr_receivers",
            AsyncMock(return_value=ssdp_receivers),
        ),
    ):
        result = await denonavr.async_discover()

    by_host = {entry["host"]: entry for entry in result}
    assert set(by_host) == {"192.168.1.10", "192.168.1.11"}
    assert by_host["192.168.1.10"]["friendlyName"] == "Living Room SSDP"
    assert by_host["192.168.1.11"]["serialNumber"] == "serial-2"
    assert by_host["192.168.1.11"]["presentationURL"] is None


@pytest.mark.asyncio
async def test_discover_uses_did_without_serial_number():
    """Test that the mDNS device id is used if no serial number is found."""
    mdns_receivers = [
        FoundReceiver(
            name="Living Room",
            ip_address="192.168.1.10",
            model="AVR-X",
            network_id="id",
            did="did-1",
            serial_number=None,
        )
    ]
    with (
        patch("denonavr.async_query_receivers", AsyncMock(return_value=mdns_receivers)),
        patch("denonavr.async_identify_denonavr_receivers", AsyncMock(return_value=[])),
    ):
        result = await denonavr.async_discover()

    assert result[0]["serialNumber"] == "did-1"


@pytest.mark.asyncio
async def test_discover_without_mdns_results():
    """Test that discovery works if mDNS finds nothing."""
    with (
        patch("denonavr.async_query_receivers", AsyncMock(return_value=None)),
        patch("denonavr.async_identify_denonavr_receivers", AsyncMock(return_value=[])),
    ):
        assert await denonavr.async_discover() == []


def _service_record() -> ServiceInfoRecord:
    info = MagicMock()
    info.decoded_properties = {"model": "AVR-X", "networkid": "id", "did": "did-1"}
    info.parsed_addresses.return_value = ["192.168.1.10"]
    return ServiceInfoRecord(name="Living Room", type=SERVICE_TYPE, info=info)


def _patched_listener(services: list[ServiceInfoRecord]):
    listener = MDNSListener()
    listener.services = services
    return patch("denonavr.mdns.MDNSListener", return_value=listener)


@pytest.mark.asyncio
async def test_query_does_not_close_shared_zeroconf():
    """Test that a Zeroconf instance from the caller is used and not closed."""
    shared = MagicMock()
    shared.async_close = AsyncMock()
    with (
        patch("denonavr.mdns.AsyncZeroconf") as zeroconf_class,
        patch("denonavr.mdns.ServiceBrowser") as browser_class,
    ):
        result = await async_query_receivers(0, async_zeroconf=shared)

    assert result is None
    zeroconf_class.assert_not_called()
    shared.async_close.assert_not_awaited()
    assert browser_class.call_args.args[0] is shared.zeroconf
    browser_class.return_value.cancel.assert_called_once()


@pytest.mark.asyncio
async def test_query_closes_own_zeroconf():
    """Test that a Zeroconf instance created by the library is closed."""
    own = MagicMock()
    own.async_close = AsyncMock()
    with (
        patch("denonavr.mdns.AsyncZeroconf", return_value=own),
        patch("denonavr.mdns.ServiceBrowser") as browser_class,
    ):
        await async_query_receivers(0)

    own.async_close.assert_awaited_once()
    browser_class.return_value.cancel.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("own", [True, False])
async def test_query_stops_browser_when_cancelled(own):
    """Test that the browser is stopped if the query is cancelled."""
    zeroconf = MagicMock()
    zeroconf.async_close = AsyncMock()
    with (
        patch("denonavr.mdns.AsyncZeroconf", return_value=zeroconf),
        patch("denonavr.mdns.ServiceBrowser") as browser_class,
        patch("denonavr.mdns.asyncio.sleep", side_effect=asyncio.CancelledError),
    ):
        with pytest.raises(asyncio.CancelledError):
            await async_query_receivers(5, async_zeroconf=None if own else zeroconf)

    browser_class.return_value.cancel.assert_called_once()
    assert zeroconf.async_close.await_count == (1 if own else 0)


@pytest.mark.asyncio
async def test_query_uses_and_keeps_client_from_caller():
    """Test that an HTTP client from the caller is used and not closed."""
    client = MagicMock()
    client.aclose = AsyncMock()
    shared = MagicMock()
    with (
        patch("denonavr.mdns.ServiceBrowser"),
        _patched_listener([_service_record()]),
        patch(
            "denonavr.mdns._async_get_serial_number",
            new_callable=AsyncMock,
            return_value="serial-1",
        ) as get_serial,
    ):
        result = await async_query_receivers(
            0, async_zeroconf=shared, async_client=client
        )

    assert result is not None
    assert result[0].ip_address == "192.168.1.10"
    assert result[0].serial_number == "serial-1"
    assert get_serial.call_args.args[1] is client
    client.aclose.assert_not_awaited()


@pytest.mark.asyncio
async def test_query_closes_own_client():
    """Test that an HTTP client created by the library is closed."""
    shared = MagicMock()
    own_client = MagicMock()
    own_client.__aenter__ = AsyncMock(return_value=own_client)
    own_client.__aexit__ = AsyncMock(return_value=None)
    with (
        patch("denonavr.mdns.ServiceBrowser"),
        _patched_listener([_service_record()]),
        patch("denonavr.mdns.httpx.AsyncClient", return_value=own_client),
        patch(
            "denonavr.mdns._async_get_serial_number",
            new_callable=AsyncMock,
            return_value=None,
        ) as get_serial,
    ):
        await async_query_receivers(0, async_zeroconf=shared)

    assert get_serial.call_args.args[1] is own_client
    own_client.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
async def test_discover_passes_shared_objects_and_uses_short_default_timeout():
    """Test that discovery hands its arguments on and waits 2.5 s by default."""
    shared = MagicMock()
    client = MagicMock()
    query = AsyncMock(return_value=None)
    with (
        patch("denonavr.async_query_receivers", query),
        patch("denonavr.async_identify_denonavr_receivers", AsyncMock(return_value=[])),
    ):
        await denonavr.async_discover(async_zeroconf=shared, async_client=client)

    query.assert_awaited_once_with(2.5, async_zeroconf=shared, async_client=client)
