#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for DenonAVRToneControl (tone control logic).

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.tonecontrol import DenonAVRToneControl
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRToneControl:
    """Test cases for DenonAVRToneControl."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("value", [0, 6, 12])
    async def test_async_set_bass_returns_early_when_matches(self, value):
        """Test that async_set_bass returns early if value matches current bass."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", f"BAS {value+44}")
        await fixture.async_execute(device.async_set_bass(value))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(0, 1), (6, 12)])
    async def test_async_set_bass_sends_command_when_differs(self, from_val, to_val):
        """Test that async_set_bass sends command if value differs from current bass."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", f"BAS {from_val+44}")
        device._tone_control_adjust = True
        await fixture.async_execute(device.async_set_bass(to_val))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bass_up_returns_early_when_max(self):
        """Test that async_bass_up returns early if bass is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "BAS 56")
        await fixture.async_execute(device.async_bass_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bass_up_sends_command_when_not_max(self):
        """Test that async_bass_up sends command if bass is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "BAS 50")
        await fixture.async_execute(device.async_bass_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bass_down_returns_early_when_min(self):
        """Test that async_bass_down returns early if bass is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "BAS 44")
        await fixture.async_execute(device.async_bass_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bass_down_sends_command_when_not_min(self):
        """Test that async_bass_down sends command if bass is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "BAS 50")
        await fixture.async_execute(device.async_bass_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("value", [0, 6, 12])
    async def test_async_set_treble_returns_early_when_matches(self, value):
        """Test that async_set_treble returns early if value matches current treble."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", f"TRE {value+44}")
        await fixture.async_execute(device.async_set_treble(value))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(0, 1), (6, 12)])
    async def test_async_set_treble_sends_command_when_differs(self, from_val, to_val):
        """Test that async_set_treble sends command if value differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", f"TRE {from_val+44}")
        await fixture.async_execute(device.async_set_treble(to_val))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_treble_up_returns_early_when_max(self):
        """Test that async_treble_up returns early if treble is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "TRE 56")
        await fixture.async_execute(device.async_treble_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_treble_up_sends_command_when_not_max(self):
        """Test that async_treble_up sends command if treble is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "TRE 50")
        await fixture.async_execute(device.async_treble_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_treble_down_returns_early_when_min(self):
        """Test that async_treble_down returns early if treble is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "TRE 44")
        await fixture.async_execute(device.async_treble_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_treble_down_sends_command_when_not_min(self):
        """Test that async_treble_down sends command if treble is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRToneControl(device=fixture.device_info)
        device._ps_callback("Main", "", "TONE CTRL ON")
        device._ps_callback("Main", "", "TRE 50")
        await fixture.async_execute(device.async_treble_down())
        fixture.assert_called_once()
