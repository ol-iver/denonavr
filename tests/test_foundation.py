#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of foundation.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.foundation import AvrCommandError
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRDeviceInfo:
    """Test cases for DenonAVRDeviceInfo."""

    @pytest.mark.asyncio
    async def test_async_sleep_returns_early_when_sleep_matches(self):
        """Test that async_sleep returns early when sleep time matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._auto_sleep_callback("Main", "SLP", "030")
        await fixture.async_execute(device.async_sleep(30))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_sleep_sends_command_when_sleep_differs(self):
        """Test that async_sleep sends command if sleep time differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._auto_sleep_callback("Main", "SLP", "010")
        await fixture.async_execute(device.async_sleep(30))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_sleep_returns_early_when_off(self):
        """Test that async_sleep returns early when sleep is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._auto_sleep_callback("Main", "SLP", "OFF")
        await fixture.async_execute(device.async_sleep("OFF"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_sleep_sends_command_when_not_off(self):
        """Test that async_sleep sends command if sleep is not off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._auto_sleep_callback("Main", "SLP", "030")
        await fixture.async_execute(device.async_sleep("OFF"))
        fixture.assert_called_once()

    def test_sleep_is_int_or_off(self):
        """Test that the sleep timer is an integer, or OFF."""
        device = DeviceTestFixture(True).device_info
        device._auto_sleep_callback("Main", "SLP", "030")
        assert device.sleep == 30
        device._auto_sleep_callback("Main", "SLP", "OFF")
        assert device.sleep == "OFF"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sleep", [-1, 0, 121, "ON"])
    async def test_async_sleep_raises_on_invalid(self, sleep):
        """Test that async_sleep raises on invalid values."""
        fixture = DeviceTestFixture(True)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(fixture.device_info.async_sleep(sleep))
