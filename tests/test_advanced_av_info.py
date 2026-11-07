#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the advanced audio and video info of DenonAVRDeviceInfo."""

import asyncio
from unittest.mock import AsyncMock, PropertyMock, patch

import pytest

from denonavr.foundation import channel_status_to_str
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def _device():
    return DeviceTestFixture(True).device_info


@pytest.mark.parametrize(
    "callback, event, parameter, attribute, expected",
    [
        (
            "_video_signal_callback",
            "SS",
            "INFSIGRES I 4K60",
            "video_hdmi_signal_in",
            "4K60",
        ),
        (
            "_video_signal_callback",
            "SS",
            "INFSIGRES O 1080p",
            "video_hdmi_signal_out",
            "1080p",
        ),
        (
            "_video_signal_callback",
            "SS",
            "INFSIGRES I ---",
            "video_hdmi_signal_in",
            None,
        ),
        ("_video_signal_callback", "SY", "SDVIN 4K24", "video_hdmi_signal_in", "4K24"),
        (
            "_video_signal_callback",
            "SY",
            "SDVOUT 4K24",
            "video_hdmi_signal_out",
            "4K24",
        ),
        (
            "_audio_sampling_rate_callback",
            "SS",
            "INFAISFSV 441",
            "audio_sampling_rate",
            "44.1",
        ),
        (
            "_audio_sampling_rate_callback",
            "SS",
            "INFAISFSV 48K",
            "audio_sampling_rate",
            "48",
        ),
        (
            "_audio_sampling_rate_callback",
            "SS",
            "INFAISFSV NON",
            "audio_sampling_rate",
            None,
        ),
        ("_hdr_callback", "SS", "INFSIGHDR I HDR10", "hdr_input", "HDR10"),
        ("_hdr_callback", "SS", "INFSIGHDR O ---", "hdr_output", None),
        ("_pixel_depth_callback", "SS", "INFSIGPIX 12", "pixel_depth_input", "8-bit"),
        ("_pixel_depth_callback", "SS", "INFSIGPIX 12", "pixel_depth_output", "10-bit"),
        ("_pixel_depth_callback", "SS", "INFSIGPIX 01", "pixel_depth_input", "Unknown"),
        ("_pixel_depth_callback", "SS", "INFSIGPIX 01", "pixel_depth_output", "8-bit"),
        ("_pixel_depth_callback", "SS", "INFSIGPIX 33", "pixel_depth_input", "12-bit"),
        ("_max_frl_callback", "SS", "INFSIGFRL I 48G", "max_frl_input", "48G"),
        ("_max_frl_callback", "SS", "INFSIGFRL O ---", "max_frl_output", None),
        ("_max_frl_callback", "SS", "INFSIGFRL I48G", "max_frl_input", "48G"),
        ("_max_frl_callback", "SS", "INFSIGFRL I---", "max_frl_input", None),
        ("_max_frl_callback", "SS", "INFSIGFRL O---", "max_frl_output", None),
        ("_colorspace_callback", "SS", "INFSIGCOS 23", "colorspace_input", "4:4:4"),
        ("_colorspace_callback", "SS", "INFSIGCOS 23", "colorspace_output", "RGB"),
        ("_colorspace_callback", "SS", "INFSIGCOS 88", "colorspace_input", "4:2:0"),
        ("_colorspace_callback", "SS", "INFSIGCOS 11", "colorspace_output", "4:2:2"),
        ("_colorspace_callback", "SS", "INFSIGCOS 03", "colorspace_input", None),
        ("_colorspace_callback", "SS", "INFSIGCOS 03", "colorspace_output", "RGB"),
        (
            "_colorspace_callback",
            "SS",
            "INFSIGCOS 99",
            "colorspace_input",
            "4:2:2/BT.2020",
        ),
        (
            "_max_resolution_callback",
            "SY",
            "HDMIDIAGMAXRES 4K18G",
            "max_resolution",
            "4K18Gbps",
        ),
        (
            "_max_resolution_callback",
            "SY",
            "HDMIDIAGMAXRES NO",
            "max_resolution",
            "No limit",
        ),
        (
            "_audio_signal_callback",
            "SY",
            "SDA Dolby Atmos",
            "audio_signal",
            "Dolby Atmos",
        ),
        ("_audio_signal_callback", "SY", "SDA Unknown", "audio_signal", "-"),
        (
            "_audio_sound_callback",
            "SY",
            "SMI Dolby Atmos",
            "audio_sound",
            "Dolby Atmos",
        ),
        (
            "_input_channel_callback",
            "OP",
            "INFINS " + "22000000".ljust(32, "0"),
            "input_channels",
            "2.0",
        ),
        (
            "_output_channels_callback",
            "OP",
            "INFASP " + "22222222".ljust(32, "0"),
            "output_channels",
            "7.1",
        ),
    ],
)
def test_callbacks(callback, event, parameter, attribute, expected):
    """Test that telnet events update the properties."""
    device = _device()
    assert getattr(device, attribute) is None
    getattr(device, callback)("Main", event, parameter)
    assert getattr(device, attribute) == expected


@pytest.mark.parametrize(
    "colorspace, hdr, expected",
    [
        ("INFSIGCOS 22", "INFSIGHDR I---", "4:4:4"),
        ("INFSIGCOS 22", "INFSIGHDR IHDR10", "4:4:4/BT.2020"),
        ("INFSIGCOS 11", "INFSIGHDR IHDR10+", "4:2:2/BT.2020"),
        ("INFSIGCOS 11", "INFSIGHDR IDolby Vision", "4:2:2/BT.2020"),
        ("INFSIGCOS 99", "INFSIGHDR I---", "4:2:2/BT.2020"),
        ("INFSIGCOS 99", "INFSIGHDR IHDR10", "4:2:2/BT.2020"),
        ("INFSIGCOS 03", "INFSIGHDR IHDR10", None),
    ],
)
def test_colorspace_bt2020(colorspace, hdr, expected):
    """Test that BT.2020 is added for HDR if the receiver did not send it."""
    device = _device()
    device._colorspace_callback("Main", "SS", colorspace)
    device._hdr_callback("Main", "SS", hdr)
    assert device.colorspace_input == expected


@pytest.mark.parametrize(
    "resolution, pixel_depth, expected",
    [
        ("INFSIGRES I1080p25", "INFSIGPIX 03", "12-bit"),
        ("INFSIGRES I4K24", "INFSIGPIX 01", "8-bit"),
        ("INFSIGRES I1080p50", "INFSIGPIX 31", "12-bit"),
        ("INFSIGRES I1080p60", "INFSIGPIX 11", "8-bit"),
        # No input signal, the 0 stays unknown
        ("INFSIGRES I---", "INFSIGPIX 01", "Unknown"),
        ("INFSIGRES I---", "INFSIGPIX 00", "Unknown"),
        # Nothing to take over, both are unknown
        ("INFSIGRES I1080p25", "INFSIGPIX 00", "Unknown"),
    ],
)
def test_pixel_depth_input_without_indication(resolution, pixel_depth, expected):
    """Test that an input without an indicated depth takes the output depth."""
    device = _device()
    device._video_signal_callback("Main", "SS", resolution)
    device._pixel_depth_callback("Main", "SS", pixel_depth)
    assert device.pixel_depth_input == expected


@pytest.mark.parametrize(
    "parameters, expected",
    [
        (["HOS ON"], True),
        (["HOS OFF"], False),
        (["HOSALS ON"], True),
        # The end of the HOS block and other HOS values are ignored
        (["HOS ON", "HOS END"], True),
        (["HOS ON", "HOSCON OFF"], True),
    ],
)
def test_auto_lip_sync_callback(parameters, expected):
    """Test that only HOS and HOSALS values change auto lip sync."""
    device = _device()
    for parameter in parameters:
        device._auto_lip_sync_callback("Main", "SS", parameter)
    assert device.auto_lip_sync is expected


def _feed(device, *parameters):
    for parameter in parameters:
        device._colorspace_callback("Main", "SS", parameter)
        device._hdr_callback("Main", "SS", parameter)
        device._extended_colorimetry_callback("Main", "SS", parameter)


@pytest.mark.parametrize(
    "colorspace, hdr, eci, expected_input, expected_output",
    [
        # Measured on an AVC-A10H, the screen showed the same
        (
            "INFSIGCOS 11",
            "INFSIGHDR IDolby Vision",
            "INFSIGECI 55",
            "4:2:2/BT.2020",
            "4:2:2/BT.2020",
        ),
        ("INFSIGCOS 33", "INFSIGHDR IDolby Vision", "INFSIGECI 00", "RGB", "RGB"),
        (
            "INFSIGCOS 22",
            "INFSIGHDR IHDR10",
            "INFSIGECI 55",
            "4:4:4/BT.2020",
            "4:4:4/BT.2020",
        ),
        ("INFSIGCOS 22", "INFSIGHDR I---", "INFSIGECI 00", "4:4:4", "4:4:4"),
        # Wide gamut without HDR
        (
            "INFSIGCOS 22",
            "INFSIGHDR I---",
            "INFSIGECI 55",
            "4:4:4/BT.2020",
            "4:4:4/BT.2020",
        ),
        # Each side follows its own digit
        ("INFSIGCOS 22", "INFSIGHDR I---", "INFSIGECI 50", "4:4:4/BT.2020", "4:4:4"),
        ("INFSIGCOS 22", "INFSIGHDR I---", "INFSIGECI 05", "4:4:4", "4:4:4/BT.2020"),
        # Already marked by the receiver, ECI does not change it
        (
            "INFSIGCOS 99",
            "INFSIGHDR I---",
            "INFSIGECI 00",
            "4:2:2/BT.2020",
            "4:2:2/BT.2020",
        ),
    ],
)
def test_extended_colorimetry(colorspace, hdr, eci, expected_input, expected_output):
    """Test that the extended colorimetry decides if BT.2020 is added."""
    device = _device()
    _feed(device, colorspace, hdr, eci)
    assert device.colorspace_input == expected_input
    assert device.colorspace_output == expected_output


def test_extended_colorimetry_comes_last():
    """Test that an event after the colorspace changes the result."""
    device = _device()
    _feed(device, "INFSIGCOS 22", "INFSIGHDR IHDR10")
    assert device.colorspace_input == "4:4:4/BT.2020"
    _feed(device, "INFSIGECI 00")
    assert device.colorspace_input == "4:4:4"


@pytest.mark.parametrize("parameter", ["INFSIGECI", "INFSIGECI 5", "INFSIGECI 555"])
def test_extended_colorimetry_ignores_bad_values(parameter):
    """Test that a malformed event leaves the HDR rule in use."""
    device = _device()
    _feed(device, "INFSIGCOS 22", "INFSIGHDR IHDR10", parameter)
    assert device.colorspace_input == "4:4:4/BT.2020"


@pytest.mark.parametrize(
    "callback, attribute",
    [
        ("_video_signal_callback", "video_hdmi_signal_in"),
        ("_audio_sampling_rate_callback", "audio_sampling_rate"),
        ("_hdr_callback", "hdr_input"),
        ("_pixel_depth_callback", "pixel_depth_input"),
        ("_max_frl_callback", "max_frl_input"),
        ("_colorspace_callback", "colorspace_input"),
        ("_max_resolution_callback", "max_resolution"),
        ("_audio_signal_callback", "audio_signal"),
        ("_audio_sound_callback", "audio_sound"),
        ("_input_channel_callback", "input_channels"),
        ("_output_channels_callback", "output_channels"),
    ],
)
def test_callbacks_ignore_other_events(callback, attribute):
    """Test that events with another prefix are ignored."""
    device = _device()
    getattr(device, callback)("Main", "SS", "TTR ON")
    assert getattr(device, attribute) is None


@pytest.mark.asyncio
async def test_trigger_sends_all_queries():
    """Test that all queries are sent without waiting for a confirmation."""
    device = _device()
    with (
        patch.object(
            type(device),
            "telnet_available",
            new_callable=PropertyMock,
            return_value=True,
        ),
        patch.object(
            device.telnet_api, "async_send_commands", new_callable=AsyncMock
        ) as mock_send,
        patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await device.async_trigger_advanced_audio_video_info_update()

    # The protocol asks for at least 50 ms between commands
    assert [call.args[0] for call in mock_sleep.await_args_list] == [0.05] * 13
    commands = [call.args[0] for call in mock_send.call_args_list]
    assert len(commands) == 13
    assert "SSINFSIGRES ?" in commands
    assert "SYSMI ?" in commands
    assert all(
        call.kwargs == {"skip_confirmation": True} for call in mock_send.call_args_list
    )


@pytest.mark.asyncio
async def test_trigger_without_telnet_sends_nothing():
    """Test that nothing is sent if telnet is not available."""
    device = _device()
    with patch.object(
        device.telnet_api, "async_send_commands", new_callable=AsyncMock
    ) as mock_send:
        await device.async_trigger_advanced_audio_video_info_update()

    mock_send.assert_not_called()


@pytest.mark.parametrize(
    "channel_status,expected",
    [
        ("00200000".ljust(32, "0"), "1.0"),
        ("22000000".ljust(32, "0"), "2.0"),
        ("22020000".ljust(32, "0"), "2.1"),
        ("22211111111111000000".ljust(32, "0"), "3.0"),
        ("20222000".ljust(32, "0"), "3.1"),
        ("22112211111111000000".ljust(32, "0"), "4.0"),
        ("22022200".ljust(32, "0"), "4.1"),
        ("22212211111111000000".ljust(32, "0"), "5.0"),
        ("22222211111111000000".ljust(32, "0"), "5.1"),
        ("22202220".ljust(32, "0"), "6.0"),
        ("22222211211111000000".ljust(32, "0"), "6.1"),
        ("22202222".ljust(32, "0"), "7.0"),
        ("22222222".ljust(32, "0"), "7.1"),
        ("22222211122111000000".ljust(32, "0"), "5.1.2"),
        ("22222211111112000000".ljust(32, "0"), "5.1.2"),
        ("22222211111112202000".ljust(32, "0"), "5.1.4"),
        ("22222222111111000000".ljust(32, "0"), "7.1"),
        ("22222222111111220000".ljust(32, "0"), "7.1.2"),
        ("22222222122112000000".ljust(32, "0"), "7.1.4"),
        ("22222222022000000000000002200000".ljust(32, "0"), "7.1.4"),
        ("22222222122112220000".ljust(32, "0"), "7.1.6"),
    ],
)
def test_channel_status_to_str(channel_status, expected):
    """Test channel_status_to_str function."""
    assert channel_status_to_str(channel_status) == expected
