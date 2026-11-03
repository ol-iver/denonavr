#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for DenonAVRSoundMode (sound mode logic)."""

import pytest

from denonavr.soundmode import DenonAVRSoundMode
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRSoundMode:
    """Test cases for DenonAVRSoundMode."""

    @pytest.mark.asyncio
    async def test_async_neural_x_on_returns_early_when_on(self):
        """Test that async_neural_x_on returns early when already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._neural_x_callback("Main", "PS", "NEURAL:ON")
        await fixture.async_execute(device.async_neural_x_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_neural_x_on_sends_command_when_off(self):
        """Test that async_neural_x_on sends command when off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._neural_x_callback("Main", "PS", "NEURAL:OFF")
        await fixture.async_execute(device.async_neural_x_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_neural_x_off_returns_early_when_off(self):
        """Test that async_neural_x_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._neural_x_callback("Main", "PS", "NEURAL:OFF")
        await fixture.async_execute(device.async_neural_x_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_neural_x_off_sends_command_when_on(self):
        """Test that async_neural_x_off sends command when on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._neural_x_callback("Main", "PS", "NEURAL:ON")
        await fixture.async_execute(device.async_neural_x_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_auto_returns_early_when_auto(self):
        """Test that async_imax_auto returns early when already auto."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAX AUTO")
        await fixture.async_execute(device.async_imax_auto())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_auto_sends_command_when_not_auto(self):
        """Test that async_imax_auto sends command when not auto."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAX OFF")
        await fixture.async_execute(device.async_imax_auto())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_off_returns_early_when_off(self):
        """Test that async_imax_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAX OFF")
        await fixture.async_execute(device.async_imax_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_off_sends_command_when_not_off(self):
        """Test that async_imax_off sends command when not off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAX AUTO")
        await fixture.async_execute(device.async_imax_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_on_returns_early_when_on(self):
        """Test that async_cinema_eq_on returns early when already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._cinema_eq_callback("Main", "PS", "CINEMA EQ.ON")
        await fixture.async_execute(device.async_cinema_eq_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_on_sends_command_when_off(self):
        """Test that async_cinema_eq_on sends command when off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._cinema_eq_callback("Main", "PS", "CINEMA EQ.OFF")
        await fixture.async_execute(device.async_cinema_eq_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_off_returns_early_when_off(self):
        """Test that async_cinema_eq_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._cinema_eq_callback("Main", "PS", "CINEMA EQ.OFF")
        await fixture.async_execute(device.async_cinema_eq_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_off_sends_command_when_on(self):
        """Test that async_cinema_eq_off sends command when on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._cinema_eq_callback("Main", "PS", "CINEMA EQ.ON")
        await fixture.async_execute(device.async_cinema_eq_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_audio_settings_returns_early_when_matches(self):
        """Test that async_imax_audio_settings returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXAUD AUTO")
        await fixture.async_execute(device.async_imax_audio_settings("AUTO"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_audio_settings_sends_command_when_differs(self):
        """Test that async_imax_audio_settings sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXAUD MANUAL")
        await fixture.async_execute(device.async_imax_audio_settings("AUTO"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_mode_returns_early_when_matches(self):
        """Test that async_imax_subwoofer_mode returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXSWM ON")
        await fixture.async_execute(device.async_imax_subwoofer_mode("ON"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_mode_sends_command_when_differs(self):
        """Test that async_imax_subwoofer_mode sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXSWM OFF")
        await fixture.async_execute(device.async_imax_subwoofer_mode("ON"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_output_returns_early_when_matches(self):
        """Test that async_imax_subwoofer_output returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXSWO L+M")
        await fixture.async_execute(device.async_imax_subwoofer_output("L+M"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_output_sends_command_when_differs(self):
        """Test that async_imax_subwoofer_output sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._imax_callback("Main", "PS", "IMAXSWO LFE")
        await fixture.async_execute(device.async_imax_subwoofer_output("L+M"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dialog_enhancer_returns_early_when_matches(self):
        """Test that async_dialog_enhancer returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._dialog_enhancer_callback("Main", "PS", "DEH OFF")
        await fixture.async_execute(device.async_dialog_enhancer("Off"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dialog_enhancer_sends_command_when_differs(self):
        """Test that async_dialog_enhancer sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._dialog_enhancer_callback("Main", "PS", "DEH OFF")
        await fixture.async_execute(device.async_dialog_enhancer("High"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_auromatic_3d_preset_returns_early_when_matches(self):
        """Test that async_auromatic_3d_preset returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._auro_callback("Main", "PS", "AUROPR SMA")
        await fixture.async_execute(device.async_auromatic_3d_preset("Small"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_auromatic_3d_preset_sends_command_when_differs(self):
        """Test that async_auromatic_3d_preset sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._auro_callback("Main", "PS", "AUROPR SMA")
        await fixture.async_execute(device.async_auromatic_3d_preset("Large"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_mdax_returns_early_when_matches(self):
        """Test that async_mdax returns early when already matches."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._device.manufacturer = "Marantz"
        device._mdax_callback("Main", "PS", "MDAX OFF")
        await fixture.async_execute(device.async_mdax("Off"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_mdax_sends_command_when_differs(self):
        """Test that async_mdax sends command when differs."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._mdax_callback("Main", "PS", "MDAX OFF")
        await fixture.async_execute(device.async_mdax("High"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dac_filter_returns_early_when_matches(self):
        """Test that async_dac_filter returns early when already matches."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._dac_filter_callback("Main", "PS", "DACFIL MODE1")
        await fixture.async_execute(device.async_dac_filter("Mode 1"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dac_filter_sends_command_when_differs(self):
        """Test that async_dac_filter sends command when differs."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._dac_filter_callback("Main", "PS", "DACFIL MODE1")
        await fixture.async_execute(device.async_dac_filter("Mode 2"))
        fixture.assert_called_once()
