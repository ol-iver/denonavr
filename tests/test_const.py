#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some tests for mappings in const.py.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import unittest
from types import SimpleNamespace
from typing import get_args

from denonavr.const import (
    CHANNEL_MAP_REVERSE,
    DIMMER_MODE_MAP_REVERSE,
    DIRAC_FILTER_MAP_REVERSE,
    ECO_MODE_MAP_REVERSE,
    HDMI_OUTPUT_MAP_REVERSE,
    Channels,
    DimmerModes,
    DiracFilters,
    EcoModes,
    HDMIOutputs,
)
from denonavr.soundmode import sound_mode_map_factory, sound_mode_rev_map_factory


class TestMappings(unittest.TestCase):
    """Test case for mappings in const.py."""

    def test_dimmer_modes_mappings(self):
        """Test that all dimmer modes are in the mapping."""
        for mode in get_args(DimmerModes):
            self.assertIn(mode, DIMMER_MODE_MAP_REVERSE)

    def test_eco_modes_mappings(self):
        """Test that all eco-modes are in the mapping."""
        for mode in get_args(EcoModes):
            self.assertIn(mode, ECO_MODE_MAP_REVERSE)

    def test_hdmi_outputs_mappings(self):
        """Test that all hdmi outputs are in the mapping."""
        for hdmi_output in get_args(HDMIOutputs):
            self.assertIn(hdmi_output, HDMI_OUTPUT_MAP_REVERSE)

    def test_channel_mappings(self):
        """Test that all channels are in the mapping."""
        for channel in get_args(Channels):
            self.assertIn(channel, CHANNEL_MAP_REVERSE)

    def test_dirac_filter_mappings(self):
        """Test that dirac filters are in the mapping."""
        for dirac_filter in get_args(DiracFilters):
            self.assertIn(dirac_filter, DIRAC_FILTER_MAP_REVERSE)

    def test_pl2_c_dsx_sound_mode(self):
        """Test that PL2 C DSX is matched to the MOVIE sound mode."""
        instance = SimpleNamespace(_sound_mode_map=sound_mode_map_factory())
        sound_mode_map_rev = sound_mode_rev_map_factory(instance)
        self.assertEqual(sound_mode_map_rev["PL2 C DSX"], "MOVIE")


if __name__ == "__main__":
    unittest.main()
