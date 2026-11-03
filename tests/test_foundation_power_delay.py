#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for power and delay commands of DenonAVRDeviceInfo.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRDeviceInfoPowerDelay:
    """Test cases for power and delay commands."""

    @pytest.mark.asyncio
    async def test_async_power_on_returns_early_when_power_is_on(self):
        """Test that async_power_on returns early when power is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._power_callback("Main", "PW", "ON")
        await fixture.async_execute(device.async_power_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_power_on_sends_command_when_power_is_off(self):
        """Test that async_power_on sends command if power is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._power_callback("Main", "PW", "OFF")
        await fixture.async_execute(device.async_power_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_power_off_returns_early_when_power_is_off(self):
        """Test that async_power_off returns early when power is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._power_callback("Main", "PW", "OFF")
        await fixture.async_execute(device.async_power_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_power_off_sends_command_when_power_is_on(self):
        """Test that async_power_off sends command if power is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._power_callback("Main", "PW", "ON")
        await fixture.async_execute(device.async_power_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_delay_up_returns_early_when_max(self):
        """Test that async_delay_up returns early when delay is at max."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_callback("Main", "PS", "DELAY 500")
        await fixture.async_execute(device.async_delay_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_delay_up_sends_command_when_not_max(self):
        """Test that async_delay_up sends command if delay is not at max."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_callback("Main", "PS", "DELAY 100")
        await fixture.async_execute(device.async_delay_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_delay_down_returns_early_when_min(self):
        """Test that async_delay_down returns early when delay is at min."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_callback("Main", "PS", "DELAY 000")
        await fixture.async_execute(device.async_delay_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_delay_down_sends_command_when_not_min(self):
        """Test that async_delay_down sends command if delay is not at min."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_callback("Main", "PS", "DELAY 100")
        await fixture.async_execute(device.async_delay_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_delay_time_up_returns_early_when_max(self):
        """Test that async_delay_time_up returns early when delay time is at max."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 300")
        await fixture.async_execute(device.async_delay_time_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_delay_time_up_sends_command_when_not_max(self):
        """Test that async_delay_time_up sends command if delay time is not at max."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 100")
        await fixture.async_execute(device.async_delay_time_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_delay_time_down_returns_early_when_min(self):
        """Test that async_delay_time_down returns early when delay time is at min."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 000")
        await fixture.async_execute(device.async_delay_time_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_delay_time_down_sends_command_when_not_min(self):
        """Test that async_delay_time_down sends command if delay time is not at min."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 100")
        await fixture.async_execute(device.async_delay_time_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_delay_time_returns_early_when_matches(self):
        """Test that async_delay_time returns early when delay time matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 100")
        await fixture.async_execute(device.async_delay_time(100))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_delay_time_sends_command_when_differs(self):
        """Test that async_delay_time sends command if delay time differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._delay_time_callback("Main", "PS", "DEL 150")
        await fixture.async_execute(device.async_delay_time(200))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_power_off_returns_early_when_power_is_standby(self):
        """Test that async_power_off returns early when receiver is in standby."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._power_callback("Main", "PW", "STANDBY")
        await fixture.async_execute(device.async_power_off())
        fixture.assert_not_called()
