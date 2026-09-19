#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the tone control reads and setters.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest
from pytest_httpx import HTTPXMock

from denonavr.const import MAIN_ZONE
from denonavr.tonecontrol import DenonAVRToneControl

# Both fixtures reproduce a state the AVR-X1700H was measured in. The dormant
# one is not a cold start: it appeared on a unit that had been answering with
# full values and survived a power cycle, a Dynamic EQ toggle and a telnet
# write that demonstrably applied
ENGAGED = "AVR-X1700H-AppCommand-tonecontrol-engaged.xml"
DORMANT = "AVR-X1700H-AppCommand-tonecontrol-dormant.xml"


def get_sample_content(filename: str) -> str:
    """Return sample content form file."""
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return file.read()


def tone_control_instance() -> DenonAVRToneControl:
    """Return a tone control instance that is ready to be updated."""
    tone_control = DenonAVRToneControl()
    # pylint: disable=protected-access
    tone_control._device.use_avr_2016_update = True
    return tone_control


class TestToneControlUpdate:
    """Test case for reading the tone control block from AppCommand.xml."""

    @pytest.mark.asyncio
    async def test_the_values_are_read(self, httpx_mock: HTTPXMock):
        """Check that a populated response lands on every attribute."""
        httpx_mock.add_response(content=get_sample_content(ENGAGED))
        tone_control = tone_control_instance()
        await tone_control.async_update_tone_control()

        assert tone_control.tone_control_status is True
        assert tone_control.tone_control_adjust is True
        assert tone_control.bass == 10
        assert tone_control.bass_level == "+4dB"
        assert tone_control.treble == 2
        assert tone_control.treble_level == "-4dB"

    @pytest.mark.asyncio
    async def test_a_dormant_response_leaves_the_values_unknown(
        self, httpx_mock: HTTPXMock
    ):
        """Check that blank elements read as unknown when nothing is known."""
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        await tone_control.async_update_tone_control()

        assert tone_control.bass is None
        assert tone_control.bass_level is None
        assert tone_control.treble is None
        assert tone_control.treble_level is None

    @pytest.mark.asyncio
    async def test_the_status_element_is_never_blank(self, httpx_mock: HTTPXMock):
        """Check that a dormant block still reports its status as a bool."""
        # status is the one element the receiver fills in this state, which is
        # why a None check on it is not a test for anything a caller can reach
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        await tone_control.async_update_tone_control()

        assert tone_control.tone_control_status is False


class TestLevelFormat:
    """Test case for the level string the two transports produce."""

    @pytest.mark.parametrize(
        "parameter,expected",
        [
            pytest.param("BAS 54", "+4dB", id="bass-above"),
            pytest.param("BAS 50", "0dB", id="bass-flat"),
            pytest.param("BAS 46", "-4dB", id="bass-below"),
            pytest.param("TRE 54", "+4dB", id="treble-above"),
            pytest.param("TRE 50", "0dB", id="treble-flat"),
            pytest.param("TRE 46", "-4dB", id="treble-below"),
        ],
    )
    def test_the_telnet_level_carries_its_sign(self, parameter: str, expected: str):
        """Check that a positive level is prefixed the way HTTP prefixes it."""
        tone_control = DenonAVRToneControl()
        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", parameter)

        level = (
            tone_control.bass_level
            if parameter.startswith("BAS")
            else tone_control.treble_level
        )
        assert level == expected

    @pytest.mark.asyncio
    async def test_both_transports_agree_on_one_reading(self, httpx_mock: HTTPXMock):
        """Check that the same setting reads the same on either transport."""
        # Measured together: GetToneControl answered basslevel +4dB while
        # telnet answered PSBAS 54, and the library rendered the second as 4dB
        httpx_mock.add_response(content=get_sample_content(ENGAGED))
        tone_control = tone_control_instance()
        await tone_control.async_update_tone_control()
        from_http = tone_control.bass_level

        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "BAS 54")

        assert tone_control.bass_level == from_http
