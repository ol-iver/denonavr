#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automation Library for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
# pylint: disable=no-else-return

# Set default logging handler to avoid "No handler found" warnings.
import logging

# Import denonavr module
from .denonavr import DenonAVR
from . import ssdp

logging.getLogger(__name__).addHandler(logging.NullHandler())

__title__ = "denonavr"
__version__ = "0.5.3"


def discover():
    """
    Discover all Denon AVR devices in LAN zone.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    Returns "None" if no Denon AVR receiver was found.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
    return ssdp.identify_denonavr_receivers()


def init_all_receivers():
    """
    Initialize all discovered Denon AVR receivers in LAN zone.

    Returns a list of created Denon AVR instances.
    Returns "None" if no Denon AVR receiver was found.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
    receivers = discover()

    if receivers is None:
        return None
    else:
        init_receivers = []
        for receiver in receivers:
            init_receiver = DenonAVR(receiver["host"])
            init_receivers.append(init_receiver)
        return init_receivers
