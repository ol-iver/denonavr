#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for the parsing of volume values."""

import pytest

from denonavr.volume import DenonAVRVolume, convert_volume
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.mark.parametrize(
    "input_val,expected",
    [
        ("--", -80.0),
        ("-10", -10.0),
        ("-10.5", -10.5),
        (" -35.5 ", -35.5),
        ("0.0", 0.0),
        (-20.0, -20.0),
        (None, -80.0),
    ],
)
def test_convert_volume(input_val, expected):
    """Test convert_volume function with dB inputs."""
    assert convert_volume(input_val) == expected


@pytest.mark.parametrize(
    "input_str,expected",
    [
        ("--", -80.0),  # -- means lowest volume, -80.0
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
        ("123", -67.7),  # Should be handled as 12.3 - 80
        ("ab23", -80.0),  # Invalid, should clamp to min
        ("1000", -80.0),  # Invalid, should clamp to min
    ],
)
def test_volume_callback(input_str, expected):
    """Test _volume_callback parsing of telnet volume values."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRVolume(device=fixture.device_info)
    device._volume_callback("Main", "", input_str)
    assert device.volume == expected
