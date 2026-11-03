#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the digital codec of DenonAVRInput."""

from typing import get_args

import pytest

from denonavr.const import (
    DIGITAL_CODEC_MAP,
    DIGITAL_CODEC_MAP_REVERSE,
    DigitalCodecModes,
)
from denonavr.exceptions import AvrCommandError
from denonavr.input import DenonAVRInput
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def test_digital_codec_maps_are_complete():
    """Test that every digital codec mode can be converted in both directions."""
    for mode in get_args(DigitalCodecModes):
        assert mode in DIGITAL_CODEC_MAP_REVERSE
        assert DIGITAL_CODEC_MAP[DIGITAL_CODEC_MAP_REVERSE[mode]] == mode


@pytest.mark.parametrize("raw, expected", [("AUTO", "Auto"), ("DTS", "DTS")])
def test_digital_codec_callback(raw, expected):
    """Test that the digital codec is read from telnet events."""
    device = DenonAVRInput(device=DeviceTestFixture(True).device_info)
    assert device.digital_codec is None
    device._digital_codec_callback("Main", "DC", raw)
    assert device.digital_codec == expected


def test_digital_codec_callback_ignores_other_zone():
    """Test that events for other zones are ignored."""
    device = DenonAVRInput(device=DeviceTestFixture(True).device_info)
    device._digital_codec_callback("Zone2", "DC", "PCM")
    assert device.digital_codec is None


@pytest.mark.asyncio
async def test_async_set_digital_codec_sends_telnet_command():
    """Test that the telnet command is sent."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRInput(device=fixture.device_info)
    await fixture.async_execute(device.async_set_digital_codec("PCM"))
    fixture._mock_telnet.assert_called_once_with("DCPCM")


@pytest.mark.asyncio
async def test_async_set_digital_codec_raises_on_invalid():
    """Test that an invalid digital codec mode is rejected."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRInput(device=fixture.device_info)
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(
            device.async_set_digital_codec("Invalid")  # type: ignore
        )


@pytest.mark.asyncio
async def test_async_set_digital_codec_returns_early_when_matches():
    """Test that no command is sent when the digital codec is already set."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRInput(device=fixture.device_info)
    device._digital_codec_callback("Main", "DC", "DTS")
    await fixture.async_execute(device.async_set_digital_codec("DTS"))
    fixture.assert_not_called()


@pytest.mark.asyncio
async def test_async_set_digital_codec_sends_command_when_differs():
    """Test that a command is sent when another digital codec is set."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRInput(device=fixture.device_info)
    device._digital_codec_callback("Main", "DC", "DTS")
    await fixture.async_execute(device.async_set_digital_codec("PCM"))
    fixture.assert_called_once()
