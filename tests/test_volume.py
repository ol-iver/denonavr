#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the volume functions of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from unittest import mock

import pytest

from denonavr.const import (
    DENONAVR_TELNET_COMMANDS,
    MAIN_ZONE,
    ZONE2,
    ZONE2_TELNET_COMMANDS,
    ZONE3,
    ZONE3_TELNET_COMMANDS,
)
from denonavr.volume import DenonAVRVolume, encode_telnet_volume


class TestEncodeTelnetVolume:
    """
    Test case for the telnet volume encoding.

    Telnet takes the absolute value -- relative plus 80 -- as two digits for a
    whole number and three for a half step, the last being tenths. The same
    encoding the receiver uses when it reports a volume back.
    """

    @pytest.mark.parametrize(
        "volume,expected",
        [
            (-80.0, "00"),
            (-48.0, "32"),
            (-24.0, "56"),
            (0.0, "80"),
            (18.0, "98"),
            # half steps keep the tenths digit instead of being truncated
            (-47.5, "325"),
            (-23.5, "565"),
            (-79.5, "005"),
            (-0.5, "795"),
            (17.5, "975"),
        ],
    )
    def test_whole_and_half_steps(self, volume, expected):
        """Check both widths of the telnet encoding."""
        assert encode_telnet_volume(volume) == expected

    @pytest.mark.parametrize(
        "volume,expected",
        [(-47.5, "32"), (-40.5, "39"), (-48.0, "32"), (0.0, "80")],
    )
    def test_half_step_disabled_keeps_two_digits(self, volume, expected):
        """Check the encoding for a zone that does not take half steps."""
        assert encode_telnet_volume(volume, half_step=False) == expected

    @pytest.mark.parametrize("volume", [-80.0, -47.5, -24.0, 0.0, 17.5, 18.0])
    def test_round_trips_through_the_reported_format(self, volume):
        """Check that what is sent decodes back to what was asked for."""
        avr_volume = DenonAVRVolume()
        # pylint: disable=protected-access
        avr_volume._volume_callback(MAIN_ZONE, "MV", encode_telnet_volume(volume))
        assert avr_volume.volume == volume


class TestSetVolumeOverTelnet:
    """Test case for the command async_set_volume puts on the wire."""

    @staticmethod
    def _volume(telnet_commands):
        volume = DenonAVRVolume()
        # pylint: disable=protected-access
        volume._device.telnet_commands = telnet_commands
        volume._device.telnet_api.async_send_commands = mock.AsyncMock()
        volume._device.api.async_get_command = mock.AsyncMock()
        return volume

    @staticmethod
    def _telnet_available(volume):
        """Pretend a telnet connection is up, so the telnet branch is taken."""
        # pylint: disable=protected-access
        return mock.patch.object(
            type(volume._device), "telnet_available", property(lambda self: True)
        )

    @staticmethod
    def _sent(volume):
        # pylint: disable=protected-access
        return volume._device.telnet_api.async_send_commands.await_args[0][0]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "requested,expected",
        [(-48.0, "MV32"), (-47.5, "MV325"), (-24.0, "MV56"), (18.0, "MV98")],
    )
    async def test_main_zone(self, requested, expected):
        """Check that a half step reaches the wire on the main zone."""
        volume = self._volume(DENONAVR_TELNET_COMMANDS)
        with self._telnet_available(volume):
            await volume.async_set_volume(requested)
        assert self._sent(volume) == expected

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "zone,telnet_commands,prefix",
        [
            (ZONE2, ZONE2_TELNET_COMMANDS, "Z2"),
            (ZONE3, ZONE3_TELNET_COMMANDS, "Z3"),
        ],
    )
    async def test_other_zones_stay_on_two_digits(self, zone, telnet_commands, prefix):
        """
        Check that the zones which cannot do half steps are left alone.

        Zone 2 ignores a three digit volume outright -- verified on an
        AVR-X1700H, where Z2395 left the volume where it was -- so sending one
        would turn an approximate result into no result at all, and leave the
        telnet confirmation waiting for an event that never arrives.
        """
        volume = self._volume(telnet_commands)
        # pylint: disable=protected-access
        volume._device.zone = zone
        with self._telnet_available(volume):
            await volume.async_set_volume(-40.5)
        assert self._sent(volume) == f"{prefix}39"

    @pytest.mark.asyncio
    async def test_other_zones_are_unchanged_from_before(self):
        """Check that zone 2 still gets a whole decibel, byte for byte."""
        volume = self._volume(ZONE2_TELNET_COMMANDS)
        # pylint: disable=protected-access
        volume._device.zone = ZONE2
        for requested in (-40.5, -40.0, -80.0, 18.0, -0.5):
            volume._device.telnet_api.async_send_commands.reset_mock()
            with self._telnet_available(volume):
                await volume.async_set_volume(requested)
            previous = "Z2" + format(int(round(requested * 2) / 2.0 + 80), "02d")
            assert self._sent(volume) == previous

    @pytest.mark.asyncio
    async def test_http_still_sends_one_decimal(self):
        """Check that the HTTP path, which was already correct, is unchanged."""
        volume = self._volume(DENONAVR_TELNET_COMMANDS)
        await volume.async_set_volume(-47.5)
        # pylint: disable=protected-access
        url = volume._device.api.async_get_command.await_args[0][0]
        assert url.endswith("1+-47.5")
