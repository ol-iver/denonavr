#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for async_set_volume with values outside the valid range."""

import logging

import pytest

from denonavr.volume import DenonAVRVolume
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.mark.asyncio
@pytest.mark.parametrize("volume", [-80.5, -100, 18.5, 50])
async def test_async_set_volume_skips_out_of_range(volume, caplog):
    """Test that an out of range volume is logged and no command is sent."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRVolume(device=fixture.device_info)
    with caplog.at_level(logging.WARNING):
        await fixture.async_execute(device.async_set_volume(volume))

    fixture.assert_not_called()
    assert "out of range" in caplog.text


@pytest.mark.asyncio
@pytest.mark.parametrize("volume", [-80, -50.5, 0, 18])
async def test_async_set_volume_sends_valid_volume(volume):
    """Test that volumes inside the range, including the limits, are sent."""
    fixture = DeviceTestFixture(True)
    device = DenonAVRVolume(device=fixture.device_info)
    device._max_volume_callback("Main", "SS", "VCTZMALIM 98")
    await fixture.async_execute(device.async_set_volume(volume))
    fixture.assert_called_once()
