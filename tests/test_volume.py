#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for DenonAVRVolume (volume logic).

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
import pytest

from denonavr.volume import DenonAVRVolume, parse_volume
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRVolume:
    """Test cases for DenonAVRVolume."""

    @pytest.mark.asyncio
    async def test_async_volume_up_returns_early_when_max(self):
        """Test that async_volume_up returns early if volume is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", "98")
        await fixture.async_execute(device.async_volume_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_volume_up_returns_early_when_custom_max(self):
        """Test that async_volume_up returns early if volume is at custom max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._max_volume_callback("Main", "", "MAX 30")
        device._volume_callback("Main", "", "30")
        await fixture.async_execute(device.async_volume_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_volume_up_sends_command_when_not_max(self):
        """Test that async_volume_up sends command if volume is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", "50")
        await fixture.async_execute(device.async_volume_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_volume_down_returns_early_when_min(self):
        """Test that async_volume_down returns early if volume is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", "00")
        await fixture.async_execute(device.async_volume_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_volume_down_sends_command_when_not_min(self):
        """Test that async_volume_down sends command if volume is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", "50")
        await fixture.async_execute(device.async_volume_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val", [-80, 18, 0])
    async def test_async_set_volume_returns_early_when_matches(self, from_val):
        """Test that async_set_volume returns early if value matches current volume."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", str(int(from_val + 80)).zfill(2))
        await fixture.async_execute(device.async_set_volume(from_val))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(0, 10), (-80, -12)])
    async def test_async_set_volume_sends_command_when_differs(self, from_val, to_val):
        """Test that async_set_volume sends command if value differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._volume_callback("Main", "", str(int(from_val + 80)).zfill(2))
        await fixture.async_execute(device.async_set_volume(to_val))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val", [-30, 0, 18])
    async def test_async_set_volume_custom_max_when_above_custom_max(self, from_val):
        """Test async_set_volume sets custom max when value exceeds custom max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._max_volume_callback("Main", "", "MAX 30")
        # add 80 to map to Denon scale
        # subtract 10 to not exceed custom max of 30 (-50)
        device._volume_callback("Main", "", str(int(from_val + 80 - 10)))
        await fixture.async_execute(device.async_set_volume(from_val))
        # add 80 to map to Denon scale
        fixture.assert_called_match_ends(f"MV{int(device.max_volume + 80)}")

    @pytest.mark.asyncio
    async def test_async_channel_volume_up_returns_early_when_max(self):
        """Test that async_channel_volume_up returns early if volume is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "CV", "FL 62")
        await fixture.async_execute(device.async_channel_volume_up("Front Left"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_channel_volume_up_sends_command_when_not_max(self):
        """Test that async_channel_volume_up sends command if volume is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "CV", "FL 615")
        await fixture.async_execute(device.async_channel_volume_up("Front Left"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_channel_volume_down_returns_early_when_min(self):
        """Test that async_channel_volume_down returns early if volume is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "CV", "FL 38")
        await fixture.async_execute(device.async_channel_volume_down("Front Left"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_channel_volume_down_sends_command_when_not_min(self):
        """Test that async_channel_volume_down sends command if not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "CV", "FL 385")
        await fixture.async_execute(device.async_channel_volume_down("Front Left"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(38, -12), (405, -9.5)])
    async def test_async_channel_volume_returns_early_when_matches(
        self, from_val, to_val
    ):
        """Test that async_channel_volume returns early if value matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "", f"FL {from_val}")
        await fixture.async_execute(device.async_channel_volume("Front Left", to_val))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(38, -11), (405, -3.5)])
    async def test_async_channel_volume_sends_command_when_differs(
        self, from_val, to_val
    ):
        """Test that async_channel_volume sends command if value differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._channel_volume_callback("Main", "", f"FL {from_val}")
        await fixture.async_execute(device.async_channel_volume("Front Left", to_val))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_subwoofer_on_returns_early_when_on(self):
        """Test that async_subwoofer_on returns early if subwoofer is already on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_state_callback("SWR ON")
        await fixture.async_execute(device.async_subwoofer_on())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_subwoofer_on_sends_command_when_off(self):
        """Test that async_subwoofer_on sends command if subwoofer is off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_state_callback("SWR OFF")
        await fixture.async_execute(device.async_subwoofer_on())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_subwoofer_off_returns_early_when_off(self):
        """Test that async_subwoofer_off returns early if subwoofer is already off."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_state_callback("SWR OFF")
        await fixture.async_execute(device.async_subwoofer_off())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_subwoofer_off_sends_command_when_on(self):
        """Test that async_subwoofer_off sends command if subwoofer is on."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_state_callback("SWR ON")
        await fixture.async_execute(device.async_subwoofer_off())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_subwoofer_level_up_returns_early_when_max(self):
        """Test that async_subwoofer_level_up returns early if level is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_levels_callback("SWL 62")
        await fixture.async_execute(device.async_subwoofer_level_up("Subwoofer"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_subwoofer_level_up_sends_command_when_not_max(self):
        """Test that async_subwoofer_level_up sends command if level is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_levels_callback("SWL 615")
        await fixture.async_execute(device.async_subwoofer_level_up("Subwoofer"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_subwoofer_level_down_returns_early_when_min(self):
        """Test that async_subwoofer_level_down returns early if level is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_levels_callback("SWL 38")
        await fixture.async_execute(device.async_subwoofer_level_down("Subwoofer"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_subwoofer_level_down_sends_command_when_not_min(self):
        """Test that async_subwoofer_level_down sends command if level not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._subwoofer_levels_callback("SWL 385")
        await fixture.async_execute(device.async_subwoofer_level_down("Subwoofer"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_lfe_up_returns_early_when_max(self):
        """Test that async_lfe_up returns early if LFE is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback("LFE 0")
        await fixture.async_execute(device.async_lfe_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_lfe_up_sends_command_when_not_max(self):
        """Test that async_lfe_up sends command if LFE is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback("LFE -2")
        await fixture.async_execute(device.async_lfe_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_lfe_down_returns_early_when_min(self):
        """Test that async_lfe_down returns early if LFE is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback("LFE 10")
        await fixture.async_execute(device.async_lfe_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_lfe_down_sends_command_when_not_min(self):
        """Test that async_lfe_down sends command if LFE is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback("LFE 9")
        await fixture.async_execute(device.async_lfe_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(10, -10), (6, -6)])
    async def test_async_lfe_returns_early_when_matches(self, from_val, to_val):
        """Test that async_lfe returns early if value matches current LFE."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback(f"LFE {from_val}")
        await fixture.async_execute(device.async_lfe(to_val))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(10, -6), (3, 0)])
    async def test_async_lfe_sends_command_when_differs(self, from_val, to_val):
        """Test that async_lfe sends command if value differs from current LFE."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._lfe_callback(f"LFE {from_val}")
        await fixture.async_execute(device.async_lfe(to_val))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bass_sync_up_returns_early_when_max(self):
        """Test that async_bass_sync_up returns early if bass sync is at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback("BSC 16")
        await fixture.async_execute(device.async_bass_sync_up())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bass_sync_up_sends_command_when_not_max(self):
        """Test that async_bass_sync_up sends command if bass sync is not at max."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback("BSC 3")
        await fixture.async_execute(device.async_bass_sync_up())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_bass_sync_down_returns_early_when_min(self):
        """Test that async_bass_sync_down returns early if bass sync is at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback("BSC 0")
        await fixture.async_execute(device.async_bass_sync_down())
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_bass_sync_down_sends_command_when_not_min(self):
        """Test that async_bass_sync_down sends command if bass sync is not at min."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback("BSC 1")
        await fixture.async_execute(device.async_bass_sync_down())
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val", [3, 12])
    async def test_async_bass_sync_returns_early_when_matches(self, from_val):
        """Test that async_bass_sync returns early if value matches."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback(f"BSC {from_val}")
        await fixture.async_execute(device.async_bass_sync(from_val))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("from_val,to_val", [(0, 6), (6, 12)])
    async def test_async_bass_sync_sends_command_when_differs(self, from_val, to_val):
        """Test that async_bass_sync sends command if value differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRVolume(device=fixture.device_info)
        device._bass_sync_callback(f"BSC {from_val}")
        await fixture.async_execute(device.async_bass_sync(to_val))
        fixture.assert_called_once()


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("00", -80.0),
        ("80", 0.0),
        ("98", 18.0),
        ("805", 0.5),
        ("005", -79.5),
        ("955", 15.5),
        ("180", -62.0),
        ("120", -68.0),
        (" 90 ", 10.0),
        ("999", 18.0),  # Should clamp to max
        ("-10", -80.0),  # Invalid, should clamp to min
        ("123", -67.7),  # Should be handled as 12.3 - 80
        ("ab23", -80.0),  # Invalid, should clamp to min
        ("1000", -80.0),  # Invalid, should clamp to min
        (None, -80.0),  # Invalid, should clamp to min
    ],
)
def test_convert_volume(input_str, expected):
    """Test convert_volume function with various inputs."""
    assert parse_volume(input_str) == expected
