#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module defines the XML Commands of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

COMMAND_ENDPOINT = "/goform/AppCommand0300.xml"

AUDYSSEY_SET_CMD = "SetAudyssey"
AUDYSSEY_GET_CMD = "GetAudyssey"
AUDYSSEY_PARAMS = {
    "dynamiceq": {
        "0": "Off",
        "1": "On",
    },
    "reflevoffset": {
        "0": "0dB",
        "1": "+5dB",
        "2": "+10dB",
        "3": "+15dB",
    },
    "dynamicvol": {
        "0": "Off",
        "1": "Light",
        "2": "Medium",
        "3": "Heavy",
    },
    "multeq": {
        "0": "Off",
        "1": "Flat",
        "2": "L/R Bypass",
        "3": "Reference",
    },
}

SURROUND_PARAMETER_SET_CMD = "SetSurroundParameter"
SURROUND_PARAMETER_GET_CMD = "GetSurroundParameter"
SURROUND_PARAMETER_PARAMS = {
    "dyncomp": {
        "0": "Off",
        "1": "Low",
        "2": "Medium",
        "3": "High",
    },
    "lfe": {str(gain): f"{str(gain)}dB" for gain in range(0, -11, -1)},
}
