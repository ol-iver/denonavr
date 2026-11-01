#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of how often Deviceinfo.xml is fetched.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import itertools
from typing import List

import httpx
import pytest
from pytest_httpx import HTTPXMock

import denonavr

APPCOMMAND_URL = "/goform/AppCommand.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
STATUS_Z2_URL = "/goform/formZone2_Zone2XmlStatus.xml"
STATUS_Z3_URL = "/goform/formZone3_Zone3XmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"
DESCRIPTION_URL1 = "/description.xml"
DESCRIPTION_URL2 = "/upnp/desc/aios_device/aios_device.xml"

SAMPLE_PATHS = {
    STATUS_URL: "formMainZone_MainZoneXmlStatus",
    STATUS_Z2_URL: "formZone2_Zone2XmlStatus",
    STATUS_Z3_URL: "formZone3_Zone3XmlStatus",
    MAINZONE_URL: "formMainZone_MainZoneXml",
    DEVICEINFO_URL: "Deviceinfo",
    NETAUDIOSTATUS_URL: "formNetAudio_StatusXml",
    TUNERSTATUS_URL: "formTuner_TunerXml",
    HDTUNERSTATUS_URL: "formTuner_HdXml",
}

ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}

# An AVR_X_2016 receiver: it serves Deviceinfo.xml on port 8080 only, so the
# probe of port 80 is the miss every setup pays for.
RECEIVER_2016 = "AVR-X4300H"
# An AVR_X receiver, answering on port 80.
RECEIVER_X = "AVR-X2000"

# The read timeout the probe runs under, which is DenonAVRApi.timeout.
PROBE_READ_TIMEOUT = 2.0
# What every other reader of the same document takes.
DEFAULT_READ_TIMEOUT = 15.0

_HOSTS = itertools.count(1)


@pytest.fixture(name="host")
def host_fixture() -> str:
    """Return a host no other test has used.

    Responses are cached under their URL and an id() that CPython reuses
    once the object it named is collected, so tests sharing a host can be
    served a document an earlier one fetched.
    """
    number = next(_HOSTS)
    return f"10.0.{number // 256}.{number % 256}"


def get_sample_content(filename: str) -> str:
    """Return sample content form file."""
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return file.read()


def sample_matcher(receiver: str):
    """Return a request callback answering from receiver's sample files.

    A model that has no sample for a port answers 403 there, which is what
    a receiver serving the document on the other port does.
    """

    def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
        port_suffix = "-8080" if request.url.port == 8080 else ""
        try:
            if request.url.path in SAMPLE_PATHS:
                content = get_sample_content(
                    f"{receiver}-{SAMPLE_PATHS[request.url.path]}{port_suffix}.xml"
                )
            elif request.url.path == APPCOMMAND_URL:
                content = get_sample_content(
                    f"{receiver}-AppCommand{appcommand_suffix(request)}"
                    f"{port_suffix}.xml"
                )
            elif request.url.path in (DESCRIPTION_URL1, DESCRIPTION_URL2):
                content = get_sample_content("AVR-X1600H_upnp.xml")
            else:
                content = "DATA"
        except FileNotFoundError:
            return httpx.Response(
                status_code=403, content="Error 403: Forbidden\nAccess Forbidden"
            )
        return httpx.Response(status_code=200, content=content)

    return matcher


def appcommand_suffix(request: httpx.Request) -> str:
    """Return the sample file suffix for an AppCommand.xml request."""
    content = request.read().decode("utf-8")
    if "GetFriendlyName" in content:
        return "-setup"
    if "GetAllZoneSource" in content:
        return "-update"
    if "GetSurroundModeStatus" in content:
        return "-update-soundmode"
    return "-update-tonecontrol"


def deviceinfo_gets(httpx_mock: HTTPXMock) -> List[httpx.Request]:
    """Return the Deviceinfo.xml requests that were actually sent."""
    return [
        request
        for request in httpx_mock.get_requests()
        if request.url.path == DEVICEINFO_URL
    ]


def deviceinfo_ports(httpx_mock: HTTPXMock) -> List[int]:
    """Return the port of each Deviceinfo.xml request, in order."""
    return [request.url.port or 80 for request in deviceinfo_gets(httpx_mock)]


def read_timeout(request: httpx.Request) -> float:
    """Return the read timeout a request was sent with."""
    return request.extensions["timeout"]["read"]


class TestDeviceinfoFetchCount:
    """Test case for the Deviceinfo.xml fetches setup makes."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_one_zone_fetches_it_once_per_port(
        self, httpx_mock: HTTPXMock, host: str
    ):
        """Check that setup and the first poll cost one fetch per port.

        The probe has to find the port, so a receiver answering on 8080
        pays for the miss on 80. Nothing after that reads the document
        again: it is static, and the probe's answer is the source list's.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(host)
        await denon.async_setup()
        await denon.async_update()

        ports = deviceinfo_ports(httpx_mock)
        assert ports == [80, 8080]
        assert denon.input_func_list

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_extra_zones_fetch_it_again_for_nothing(
        self, httpx_mock: HTTPXMock, host: str
    ):
        """Check that a second and third zone cost no fetch of their own.

        The receiver type and its port are properties of the receiver, and
        every zone shares one api object, so the zones are answered from
        what the main zone's probe found.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(host, add_zones=ZONE2_ZONE3)
        await denon.async_setup()
        for zone_receiver in denon.zones.values():
            await zone_receiver.async_update()

        ports = deviceinfo_ports(httpx_mock)
        assert ports == [80, 8080]
        assert denon.zones["Zone2"].input_func_list
        assert denon.zones["Zone3"].input_func_list

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_a_receiver_answering_on_port_80_is_asked_once(
        self, httpx_mock: HTTPXMock, host: str
    ):
        """Check that a pre 2016 receiver pays for no miss at all."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_X))
        denon = denonavr.DenonAVR(host, add_zones=ZONE2_ZONE3)
        await denon.async_setup()
        for zone_receiver in denon.zones.values():
            await zone_receiver.async_update()

        ports = deviceinfo_ports(httpx_mock)
        assert ports == [80]


class TestProbeTimeout:
    """Test case for the read timeout the port probe runs under."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_the_probe_still_gives_up_early(
        self, httpx_mock: HTTPXMock, host: str
    ):
        """Check that a wrong port is still abandoned after the short wait.

        The probe is the one reader that cannot afford the default read
        timeout, because the endpoint takes very long to return 404, and
        sharing its answer with the later readers must not change that.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(host)
        await denon.async_setup()

        timeouts = [read_timeout(request) for request in deviceinfo_gets(httpx_mock)]
        assert timeouts == [PROBE_READ_TIMEOUT, PROBE_READ_TIMEOUT]

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_every_other_request_keeps_the_default(
        self, httpx_mock: HTTPXMock, host: str
    ):
        """Check that the short wait is not left behind on the api."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(host)
        await denon.async_setup()

        posts = [
            request
            for request in httpx_mock.get_requests()
            if request.url.path == APPCOMMAND_URL
        ]
        assert posts
        for request in posts:
            assert read_timeout(request) == DEFAULT_READ_TIMEOUT
