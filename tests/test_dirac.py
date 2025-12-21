#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of dirac.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.dirac import DenonAVRDirac
from denonavr.exceptions import AvrCommandError
from tests.test_helpers import DeviceTestFixture


class TestDenonAVRDirac:
    """Test cases for DenonAVRDirac."""

    @pytest.mark.asyncio
    async def test_async_dirac_filter_returns_early_when_matches(self):
        """Test that async_dirac_filter returns early when same filter."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        device._ps_callback("Main", "", "DIRAC:1")
        await fixture.async_execute(device.async_dirac_filter("Slot 1"))
        fixture.assert_not_called()

    @pytest.mark.asyncio
    async def test_async_dirac_filter_sends_command_when_differs(self):
        """Test that async_dirac_filter sends command when filter differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        device._ps_callback("Main", "", "DIRAC OFF")
        await fixture.async_execute(device.async_dirac_filter("Slot 1"))
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dirac_filter_raises_on_invalid(self):
        """Test that async_dirac_filter raises on invalid filter."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(
                device.async_dirac_filter("notavalidfilter")  # type: ignore
            )
