#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the IMAX high pass and low pass filters."""

import pytest

from denonavr.exceptions import AvrCommandError
from denonavr.soundmode import DenonAVRSoundMode
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def _soundmode() -> tuple[DeviceTestFixture, DenonAVRSoundMode]:
    fixture = DeviceTestFixture(True)
    return fixture, DenonAVRSoundMode(device=fixture.device_info)


@pytest.mark.asyncio
async def test_async_imax_hpf_returns_early_when_matches():
    """Test that no command is sent when the high pass filter is already set."""
    fixture, device = _soundmode()
    device._imax_callback("Main", "PS", "IMAXHPF 080")
    await fixture.async_execute(device.async_imax_hpf(80))
    fixture.assert_not_called()


@pytest.mark.asyncio
async def test_async_imax_hpf_sends_command_when_differs():
    """Test that a command is sent when another high pass filter is set."""
    fixture, device = _soundmode()
    device._imax_callback("Main", "PS", "IMAXHPF 060")
    await fixture.async_execute(device.async_imax_hpf(80))
    fixture.assert_called_once()
    fixture._mock_telnet.assert_called_once_with("PSIMAXHPF 080")


@pytest.mark.asyncio
async def test_async_imax_lpf_returns_early_when_matches():
    """Test that no command is sent when the low pass filter is already set."""
    fixture, device = _soundmode()
    device._imax_callback("Main", "PS", "IMAXLPF 120")
    await fixture.async_execute(device.async_imax_lpf(120))
    fixture.assert_not_called()


@pytest.mark.asyncio
async def test_async_imax_lpf_sends_command_when_differs():
    """Test that a command is sent when another low pass filter is set."""
    fixture, device = _soundmode()
    device._imax_callback("Main", "PS", "IMAXLPF 080")
    await fixture.async_execute(device.async_imax_lpf(120))
    fixture.assert_called_once()
    fixture._mock_telnet.assert_called_once_with("PSIMAXLPF 120")


@pytest.mark.asyncio
@pytest.mark.parametrize("value", ["80", 70, 0])
async def test_imax_filters_reject_invalid_values(value):
    """Test that values that are not valid frequencies are rejected."""
    fixture, device = _soundmode()
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(device.async_imax_hpf(value))  # type: ignore
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(device.async_imax_lpf(value))  # type: ignore
