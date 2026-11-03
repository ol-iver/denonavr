#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the picture mode of DenonAVRDeviceInfo."""

from typing import get_args

import pytest

from denonavr.const import PICTURE_MODE_MAP, PICTURE_MODE_MAP_REVERSE, PictureModes
from denonavr.foundation import AvrCommandError
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def test_picture_mode_maps_are_complete():
    """Test that every picture mode can be converted in both directions."""
    for mode in get_args(PictureModes):
        assert mode in PICTURE_MODE_MAP_REVERSE
        assert PICTURE_MODE_MAP[PICTURE_MODE_MAP_REVERSE[mode]] == mode


@pytest.mark.parametrize("raw, expected", [("OFF", "Off"), ("MOV", "Movie")])
def test_picture_mode_callback(raw, expected):
    """Test that the picture mode is read from telnet events."""
    device = DeviceTestFixture(True).device_info
    assert device.picture_mode is None
    device._picture_mode_callback("Main", "PV", raw)
    assert device.picture_mode == expected


def test_picture_mode_callback_ignores_other_zone():
    """Test that events for other zones are ignored."""
    device = DeviceTestFixture(True).device_info
    device._picture_mode_callback("Zone2", "PV", "MOV")
    assert device.picture_mode is None


@pytest.mark.asyncio
async def test_async_set_picture_mode_sends_telnet_command():
    """Test that the telnet command is sent."""
    fixture = DeviceTestFixture(True)
    await fixture.async_execute(fixture.device_info.async_set_picture_mode("ISF Day"))
    fixture._mock_telnet.assert_called_once_with("PVDAY")


@pytest.mark.asyncio
async def test_async_set_picture_mode_raises_on_invalid():
    """Test that an invalid picture mode is rejected."""
    fixture = DeviceTestFixture(True)
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(
            fixture.device_info.async_set_picture_mode("Invalid")  # type: ignore
        )


@pytest.mark.asyncio
async def test_async_set_picture_mode_returns_early_when_matches():
    """Test that no command is sent when the picture mode is already set."""
    fixture = DeviceTestFixture(True)
    device = fixture.device_info
    device._picture_mode_callback("Main", "PV", "MOV")
    await fixture.async_execute(device.async_set_picture_mode("Movie"))
    fixture.assert_not_called()


@pytest.mark.asyncio
async def test_async_set_picture_mode_sends_command_when_differs():
    """Test that a command is sent when another picture mode is set."""
    fixture = DeviceTestFixture(True)
    device = fixture.device_info
    device._picture_mode_callback("Main", "PV", "MOV")
    await fixture.async_execute(device.async_set_picture_mode("Game"))
    fixture.assert_called_once()
