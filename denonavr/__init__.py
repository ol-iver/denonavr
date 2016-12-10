#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automation Library for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

# Set default logging handler to avoid "No handler found" warnings.
import logging

# Import denonavr module
from .denonavr import DenonAVR
from . import ssdp

logging.getLogger(__name__).addHandler(logging.NullHandler())

__title__ = "denonavr"
__version__ = "0.2.0"


def discover(attempts=3):
    """
    Discover all DenonAVR devices in LAN zone.

    Returns a list of dictionaries which includes all discovered DenonAVR
    devices with keys "host", "ModelName" and "PresentationURL".
    Returns "None" if no DenonAVR receiver was found.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
    return ssdp.identify_denonavr_receivers(attempts)


def init_all_receivers(attempts=3):
    """
    Initialize all discovered DenonAVR receivers in LAN zone.

    Returns a list of created DenonAVR instances.
    Returns "None" if no DenonAVR receiver was found.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
    receivers = discover(attempts)

    if receivers is None:
        return None
    else:
        init_receivers = []
        for receiver in receivers:
            init_receiver = DenonAVR(receiver["host"])
            init_receivers.append(init_receiver)
        return init_receivers
