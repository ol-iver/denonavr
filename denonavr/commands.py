#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains instances of the XmlCommand class that are representations
of the Denon AVR 2016 XML command structure.  Refer to ./XML_data_dump.txt for
more information or to find out how to sniff commands on your own AVR.
"""
from .helpers import XmlCommand1, XmlCommand3

SET_DYNAMIC_VOL = XmlCommand3(
    "Dynamic Volume", "SetAudyssey",
    (0, 3), param="dynamicvol",
    values=[
        "Off",
        "Light",
        "Medium",
        "Heavy"]
)
