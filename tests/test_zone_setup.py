#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for setting up several zones of one receiver."""

import asyncio

import httpx
import pytest
from pytest_httpx import HTTPXMock

import denonavr

from .test_denonavr import TestMainFunctions as SampleReceiver

ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}


@pytest.mark.asyncio
@pytest.mark.httpx_mock(can_send_already_matched_responses=True)
@pytest.mark.parametrize(
    "host,model,api_port,receiver_type",
    [
        # Hosts of their own: responses are cached under the URL and an id()
        # CPython reuses, so a shared host can be served another test's answer
        pytest.param("10.2.0.1", "AV7703", 8080, "avr-x-2016", id="avr-x-2016"),
        pytest.param("10.2.0.2", "AVR-3311CI", 80, "avr", id="avr"),
    ],
)
async def test_zone_setup_keeps_the_api_port(
    httpx_mock: HTTPXMock,
    host: str,
    model: str,
    api_port: int,
    receiver_type: str,
):
    """No zone's request follows another zone's probe to the wrong port."""
    wrong_port = 80 if api_port == 8080 else 8080
    samples = SampleReceiver()
    samples.testing_receiver = model
    requests = []

    async def receiver(request: httpx.Request) -> httpx.Response:
        port = request.url.port or 80
        requests.append((port, request.url.path))
        # A zone's setup overlaps its siblings only once requests take time
        await asyncio.sleep(0.018 if port == wrong_port else 0.005)
        if port == wrong_port and request.url.path.startswith("/goform/"):
            return httpx.Response(403 if api_port == 8080 else 404)
        return samples.custom_matcher(request)

    httpx_mock.add_callback(receiver)
    denon = denonavr.DenonAVR(host, add_zones=ZONE2_ZONE3)
    await denon.async_setup()

    assert [
        path
        for port, path in requests
        if port == wrong_port
        and path.startswith("/goform/")
        and path != "/goform/Deviceinfo.xml"
    ] == []
    assert denon._device.api.port == api_port  # pylint: disable=protected-access
    for zone in denon.zones.values():
        assert zone.receiver_type == receiver_type
