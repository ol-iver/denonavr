#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the range of the Auro-Matic 3D strength."""

import pytest

from denonavr.exceptions import AvrCommandError
from denonavr.soundmode import DenonAVRSoundMode
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def _soundmode() -> tuple[DeviceTestFixture, DenonAVRSoundMode]:
    fixture = DeviceTestFixture(True)
    return fixture, DenonAVRSoundMode(device=fixture.device_info)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strength, expected",
    [(0, "PSAUROST 00"), (1, "PSAUROST 01"), (10, "PSAUROST 10"), (15, "PSAUROST 15")],
)
async def test_async_auromatic_3d_strength_accepts_0_to_15(strength, expected):
    """Test that the strength is sent with two digits for 0 to 15."""
    fixture, device = _soundmode()
    await fixture.async_execute(device.async_auromatic_3d_strength(strength))
    fixture._mock_telnet.assert_called_once_with(expected)


@pytest.mark.asyncio
@pytest.mark.parametrize("strength", [-1, 16, 99])
async def test_async_auromatic_3d_strength_rejects_values_outside_the_range(strength):
    """Test that values outside 0-15 are rejected."""
    fixture, device = _soundmode()
    with pytest.raises(AvrCommandError):
        await fixture.async_execute(device.async_auromatic_3d_strength(strength))
