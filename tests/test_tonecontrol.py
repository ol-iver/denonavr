#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the tone control reads and setters.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from typing import Optional
from unittest import mock

import attr
import pytest
from pytest_httpx import HTTPXMock

from denonavr.appcommand import AppCommands
from denonavr.const import MAIN_ZONE
from denonavr.exceptions import AvrCommandError
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


class TestDormantResponseDoesNotOverwrite:
    """Test case for a blank element meeting a value telnet already pushed."""

    @pytest.mark.asyncio
    async def test_the_telnet_values_survive_the_poll(self, httpx_mock: HTTPXMock):
        """Check that a dormant block keeps what telnet reported."""
        # The poll runs every 10 s. Overwriting here blanks a value the user
        # has just changed, within seconds of the change reaching the library
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "BAS 53")
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "TRE 46")

        await tone_control.async_update_tone_control()

        assert tone_control.bass == 9
        assert tone_control.bass_level == "+3dB"
        assert tone_control.treble == 2
        assert tone_control.treble_level == "-4dB"

    @pytest.mark.asyncio
    async def test_a_populated_response_still_wins(self, httpx_mock: HTTPXMock):
        """Check that the rule is blank does not overwrite, not telnet wins."""
        httpx_mock.add_response(content=get_sample_content(ENGAGED))
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "BAS 53")

        await tone_control.async_update_tone_control()

        assert tone_control.bass == 10
        assert tone_control.bass_level == "+4dB"

    @pytest.mark.asyncio
    async def test_a_command_that_does_not_opt_in_still_clears(
        self, httpx_mock: HTTPXMock
    ):
        """Check that a blank element is unknown for every other command."""
        # Commands whose blank elements carry an explicit readability marker
        # must go on reporting unknown rather than a stale value
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "BAS 53")

        await tone_control.async_update_attrs_appcommand(
            {attr.evolve(AppCommands.GetToneControl, blank_is_unknown=True): None}
        )

        assert tone_control.bass is None
        assert tone_control.bass_level is None


class TestSetterAfterADormantResponse:
    """Test case for the setters reading an attribute the poll kept."""

    @pytest.mark.asyncio
    async def test_the_enable_is_still_sent_when_adjust_was_seen_off(
        self, httpx_mock: HTTPXMock
    ):
        """Check that a kept adjust of False still triggers the enable."""
        # async_set_bass relies on tone_control_adjust being falsy to send the
        # enable. Keeping the last value instead of blanking it must not cost
        # the enable when that last value was off
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._sound_detail_callback(MAIN_ZONE, "PS", "TONE CTRL OFF")
        await tone_control.async_update_tone_control()

        assert tone_control.tone_control_adjust is False

        with mock.patch.object(
            type(tone_control._device),
            "telnet_available",
            mock.PropertyMock(return_value=True),
        ), mock.patch.object(
            tone_control._device.telnet_api, "async_send_commands", mock.AsyncMock()
        ) as send:
            await tone_control.async_set_bass(9)

        assert [call.args[0] for call in send.await_args_list] == [
            "PSTONE CTRL ON",
            "PSBAS 53",
        ]

    @pytest.mark.asyncio
    async def test_the_enable_is_skipped_when_adjust_was_seen_on(
        self, httpx_mock: HTTPXMock
    ):
        """Check that a kept adjust of True spares the redundant enable."""
        httpx_mock.add_response(content=get_sample_content(ENGAGED))
        httpx_mock.add_response(content=get_sample_content(DORMANT))
        tone_control = tone_control_instance()
        await tone_control.async_update_tone_control()
        await tone_control.async_update_tone_control()

        assert tone_control.tone_control_adjust is True

        # pylint: disable=protected-access
        with mock.patch.object(
            type(tone_control._device),
            "telnet_available",
            mock.PropertyMock(return_value=True),
        ), mock.patch.object(
            tone_control._device.telnet_api, "async_send_commands", mock.AsyncMock()
        ) as send:
            await tone_control.async_set_bass(9)

        send.assert_awaited_once_with("PSBAS 53")


class TestToneControlGuard:
    """Test case for the guard on enabling and disabling tone control."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method",
        [
            pytest.param("async_enable_tone_control", id="enable"),
            pytest.param("async_disable_tone_control", id="disable"),
        ],
    )
    async def test_an_unsupported_receiver_raises(self, method: str):
        """Check that the command is refused on a model without the block."""
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._support_tone_control = False

        with pytest.raises(AvrCommandError) as excinfo:
            await getattr(tone_control, method)()

        assert "Dynamic EQ" not in str(excinfo.value)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method,expected",
        [
            pytest.param("async_enable_tone_control", "PSTONE CTRL ON", id="enable"),
            pytest.param("async_disable_tone_control", "PSTONE CTRL OFF", id="disable"),
        ],
    )
    @pytest.mark.parametrize(
        "support",
        [
            pytest.param(True, id="supported"),
            pytest.param(None, id="not-yet-known"),
        ],
    )
    async def test_the_command_is_sent_otherwise(
        self, method: str, expected: str, support: Optional[bool]
    ):
        """Check that nothing but a lack of support stops the command."""
        # The guard tests support, not tone_control_status, which the receiver
        # answers as a bool from the first update on and so never fires
        tone_control = tone_control_instance()
        # pylint: disable=protected-access
        tone_control._support_tone_control = support
        tone_control._tone_control_status = None

        with mock.patch.object(
            type(tone_control._device),
            "telnet_available",
            mock.PropertyMock(return_value=True),
        ), mock.patch.object(
            tone_control._device.telnet_api, "async_send_commands", mock.AsyncMock()
        ) as send:
            await getattr(tone_control, method)()

        send.assert_awaited_once_with(expected)


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
