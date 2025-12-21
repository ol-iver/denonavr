#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for DenonAVRSoundMode (sound mode logic)."""

import pytest

from denonavr.const import (
    AURO_MATIC_3D_PRESET_MAP_LABELS,
    DAC_FILTERS_MAP_LABELS,
    DIALOG_ENHANCER_LEVEL_MAP_LABELS,
    MDAX_MAP_LABELS,
)
from denonavr.soundmode import DenonAVRSoundMode
from tests.test_helpers import DeviceTestFixture


class TestDenonAVRSoundMode:
    """Test cases for DenonAVRSoundMode."""

    @pytest.mark.asyncio
    async def test_async_neural_x_on_returns_early_when_on(self):
        """Test that async_neural_x_on returns early when already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "NEURAL:ON")
        await fixture.async_execute(device.async_neural_x_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_neural_x_on_sends_command_when_off(self):
        """Test that async_neural_x_on sends command when off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "NEURAL:OFF")
        await fixture.async_execute(device.async_neural_x_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_neural_x_off_returns_early_when_off(self):
        """Test that async_neural_x_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "NEURAL:OFF")
        await fixture.async_execute(device.async_neural_x_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_neural_x_off_sends_command_when_on(self):
        """Test that async_neural_x_off sends command when on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "NEURAL:ON")
        await fixture.async_execute(device.async_neural_x_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_auto_returns_early_when_auto(self):
        """Test that async_imax_auto returns early when already auto."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAX AUTO")
        await fixture.async_execute(device.async_imax_auto())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_auto_sends_command_when_not_auto(self):
        """Test that async_imax_auto sends command when not auto."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAX OFF")
        await fixture.async_execute(device.async_imax_auto())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_off_returns_early_when_off(self):
        """Test that async_imax_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAX OFF")
        await fixture.async_execute(device.async_imax_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_off_sends_command_when_not_off(self):
        """Test that async_imax_off sends command when not off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAX AUTO")
        await fixture.async_execute(device.async_imax_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_on_returns_early_when_on(self):
        """Test that async_cinema_eq_on returns early when already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "CINEMA EQ.ON")
        await fixture.async_execute(device.async_cinema_eq_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_on_sends_command_when_off(self):
        """Test that async_cinema_eq_on sends command when off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "CINEMA EQ.OFF")
        await fixture.async_execute(device.async_cinema_eq_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_off_returns_early_when_off(self):
        """Test that async_cinema_eq_off returns early when already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "CINEMA EQ.OFF")
        await fixture.async_execute(device.async_cinema_eq_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_cinema_eq_off_sends_command_when_on(self):
        """Test that async_cinema_eq_off sends command when on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "CINEMA EQ.ON")
        await fixture.async_execute(device.async_cinema_eq_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_audio_settings_returns_early_when_matches(self):
        """Test that async_imax_audio_settings returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXAUD AUTO")
        await fixture.async_execute(device.async_imax_audio_settings("AUTO"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_audio_settings_sends_command_when_differs(self):
        """Test that async_imax_audio_settings sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXAUD MANUAL")
        await fixture.async_execute(device.async_imax_audio_settings("AUTO"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_hpf_returns_early_when_matches(self):
        """Test that async_imax_hpf returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXHPF 080")
        await fixture.async_execute(device.async_imax_hpf(80))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_hpf_sends_command_when_differs(self):
        """Test that async_imax_hpf sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXHPF 060")
        await fixture.async_execute(device.async_imax_hpf(80))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_lpf_returns_early_when_matches(self):
        """Test that async_imax_lpf returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXLPF 120")
        await fixture.async_execute(device.async_imax_lpf(120))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_lpf_sends_command_when_differs(self):
        """Test that async_imax_lpf sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXLPF 080")
        await fixture.async_execute(device.async_imax_lpf(120))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_mode_returns_early_when_matches(self):
        """Test that async_imax_subwoofer_mode returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXSWM ON")
        await fixture.async_execute(device.async_imax_subwoofer_mode("ON"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_mode_sends_command_when_differs(self):
        """Test that async_imax_subwoofer_mode sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXSWM OFF")
        await fixture.async_execute(device.async_imax_subwoofer_mode("ON"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_output_returns_early_when_matches(self):
        """Test that async_imax_subwoofer_output returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXSWO L+M")
        await fixture.async_execute(device.async_imax_subwoofer_output("L+M"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_imax_subwoofer_output_sends_command_when_differs(self):
        """Test that async_imax_subwoofer_output sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._ps_callback("Main", "", "IMAXSWO LFE")
        await fixture.async_execute(device.async_imax_subwoofer_output("L+M"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dialog_enhancer_returns_early_when_matches(self):
        """Test that async_dialog_enhancer returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        # Use a valid dialog enhancer level from the mapping
        level = next(iter(DIALOG_ENHANCER_LEVEL_MAP_LABELS.keys()))
        mapped = DIALOG_ENHANCER_LEVEL_MAP_LABELS[level]
        device._ps_callback("Main", "", f"DEH {level}")
        await fixture.async_execute(device.async_dialog_enhancer(mapped))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dialog_enhancer_sends_command_when_differs(self):
        """Test that async_dialog_enhancer sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        # Use two valid dialog enhancer levels from the mapping
        levels = list(DIALOG_ENHANCER_LEVEL_MAP_LABELS.keys())
        mapped1 = DIALOG_ENHANCER_LEVEL_MAP_LABELS[levels[0]]
        mapped2 = (
            DIALOG_ENHANCER_LEVEL_MAP_LABELS[levels[1]] if len(levels) > 1 else mapped1
        )
        device._ps_callback("Main", "", f"DEH {levels[0]}")
        await fixture.async_execute(device.async_dialog_enhancer(mapped2))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_auromatic_3d_preset_returns_early_when_matches(self):
        """Test that async_auromatic_3d_preset returns early when already matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        # Use a valid preset from the mapping
        preset = next(iter(AURO_MATIC_3D_PRESET_MAP_LABELS.keys()))
        mapped = AURO_MATIC_3D_PRESET_MAP_LABELS[preset]
        device._ps_callback("Main", "", f"AUROPR {preset}")
        await fixture.async_execute(device.async_auromatic_3d_preset(mapped))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_auromatic_3d_preset_sends_command_when_differs(self):
        """Test that async_auromatic_3d_preset sends command when differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRSoundMode(device=fixture.device_info)
        presets = list(AURO_MATIC_3D_PRESET_MAP_LABELS.keys())
        mapped1 = AURO_MATIC_3D_PRESET_MAP_LABELS[presets[0]]
        mapped2 = (
            AURO_MATIC_3D_PRESET_MAP_LABELS[presets[1]] if len(presets) > 1 else mapped1
        )
        device._ps_callback("Main", "", f"AUROPR {presets[0]}")
        await fixture.async_execute(device.async_auromatic_3d_preset(mapped2))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_mdax_returns_early_when_matches(self):
        """Test that async_mdax returns early when already matches."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        device._device.manufacturer = "Marantz"
        mdax = next(iter(MDAX_MAP_LABELS.keys()))
        mapped = MDAX_MAP_LABELS[mdax]
        device._ps_callback("Main", "", f"MDAX {mdax}")
        await fixture.async_execute(device.async_mdax(mapped))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_mdax_sends_command_when_differs(self):
        """Test that async_mdax sends command when differs."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        mdaxs = list(MDAX_MAP_LABELS.keys())
        mapped1 = MDAX_MAP_LABELS[mdaxs[0]]
        mapped2 = MDAX_MAP_LABELS[mdaxs[1]] if len(mdaxs) > 1 else mapped1
        device._ps_callback("Main", "", f"MDAX {mdaxs[0]}")
        await fixture.async_execute(device.async_mdax(mapped2))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dac_filter_returns_early_when_matches(self):
        """Test that async_dac_filter returns early when already matches."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        dac = next(iter(DAC_FILTERS_MAP_LABELS.keys()))
        mapped = DAC_FILTERS_MAP_LABELS[dac]
        device._ps_callback("Main", "", f"DACFIL {dac}")
        await fixture.async_execute(device.async_dac_filter(mapped))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dac_filter_sends_command_when_differs(self):
        """Test that async_dac_filter sends command when differs."""
        fixture = DeviceTestFixture(False)
        device = DenonAVRSoundMode(device=fixture.device_info)
        dacs = list(DAC_FILTERS_MAP_LABELS.keys())
        mapped1 = DAC_FILTERS_MAP_LABELS[dacs[0]]
        mapped2 = DAC_FILTERS_MAP_LABELS[dacs[1]] if len(dacs) > 1 else mapped1
        await fixture.async_execute(device.async_dac_filter(mapped2))
        fixture.assert_called_once()
