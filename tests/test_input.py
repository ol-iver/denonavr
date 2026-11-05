#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for DenonAVRInput."""

import pytest

from denonavr.input import DenonAVRInput
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


class TestDenonAVRInput:
    """Test cases for DenonAVRInput."""

    @staticmethod
    def _input(
        source: str, power: str = "ON"
    ) -> tuple[DeviceTestFixture, DenonAVRInput]:
        fixture = DeviceTestFixture(True)
        fixture.device_info._power_callback("Main", "ZM", power)
        device = DenonAVRInput(device=fixture.device_info)
        device._input_func_map = {"TV Audio": "TV", "Game": "GAME"}
        device._input_func_map_rev = {"TV": "TV Audio", "GAME": "Game"}
        device._input_func = source
        return fixture, device

    @pytest.mark.asyncio
    async def test_async_set_input_func_returns_early_when_matches(self):
        """Test that no command is sent when the input is already selected."""
        fixture, device = self._input("TV Audio")
        await fixture.async_execute(device.async_set_input_func("TV Audio"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_set_input_func_sends_command_when_differs(self):
        """Test that a command is sent when another input is selected."""
        fixture, device = self._input("Game")
        await fixture.async_execute(device.async_set_input_func("TV Audio"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("power", ["OFF", "STANDBY"])
    async def test_async_set_input_func_sends_command_when_zone_is_off(self, power):
        """Test that the current input is sent when the zone is off.

        Selecting a source turns on a zone that is off.
        """
        fixture, device = self._input("TV Audio", power)
        await fixture.async_execute(device.async_set_input_func("TV Audio"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_input_func_sends_command_when_power_is_unknown(self):
        """Test that the current input is sent when the power state is not known."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRInput(device=fixture.device_info)
        device._input_func_map = {"TV Audio": "TV"}
        device._input_func_map_rev = {"TV": "TV Audio"}
        device._input_func = "TV Audio"
        await fixture.async_execute(device.async_set_input_func("TV Audio"))
        fixture.assert_called_once()
