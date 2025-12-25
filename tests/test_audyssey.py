#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of audyssey.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.audyssey import AvrCommandError, DenonAVRAudyssey
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRAudyssey:
    """Test cases for DenonAVRAudyssey."""

    @pytest.mark.asyncio
    async def test_async_dynamiceq_on_returns_early_when_on(self):
        """Test that no command is sent when DynamicEQ is already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ ON")
        await fixture.async_execute(device.async_dynamiceq_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dynamiceq_on_sends_command_when_off(self):
        """Test that command is sent when DynamicEQ is off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ OFF")
        await fixture.async_execute(device.async_dynamiceq_on())
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_dynamiceq_off_returns_early_when_off(self):
        """Test that no command is sent when DynamicEQ is already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ OFF")
        await fixture.async_execute(device.async_dynamiceq_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dynamiceq_off_sends_command_when_on(self):
        """Test that command is sent when DynamicEQ is on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ ON")
        await fixture.async_execute(device.async_dynamiceq_off())
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_set_reflevoffset_raises_if_dynamiceq_off(self):
        """Test that setting reflev offset raises error if DynamicEQ is off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ OFF")
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_set_reflevoffset("0dB"))

    @pytest.mark.asyncio
    async def test_async_set_reflevoffset_returns_early_when_matches(self):
        """Test that no command is sent when reflev offset matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ ON")
        device._ps_callback("Main", "", "REFLEV 0")
        await fixture.async_execute(device.async_set_reflevoffset("0dB"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_reflevoffset_sends_command_when_differs(self):
        """Test that command is sent when reflev offset differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNEQ ON")
        device._ps_callback("Main", "", "REFLEV 0")
        await fixture.async_execute(device.async_set_reflevoffset("+5dB"))
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_lfc_on_returns_early_when_on(self):
        """Test that no command is sent when LFC is already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "LFC ON")
        await fixture.async_execute(device.async_lfc_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_lfc_on_sends_command_when_off(self):
        """Test that command is sent when LFC is off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "LFC OFF")
        await fixture.async_execute(device.async_lfc_on())
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_lfc_off_returns_early_when_off(self):
        """Test that no command is sent when LFC is already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "LFC OFF")
        await fixture.async_execute(device.async_lfc_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_lfc_off_sends_command_when_on(self):
        """Test that command is sent when LFC is on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "LFC ON")
        await fixture.async_execute(device.async_lfc_off())
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_returns_early_when_matches(self):
        """Test that no command is sent when containment amount matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 3")
        await fixture.async_execute(device.async_containment_amount(3))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_sends_command_when_differs(self):
        """Test that command is sent when containment amount differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 2")
        await fixture.async_execute(device.async_containment_amount(3))
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_raises_on_invalid(self):
        """Test that setting invalid containment amount raises error."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_containment_amount(0))
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_containment_amount(8))

    @pytest.mark.asyncio
    async def test_async_set_multieq_returns_early_when_matches(self):
        """Test that no command is sent when MultiEQ setting matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "MULTEQ:OFF")
        await fixture.async_execute(device.async_set_multieq("Off"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_multieq_sends_command_when_differs(self):
        """Test that command is sent when MultiEQ setting differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "MULTEQ:OFF")
        await fixture.async_execute(device.async_set_multieq("Flat"))
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_set_multieq_raises_on_invalid(self):
        """Test that setting invalid MultiEQ raises error."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_set_multieq("notavalidmode"))

    @pytest.mark.asyncio
    async def test_async_set_dynamicvol_returns_early_when_matches(self):
        """Test that no command is sent when Dynamic Volume setting matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNVOL OFF")
        await fixture.async_execute(device.async_set_dynamicvol("Off"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_dynamicvol_sends_command_when_differs(self):
        """Test that command is sent when Dynamic Volume setting differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "DYNVOL OFF")
        await fixture.async_execute(device.async_set_dynamicvol("Light"))
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_set_dynamicvol_raises_on_invalid(self):
        """Test that setting invalid Dynamic Volume raises error."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_set_dynamicvol("notavalidmode"))

    @pytest.mark.asyncio
    async def test_async_containment_amount_up_returns_early_when_max(self):
        """Test that no command is sent when containment amount is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 7")
        await fixture.async_execute(device.async_containment_amount_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_up_sends_command_when_not_max(self):
        """Test that command is sent when containment amount is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 5")
        await fixture.async_execute(device.async_containment_amount_up())
        fixture.assert_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_down_returns_early_when_min(self):
        """Test that no command is sent when containment amount is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 1")
        await fixture.async_execute(device.async_containment_amount_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_containment_amount_down_sends_command_when_not_min(self):
        """Test that command is sent when containment amount is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRAudyssey(device=fixture.device_info)
        device._ps_callback("Main", "", "CNTAMT 3")
        await fixture.async_execute(device.async_containment_amount_down())
        fixture.assert_called()
