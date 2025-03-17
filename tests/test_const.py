#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some tests for mappings in const.py.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import unittest
from typing import get_args

from denonavr.const import (
    CHANNEL_MAP,
    DIMMER_MODE_MAP,
    DIRAC_FILTER_MAP,
    ECO_MODE_MAP,
    HDMI_OUTPUT_MAP,
    Channels,
    DimmerModes,
    DiracFilters,
    EcoModes,
    HDMIOutputs,
)


class TestMappings(unittest.TestCase):
    """Test case for mappings in const.py."""

    def test_dimmer_modes_mappings(self):
        """Test that all dimmer modes are in the mapping."""
        for mode in get_args(DimmerModes):
            self.assertIn(mode, DIMMER_MODE_MAP)

    def test_eco_modes_mappings(self):
        """Test that all eco-modes are in the mapping."""
        for mode in get_args(EcoModes):
            self.assertIn(mode, ECO_MODE_MAP)

    def test_hdmi_outputs_mappings(self):
        """Test that all hdmi outputs are in the mapping."""
        for hdmi_output in get_args(HDMIOutputs):
            self.assertIn(hdmi_output, HDMI_OUTPUT_MAP)

    def test_channel_mappings(self):
        """Test that all channels are in the mapping."""
        for channel in get_args(Channels):
            self.assertIn(channel, CHANNEL_MAP)

    def test_dirac_filter_mappings(self):
        """Test that dirac filters are in the mapping."""
        for dirac_filter in get_args(DiracFilters):
            self.assertIn(dirac_filter, DIRAC_FILTER_MAP)


if __name__ == "__main__":
    unittest.main()
