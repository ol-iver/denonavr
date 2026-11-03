#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ssdp."""

import httpx
import pytest

from denonavr.ssdp import async_is_av_receiver, evaluate_scpd_xml


def get_sample_content(filename):
    """Return sample content form file."""
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return file.read()


@pytest.mark.parametrize(
    "model,expected_device",
    [
        (
            "AVR-X1600H",
            {
                "friendlyName": "Denon AVR-X1600H",
                "host": "10.0.0.0",
                "manufacturer": "Denon",
                "modelName": "Denon AVR-X1600H",
                "serialNumber": "XXX",
            },
        )
    ],
)
def test_evaluate(model, expected_device):
    """Test that the discovered device looks like expected."""
    url = "https://10.0.0.0/denon"
    body = get_sample_content(f"{model}_upnp.xml")
    device = evaluate_scpd_xml(url, body)
    assert device == expected_device


def _client(deviceinfo: dict) -> httpx.AsyncClient:
    """Create a client that answers Deviceinfo requests by port."""

    def handler(request: httpx.Request) -> httpx.Response:
        body = deviceinfo.get(request.url.port or 80)
        if body is None:
            raise httpx.ConnectError("unreachable", request=request)
        return httpx.Response(200, text=body)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "deviceinfo, expected",
    [
        ({8080: get_sample_content("AVC-X3700H-Deviceinfo-8080.xml")}, True),
        ({80: get_sample_content("AVR-X4100W-Deviceinfo.xml")}, True),
        ({80: get_sample_content("AVR-1713-Deviceinfo.xml")}, True),
        ({}, True),
        (
            {8080: "<Device_Info><CategoryName>SPEAKER</CategoryName></Device_Info>"},
            False,
        ),
        ({80: "not xml"}, True),
    ],
)
async def test_is_av_receiver(deviceinfo, expected):
    """Test that only devices reporting another category are rejected."""
    async with _client(deviceinfo) as client:
        assert await async_is_av_receiver("10.0.0.1", client, timeout=1) is expected
