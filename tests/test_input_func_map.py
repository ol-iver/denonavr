#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the input function maps."""

import pytest

from denonavr import DenonAVR
from denonavr.input import DenonAVRInput
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.fixture(name="input_device")
def input_device_fixture():
    """Return an input instance with two renamed sources."""
    device = DenonAVRInput(device=DeviceTestFixture(True).device_info)
    device._input_func_map = {"Living TV": "TV", "Console": "GAME"}
    device._input_func_map_rev = {"TV": "Living TV", "GAME": "Console"}
    return device


def test_input_func_map(input_device):
    """Test that the map has the names on the receiver as keys."""
    assert input_device.input_func_map == {"Living TV": "TV", "Console": "GAME"}


def test_input_func_map_reverse(input_device):
    """Test that the reverse map has the default names as keys."""
    assert input_device.input_func_map_reverse == {
        "TV": "Living TV",
        "GAME": "Console",
    }


def test_maps_are_copies(input_device):
    """Test that changing a returned map does not change the receiver state."""
    input_device.input_func_map["New"] = "NEW"
    input_device.input_func_map_reverse["NEW"] = "New"
    assert "New" not in input_device.input_func_map
    assert "NEW" not in input_device.input_func_map_reverse
    assert input_device.input_func_list == ["Console", "Living TV"]


def test_maps_are_available_on_receiver_class():
    """Test that the maps are available on the public class."""
    receiver = DenonAVR("127.0.0.1")
    receiver.input._input_func_map = {"Living TV": "TV"}
    receiver.input._input_func_map_rev = {"TV": "Living TV"}
    assert receiver.input_func_map == {"Living TV": "TV"}
    assert receiver.input_func_map_reverse == {"TV": "Living TV"}
