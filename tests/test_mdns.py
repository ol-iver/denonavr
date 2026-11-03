# -*- coding: utf-8 -*-
"""Tests for mDNS discovery."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import denonavr
from denonavr.mdns import FoundReceiver, MDNSListener

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
