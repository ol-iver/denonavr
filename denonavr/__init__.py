#!/usr/bin/env python3
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
from .ssdp import async_identify_denonavr_receivers
from .decorators import run_async_synchronously

logging.getLogger(__name__).addHandler(logging.NullHandler())

__title__ = "denonavr"
__version__ = "0.10.11"


async def async_discover():
    """
    Discover all Denon AVR devices in LAN zone.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    By default SSDP broadcasts are sent once with a 2 seconds timeout.
    """
    return await async_identify_denonavr_receivers()


@run_async_synchronously(async_func=async_discover)
def discover():
    """
    Discover all Denon AVR devices in LAN zone.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    By default SSDP broadcasts are sent once with a 2 seconds timeout.
    """


async def async_init_all_receivers():
    """
    Initialize all discovered Denon AVR receivers in LAN zone.

    Returns a list of created Denon AVR instances.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
    receivers = await async_discover()

    init_receivers = []
    for receiver in receivers:
        init_receiver = DenonAVR(receiver["host"])
        init_receivers.append(init_receiver)
    return init_receivers


@run_async_synchronously(async_func=async_init_all_receivers)
def init_all_receivers():
    """
    Initialize all discovered Denon AVR receivers in LAN zone.

    Returns a list of created Denon AVR instances.
    By default SSDP broadcasts are sent up to 3 times with a 2 seconds timeout.
    """
