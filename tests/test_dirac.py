#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of dirac.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest

from denonavr.const import DIRAC_FILTER_MAP
from denonavr.dirac import DenonAVRDirac
from denonavr.exceptions import AvrCommandError
from tests.test_helpers import DeviceTestFixture


class TestDenonAVRDirac:
    """Test cases for DenonAVRDirac."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("filter_val", list(DIRAC_FILTER_MAP.keys()))
    async def test_async_dirac_filter_returns_early_when_matches(self, filter_val):
        """Test that async_dirac_filter returns early when same filter."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        mapped = DIRAC_FILTER_MAP[filter_val]
        assert mapped is not None, f"Mapping for {filter_val} should not be None"
        device._ps_callback("Main", "", f"DIRAC:{mapped}")
        await fixture.async_execute(device.async_dirac_filter(filter_val))
        await device.async_dirac_filter(filter_val)
        fixture.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "from_val,to_val",
        [
            ("Off", "Slot 1"),
            ("Slot 1", "Slot 2"),
            ("Slot 2", "Slot 3"),
            ("Slot 3", "Off"),
        ],
    )
    async def test_async_dirac_filter_sends_command_when_differs(
        self, from_val, to_val
    ):
        """Test that async_dirac_filter sends command when filter differs."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        mapped = DIRAC_FILTER_MAP[from_val]
        assert mapped is not None, f"Mapping for {from_val} should not be None"
        device._ps_callback("Main", "", f"DIRAC {mapped}")
        await fixture.async_execute(device.async_dirac_filter(to_val))  # type: ignore
        fixture.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_dirac_filter_raises_on_invalid(self):
        """Test that async_dirac_filter raises on invalid filter."""
        fixture = DeviceTestFixture(True)
        device = DenonAVRDirac(device=fixture.device_info)
        with pytest.raises(AvrCommandError):
            await fixture.async_execute(device.async_dirac_filter("notavalidfilter"))
