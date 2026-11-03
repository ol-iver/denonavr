#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for device setting commands of DenonAVRDeviceInfo.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.foundation import AvrCommandError
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRDeviceInfoSettings:
    """Test cases for device setting commands."""

    @pytest.mark.asyncio
    async def test_async_room_size_returns_early_when_matches(self):
        """Test that async_room_size returns early when room size matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._room_size_callback("Main", "PS", "RSZ S")
        await fixture.async_execute(device.async_room_size("S"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_room_size_sends_command_when_differs(self):
        """Test that async_room_size sends command if room size differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._room_size_callback("Main", "PS", "RSZ S")
        await fixture.async_execute(device.async_room_size("M"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_room_size_raises_on_invalid(self):
        """Test that async_room_size raises on invalid room size."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._room_size_callback("Main", "PS", "RSZ S")
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_room_size("INVALID"))

    @pytest.mark.asyncio
    async def test_async_tactile_transducer_on_returns_early_when_on(self):
        """Test that async_tactile_transducer_on returns early when TTR is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._tactile_transducer_callback("Main", "SS", "TTR ON")
        await fixture.async_execute(device.async_tactile_transducer_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_tactile_transducer_on_sends_command_when_off(self):
        """Test that async_tactile_transducer_on sends command if TTR is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._tactile_transducer_callback("Main", "SS", "TTR OFF")
        await fixture.async_execute(device.async_tactile_transducer_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_tactile_transducer_off_returns_early_when_off(self):
        """Test that async_tactile_transducer_off returns early when TTR is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._tactile_transducer_callback("Main", "SS", "TTR OFF")
        await fixture.async_execute(device.async_tactile_transducer_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_tactile_transducer_off_sends_command_when_on(self):
        """Test that async_tactile_transducer_off sends command if TTR is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._tactile_transducer_callback("Main", "SS", "TTR ON")
        await fixture.async_execute(device.async_tactile_transducer_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_trigger_on_returns_early_when_on(self):
        """Test that async_trigger_on returns early when trigger is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._trigger_callback("Main", "TRG", "1 ON")
        await fixture.async_execute(device.async_trigger_on(1))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_trigger_on_sends_command_when_off(self):
        """Test that async_trigger_on sends command if trigger is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._trigger_callback("Main", "TRG", "1 OFF")
        await fixture.async_execute(device.async_trigger_on(1))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_trigger_off_returns_early_when_off(self):
        """Test that async_trigger_off returns early when trigger is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._trigger_callback("Main", "TRG", "1 OFF")
        await fixture.async_execute(device.async_trigger_off(1))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_trigger_off_sends_command_when_on(self):
        """Test that async_trigger_off sends command if trigger is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._trigger_callback("Main", "TRG", "1 ON")
        await fixture.async_execute(device.async_trigger_off(1))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_eco_mode_returns_early_when_matches(self):
        """Test that async_eco_mode returns early when eco mode matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._eco_mode_callback("Main", "ECO", "ON")
        await fixture.async_execute(device.async_eco_mode("On"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_eco_mode_sends_command_when_differs(self):
        """Test that async_eco_mode sends command if eco mode differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._eco_mode_callback("Main", "ECO", "AUTO")
        await fixture.async_execute(device.async_eco_mode("On"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_eco_mode_raises_on_invalid(self):
        """Test that async_eco_mode raises on invalid eco mode."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._eco_mode_callback("Main", "ECO", "On")
        with pytest.raises(AvrCommandError):
            await device.async_eco_mode("InvalidMode")

    @pytest.mark.asyncio
    async def test_async_hdmi_output_returns_early_when_matches(self):
        """Test that async_hdmi_output returns early when HDMI output matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_output_callback("Main", "VS", "MONI1")
        await fixture.async_execute(device.async_hdmi_output("HDMI1"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_hdmi_output_sends_command_when_differs(self):
        """Test that async_hdmi_output sends command if HDMI output differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_output_callback("Main", "VS", "MONIAUTO")
        await fixture.async_execute(device.async_hdmi_output("HDMI2"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_hdmi_output_raises_on_invalid(self):
        """Test that async_hdmi_output raises on invalid HDMI output."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_output_callback("Main", "VS", "MONI1")
        with pytest.raises(AvrCommandError):
            await device.async_hdmi_output("InvalidOutput")

    @pytest.mark.asyncio
    async def test_async_hdmi_audio_decode_returns_early_when_setting_matches(self):
        """Test that async_hdmi_audio_decode returns early when setting matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_audio_decode_callback("Main", "VS", "AUDIO AMP")
        await fixture.async_execute(device.async_hdmi_audio_decode("AMP"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_hdmi_audio_decode_sends_command_when_differs(self):
        """Test that async_hdmi_audio_decode sends command if setting differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_audio_decode_callback("Main", "VS", "AUDIO AMP")
        await fixture.async_execute(device.async_hdmi_audio_decode("TV"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_hdmi_audio_decode_raises_on_invalid(self):
        """Test that async_hdmi_audio_decode raises on invalid setting."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._hdmi_audio_decode_callback("Main", "VS", "Auto")
        with pytest.raises(AvrCommandError):
            await device.async_hdmi_audio_decode("InvalidMode")

    @pytest.mark.asyncio
    async def test_async_video_processing_mode_returns_early_when_mode_matches(self):
        """Test that async_video_processing_mode returns early when mode matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._video_processing_mode_callback("Main", "VS", "VPMAUTO")
        await fixture.async_execute(device.async_video_processing_mode("Auto"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_video_processing_mode_sends_command_when_differs(self):
        """Test that async_video_processing_mode sends command if mode differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._video_processing_mode_callback("Main", "VS", "VPMAUTO")
        await fixture.async_execute(device.async_video_processing_mode("Movie"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_video_processing_mode_raises_on_invalid(self):
        """Test that async_video_processing_mode raises on invalid mode."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._video_processing_mode_callback("Main", "VS", "VPMAUTO")
        with pytest.raises(AvrCommandError):
            await device.async_video_processing_mode("InvalidMode")

    @pytest.mark.asyncio
    async def test_async_speaker_preset_returns_early_when_matches(self):
        """Test that async_speaker_preset returns early when preset matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._speaker_preset_callback("Main", "SP", "PR 1")
        await fixture.async_execute(device.async_speaker_preset(1))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_speaker_preset_sends_command_when_differs(self):
        """Test that async_speaker_preset sends command if preset differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._speaker_preset_callback("Main", "SP", "PR 1")
        await fixture.async_execute(device.async_speaker_preset(2))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_speaker_preset_raises_on_invalid(self):
        """Test that async_speaker_preset raises on invalid preset."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._speaker_preset_callback("Main", "SP", "PR 1")
        with pytest.raises(AvrCommandError):
            await device.async_speaker_preset(42)

    @pytest.mark.asyncio
    async def test_async_bt_transmitter_on_returns_early_when_on(self):
        """Test that async_bt_transmitter_on returns early when transmitter is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "BT", "TX ON")
        await fixture.async_execute(device.async_bt_transmitter_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bt_transmitter_on_sends_command_when_off(self):
        """Test that async_bt_transmitter_on sends command if transmitter is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "BT", "TX OFF")
        await fixture.async_execute(device.async_bt_transmitter_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bt_transmitter_off_returns_early_when_off(self):
        """Test that async_bt_transmitter_off returns early when transmitter is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "BT", "TX OFF")
        await fixture.async_execute(device.async_bt_transmitter_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bt_transmitter_off_sends_command_when_on(self):
        """Test that async_bt_transmitter_off sends command if transmitter is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "BT", "TX ON")
        await fixture.async_execute(device.async_bt_transmitter_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_audio_restorer_low_returns_early_when_low(self):
        """Test that async_audio_restorer_low returns early when setting is low."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._audio_restorer_callback("Main", "PS", "RSTR LOW")
        await fixture.async_execute(device.async_audio_restorer("Low"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_audio_restorer_low_sends_command_when_off(self):
        """Test that async_audio_restorer_low sends command if setting is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._audio_restorer_callback("Main", "PS", "RSTR OFF")
        await fixture.async_execute(device.async_audio_restorer("Low"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_graphic_eq_on_returns_early_when_on(self):
        """Test that async_graphic_eq_on returns early when graphic EQ is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._graphic_eq_callback("Main", "PS", "GEQ ON")
        await fixture.async_execute(device.async_graphic_eq_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_graphic_eq_on_sends_command_when_off(self):
        """Test that async_graphic_eq_on sends command if graphic EQ is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._graphic_eq_callback("Main", "PS", "GEQ OFF")
        await fixture.async_execute(device.async_graphic_eq_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_graphic_eq_off_returns_early_when_off(self):
        """Test that async_graphic_eq_off returns early when graphic EQ is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._graphic_eq_callback("Main", "PS", "GEQ OFF")
        await fixture.async_execute(device.async_graphic_eq_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_graphic_eq_off_sends_command_when_on(self):
        """Test that async_graphic_eq_off sends command if graphic EQ is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._graphic_eq_callback("Main", "PS", "GEQ ON")
        await fixture.async_execute(device.async_graphic_eq_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_headphone_eq_on_returns_early_when_on(self):
        """Test that async_headphone_eq_on returns early when headphone EQ is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._headphone_eq_callback("Main", "PS", "HEQ ON")
        await fixture.async_execute(device.async_headphone_eq_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_headphone_eq_on_sends_command_when_off(self):
        """Test that async_headphone_eq_on sends command if headphone EQ is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._headphone_eq_callback("Main", "PS", "HEQ OFF")
        await fixture.async_execute(device.async_headphone_eq_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_headphone_eq_off_returns_early_when_off(self):
        """Test that async_headphone_eq_off returns early when headphone EQ is off."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._headphone_eq_callback("Main", "PS", "HEQ OFF")
        await fixture.async_execute(device.async_headphone_eq_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_headphone_eq_off_sends_command_when_on(self):
        """Test that async_headphone_eq_off sends command if headphone EQ is on."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._headphone_eq_callback("Main", "PS", "HEQ ON")
        await fixture.async_execute(device.async_headphone_eq_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_illumination_returns_early_when_matches(self):
        """Test that async_illumination returns early when illumination matches."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._illumination_callback("Main", "", "ILL AUTO")
        await fixture.async_execute(device.async_illumination("Auto"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_illumination_sends_command_when_differs(self):
        """Test that async_illumination sends command if illumination differs."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._illumination_callback("Main", "", "ILL AUTO")
        await fixture.async_execute(device.async_illumination("Off"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_illumination_raises_on_invalid(self):
        """Test that async_illumination raises on invalid illumination."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._illumination_callback("Main", "", "ILL AUTO")
        with pytest.raises(AvrCommandError):
            await device.async_illumination("InvalidState")

    @pytest.mark.asyncio
    async def test_async_auto_lip_sync_on_returns_early_when_on(self):
        """Test that async_auto_lip_sync_on returns early when auto lip sync is on."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._auto_lip_sync_callback("Main", "SS", "HOS ON")
        await fixture.async_execute(device.async_auto_lip_sync_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_auto_lip_sync_on_sends_command_when_off(self):
        """Test that async_auto_lip_sync_on sends command if auto lip sync is off."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._auto_lip_sync_callback("Main", "SS", "HOS OFF")
        await fixture.async_execute(device.async_auto_lip_sync_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_auto_lip_sync_off_returns_early_when_off(self):
        """Test that async_auto_lip_sync_off returns early when auto lip sync is off."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._auto_lip_sync_callback("Main", "SS", "HOS OFF")
        await fixture.async_execute(device.async_auto_lip_sync_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_auto_lip_sync_off_sends_command_when_on(self):
        """Test that async_auto_lip_sync_off sends command if auto lip sync is on."""
        fixture = DeviceTestFixture(False)
        device = fixture.device_info
        device._auto_lip_sync_callback("Main", "SS", "HOS ON")
        await fixture.async_execute(device.async_auto_lip_sync_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bt_output_mode_returns_early_when_matches(self):
        """Test that async_bt_output_mode returns early when mode matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "", "TX SP")
        await fixture.async_execute(device.async_bt_output_mode("Bluetooth + Speakers"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bt_output_mode_sends_command_when_differs(self):
        """Test that async_bt_output_mode sends command if mode differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "", "TX SP")
        await fixture.async_execute(device.async_bt_output_mode("Bluetooth Only"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bt_output_mode_raises_on_invalid(self):
        """Test that async_bt_output_mode raises on invalid mode."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._bt_callback("Main", "", "TX SP")
        with pytest.raises(AvrCommandError):
            await device.async_bt_output_mode("INVALID")

    @pytest.mark.asyncio
    async def test_async_audio_restorer_returns_early_when_matches(self):
        """Test that async_audio_restorer returns early when setting matches."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._audio_restorer_callback("Main", "PS", "RSTR OFF")
        await fixture.async_execute(device.async_audio_restorer("Off"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_audio_restorer_sends_command_when_differs(self):
        """Test that async_audio_restorer sends command if setting differs."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._audio_restorer_callback("Main", "PS", "RSTR OFF")
        await fixture.async_execute(device.async_audio_restorer("High"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_audio_restorer_raises_on_invalid(self):
        """Test that async_audio_restorer raises on invalid setting."""
        fixture = DeviceTestFixture(True)
        device = fixture.device_info
        device._audio_restorer_callback("Main", "PS", "RSTR OFF")
        with pytest.raises(AvrCommandError):
            await device.async_audio_restorer("Max")
