#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the requests every zone's setup repeats.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from typing import List

import httpx
import pytest
from pytest_httpx import HTTPXMock

import denonavr

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

# An AVR_X_2016 receiver: its description lives on port 60006.
RECEIVER_2016 = "AVR-X4300H"
# An AVR_X receiver, which also serves the status XML interface.
RECEIVER_X = "AVR-X2000"

FORBIDDEN = httpx.Response(
    status_code=403, content="Error 403: Forbidden\nAccess Forbidden"
)


def get_sample_content(filename):
    """Return sample content form file."""
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return file.read()


def sample_matcher(receiver: str):
    """Return a request callback answering from receiver's sample files."""

    def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
        port_suffix = "-8080" if request.url.port == 8080 else ""
        try:
            if request.url.path == APPCOMMAND_URL:
                content = get_sample_content(
                    f"{receiver}-AppCommand{appcommand_suffix(request)}"
                    f"{port_suffix}.xml"
                )
            elif request.url.path in (DESCRIPTION_URL1, DESCRIPTION_URL2):
                content = get_sample_content("AVR-X1600H_upnp.xml")
            elif request.url.path in SAMPLE_PATHS:
                content = get_sample_content(
                    f"{receiver}-{SAMPLE_PATHS[request.url.path]}{port_suffix}.xml"
                )
            else:
                content = "DATA"
        except FileNotFoundError:
            return FORBIDDEN
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


def setup_requests(httpx_mock: HTTPXMock, path: str) -> List[httpx.Request]:
    """Return the requests made to path."""
    return [r for r in httpx_mock.get_requests() if r.url.path == path]


def probe_suffixes(httpx_mock: HTTPXMock) -> List[str]:
    """Return which probe each AppCommand.xml request carried."""
    return [appcommand_suffix(r) for r in setup_requests(httpx_mock, APPCOMMAND_URL)]


class TestSetupProbes:
    """Test case for one cache id covering a whole setup run."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_the_probes_are_made_once_for_the_receiver(
        self, httpx_mock: HTTPXMock
    ):
        """Check that three zones cost one of each setup request.

        None of them carries a zone: the description names the receiver and
        the AppCommand.xml body has no zone element at all.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)

        await denon.async_setup()

        assert len(setup_requests(httpx_mock, DESCRIPTION_URL2)) == 1
        assert probe_suffixes(httpx_mock) == [
            "-setup",
            "-update-soundmode",
            "-update-tonecontrol",
        ]

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_every_zone_reads_what_the_probes_found(self, httpx_mock: HTTPXMock):
        """Check that sharing the answers is invisible above the transport."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)

        await denon.async_setup()

        # pylint: disable=protected-access
        main_device = denon._device
        assert main_device.friendly_name is not None
        for zone_receiver in denon.zones.values():
            assert zone_receiver._device.friendly_name == main_device.friendly_name
            assert zone_receiver._device.model_name == main_device.model_name
            assert zone_receiver._device.receiver == main_device.receiver
            assert zone_receiver._device.use_avr_2016_update is True
            assert zone_receiver.support_sound_mode is True
            assert zone_receiver.support_tone_control is True

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_a_second_setup_asks_again(self, httpx_mock: HTTPXMock):
        """Check that a repeated setup is not served the first one's answers.

        The port change recovery re-runs setup precisely because the receiver
        moved, so the probes must reach it again.
        """
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP)

        await denon.async_setup()
        await denon.async_setup()

        assert len(setup_requests(httpx_mock, DESCRIPTION_URL2)) == 2
        assert probe_suffixes(httpx_mock).count("-setup") == 2
        assert probe_suffixes(httpx_mock).count("-update-soundmode") == 2
        assert probe_suffixes(httpx_mock).count("-update-tonecontrol") == 2

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_a_caller_can_give_the_setup_its_cache_id(
        self, httpx_mock: HTTPXMock
    ):
        """Check that two setups under one cache id make one set of requests."""
        httpx_mock.add_callback(sample_matcher(RECEIVER_2016))
        denon = denonavr.DenonAVR(FAKE_IP)

        await denon.async_setup(cache_id="one setup")
        await denon.async_setup(cache_id="one setup")

        assert len(setup_requests(httpx_mock, DESCRIPTION_URL2)) == 1
        assert probe_suffixes(httpx_mock).count("-setup") == 1


class TestStatusXmlFallback:
    """Test case for the receivers that refuse AppCommand.xml."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_only_the_shared_documents_collapse(self, httpx_mock: HTTPXMock):
        """Check that the fallback shares the main zone document only.

        When AppCommand.xml is refused the update method is named from
        formMainZone_MainZoneXml.xml, which is one URL for every zone, while
        the per zone status documents carry the zone in the URL and stay one
        request each.
        """
        answer = sample_matcher(RECEIVER_X)

        def matcher(request: httpx.Request, *args, **kwargs) -> httpx.Response:
            if request.url.path == APPCOMMAND_URL:
                return FORBIDDEN
            return answer(request, *args, **kwargs)

        httpx_mock.add_callback(matcher)
        denon = denonavr.DenonAVR(FAKE_IP, add_zones=ZONE2_ZONE3)

        await denon.async_setup()

        assert len(setup_requests(httpx_mock, MAINZONE_URL)) == 1
        assert len(setup_requests(httpx_mock, STATUS_URL)) == 1
        assert len(setup_requests(httpx_mock, STATUS_Z2_URL)) == 1
        assert len(setup_requests(httpx_mock, STATUS_Z3_URL)) == 1
        for zone_receiver in denon.zones.values():
            # pylint: disable=protected-access
            assert zone_receiver._device.use_avr_2016_update is False
            assert zone_receiver._device.friendly_name is not None
