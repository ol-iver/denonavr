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
    def _input(source: str) -> tuple[DeviceTestFixture, DenonAVRInput]:
        fixture = DeviceTestFixture(True)
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
