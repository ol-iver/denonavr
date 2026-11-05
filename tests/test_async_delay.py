#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the async_delay command of DenonAVRDeviceInfo."""

import pytest

from denonavr.foundation import AvrCommandError
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.mark.asyncio
async def test_async_delay_returns_early_when_matches():
    """Test that no command is sent when the delay is already set."""
    fixture = DeviceTestFixture(True)
    device = fixture.device_info
    device._delay_callback("Main", "PS", "DELAY 100")
    await fixture.async_execute(device.async_delay(100))
    fixture.assert_not_called()


@pytest.mark.asyncio
async def test_async_delay_sends_command_when_differs():
    """Test that a command is sent when another delay is set."""
    fixture = DeviceTestFixture(True)
    device = fixture.device_info
    device._delay_callback("Main", "PS", "DELAY 100")
    await fixture.async_execute(device.async_delay(200))
    fixture._mock_telnet.assert_called_once_with("PSDELAY 200")


@pytest.mark.asyncio
async def test_async_delay_sends_command_when_delay_is_unknown():
    """Test that a command is sent when the current delay is not known."""
    fixture = DeviceTestFixture(True)
    await fixture.async_execute(fixture.device_info.async_delay(0))
    fixture._mock_telnet.assert_called_once_with("PSDELAY 000")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "delay, expected",
    [(0, "PSDELAY 000"), (5, "PSDELAY 005"), (50, "PSDELAY 050"), (500, "PSDELAY 500")],
)
async def test_async_delay_pads_value_to_three_digits(delay, expected):
    """Test that the receiver gets the delay with three digits."""
    fixture = DeviceTestFixture(True)
    await fixture.async_execute(fixture.device_info.async_delay(delay))
    fixture._mock_telnet.assert_called_once_with(expected)


def test_http_command_pads_value_to_three_digits():
    """Test that the HTTP command also uses three digits."""
    url = DeviceTestFixture(True).device_info.urls.command_delay
    assert url.format(delay=5).endswith("PSDELAY%20005")


@pytest.mark.asyncio
@pytest.mark.parametrize("delay", [-1, 501])
async def test_async_delay_raises_on_invalid(delay):
    """Test that a delay outside 0-500 is rejected."""
    fixture = DeviceTestFixture(True)
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(fixture.device_info.async_delay(delay))
