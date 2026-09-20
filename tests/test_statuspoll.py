#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the status poll shared by every zone.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import time
from typing import List

import httpx
import pytest
from pytest_httpx import HTTPXMock

import denonavr
from denonavr.exceptions import AvrForbiddenError

FAKE_IP = "10.0.0.0"

ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}

APPCOMMAND_URL = "/goform/AppCommand.xml"
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
STATUS_Z2_URL = "/goform/formZone2_Zone2XmlStatus.xml"
STATUS_Z3_URL = "/goform/formZone3_Zone3XmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"
DESCRIPTION_URL1 = "/description.xml"
DESCRIPTION_URL2 = "/upnp/desc/aios_device/aios_device.xml"

# An AVR_X_2016 receiver: its whole status update is one AppCommand.xml POST.
RECEIVER_2016 = "AVR-X4300H"
# An AVR_X receiver, which also serves the status XML interface.
RECEIVER_X = "AVR-X2000"


def get_sample_content(filename):
    """Return sample content form file."""
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return file.read()


def sample_matcher(receiver: str):
    """Return a request callback answering from receiver's sample files."""

    def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
        port_suffix = "-8080" if request.url.port == 8080 else ""
        paths = {
            STATUS_URL: "formMainZone_MainZoneXmlStatus",
            STATUS_Z2_URL: "formZone2_Zone2XmlStatus",
            STATUS_Z3_URL: "formZone3_Zone3XmlStatus",
            MAINZONE_URL: "formMainZone_MainZoneXml",
            DEVICEINFO_URL: "Deviceinfo",
            NETAUDIOSTATUS_URL: "formNetAudio_StatusXml",
            TUNERSTATUS_URL: "formTuner_TunerXml",
            HDTUNERSTATUS_URL: "formTuner_HdXml",
        }
        try:
            if request.url.path == APPCOMMAND_URL:
                content = get_sample_content(
                    f"{receiver}-AppCommand{appcommand_suffix(request)}"
                    f"{port_suffix}.xml"
                )
            elif request.url.path in (DESCRIPTION_URL1, DESCRIPTION_URL2):
                content = get_sample_content("AVR-X1600H_upnp.xml")
            elif request.url.path in paths:
                content = get_sample_content(
                    f"{receiver}-{paths[request.url.path]}{port_suffix}.xml"
                )
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


def poll_requests(httpx_mock: HTTPXMock, since: int) -> List[httpx.Request]:
    """Return the requests made after the first since ones."""
    return httpx_mock.get_requests()[since:]


def appcommand_posts(httpx_mock: HTTPXMock, since: int) -> List[httpx.Request]:
    """Return the AppCommand.xml posts made after the first since requests.

    The poll fetches Deviceinfo.xml as well; that is its own defect and
    counting it here would measure that instead.
    """
    return [
        request
        for request in poll_requests(httpx_mock, since)
        if request.url.path == APPCOMMAND_URL
    ]


class TestStatusPollCacheId:
    """Test case for one cache id covering a whole zone loop."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_one_cache_id_serves_every_zone(self, httpx_mock: HTTPXMock):
        """Check that polling three zones costs a single request.

        The AppCommand.xml body carries no zone, so the second and third
        zone would otherwise post the same bytes and get the same document
        back.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)
        await denon.async_setup()
        after_setup = len(httpx_mock.get_requests())

        cache_id = time.time()
        for zone_receiver in denon.zones.values():
            await zone_receiver.async_update(cache_id=cache_id)

        assert len(appcommand_posts(httpx_mock, after_setup)) == 1
        assert denon.power is not None
        assert denon.zones["Zone2"].power is not None
        assert denon.zones["Zone3"].power is not None

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_without_a_cache_id_every_zone_asks(self, httpx_mock: HTTPXMock):
        """Check that the default is what it has always been, one poll per zone."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)
        await denon.async_setup()
        after_setup = len(httpx_mock.get_requests())

        for zone_receiver in denon.zones.values():
            await zone_receiver.async_update()

        assert len(appcommand_posts(httpx_mock, after_setup)) == 3

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_each_poll_asks_again(self, httpx_mock: HTTPXMock):
        """Check that a later poll is not served the first poll's answer."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP)
        await denon.async_setup()
        after_setup = len(httpx_mock.get_requests())

        await denon.async_update(cache_id=time.time())
        await denon.async_update(cache_id=time.time())

        assert len(appcommand_posts(httpx_mock, after_setup)) == 2

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_status_xml_zones_keep_their_own_documents(
        self, httpx_mock: HTTPXMock
    ):
        """Check that the status XML interface still fetches one set per zone.

        Those documents carry the zone in the URL, so they are genuinely
        different requests and sharing a cache id must not collapse them.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_X))
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)
        await denon.async_setup()
        for zone_receiver in denon.zones.values():
            # pylint: disable=protected-access
            zone_receiver._device.use_avr_2016_update = False
        after_setup = len(httpx_mock.get_requests())

        cache_id = time.time()
        for zone_receiver in denon.zones.values():
            await zone_receiver.async_update(cache_id=cache_id)

        paths = [r.url.path for r in poll_requests(httpx_mock, after_setup)]
        assert STATUS_URL in paths
        assert STATUS_Z2_URL in paths
        assert STATUS_Z3_URL in paths
        assert denon.zones["Zone2"].power is not None
        assert denon.zones["Zone3"].power is not None


class TestRecoveryCacheId:
    """Test case for the retries that re-enter async_update()."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_forbidden_retry_is_not_answered_from_the_cache(
        self, httpx_mock: HTTPXMock
    ):
        """Check that the port-change recovery still reads the receiver.

        The retry runs setup again and must not be handed the cache entry
        that the failed attempt's cache id would otherwise name.
        """
        answer = sample_matcher(RECEIVER_2016)
        forbidden: List[bool] = [True]

        def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
            if request.url.path == APPCOMMAND_URL and forbidden[0]:
                if appcommand_suffix(request) == "-update":
                    forbidden[0] = False
                    return httpx.Response(
                        status_code=403,
                        content="Error 403: Forbidden\nAccess Forbidden",
                    )
            return answer(request, *args, **kwargs)

        httpx_mock.add_callback(matcher)
        denon = denonavr.DenonAVR(FAKE_IP)
        await denon.async_setup()
        after_setup = len(httpx_mock.get_requests())

        await denon.async_update(cache_id=time.time())

        suffixes = [
            appcommand_suffix(request)
            for request in appcommand_posts(httpx_mock, after_setup)
        ]
        assert suffixes.count("-update") == 2
        assert denon.power is not None

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_forbidden_is_raised_when_recovery_is_spent(
        self, httpx_mock: HTTPXMock
    ):
        """Check that a second 403 in a row still reaches the caller."""
        answer = sample_matcher(RECEIVER_2016)

        def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
            if request.url.path == APPCOMMAND_URL:
                if appcommand_suffix(request) == "-update":
                    return httpx.Response(
                        status_code=403,
                        content="Error 403: Forbidden\nAccess Forbidden",
                    )
            return answer(request, *args, **kwargs)

        httpx_mock.add_callback(matcher)
        denon = denonavr.DenonAVR(FAKE_IP)
        await denon.async_setup()

        with pytest.raises(AvrForbiddenError):
            await denon.async_update(cache_id=time.time())
