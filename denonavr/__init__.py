#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automation Library for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio

# Set default logging handler to avoid "No handler found" warnings.
import logging

# Import denonavr module
from .denonavr import DenonAVR
from .mdns import async_query_receivers
from .ssdp import async_identify_denonavr_receivers

logging.getLogger(__name__).addHandler(logging.NullHandler())

__title__ = "denonavr"
__version__ = "1.3.0-dev"


async def async_discover(timeout: float = 5):
    """
    Discover all Denon AVR devices in LAN zone.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    Combines both mDNS and SSDP discovery methods.
    By default, SSDP broadcasts are sent once with a 2 seconds timeout.

    Args:
        timeout: Number of seconds to wait for mDNS responses.
    """

    async def async_query_mdns() -> list[dict]:
        receivers = await async_query_receivers(timeout)
        return [
            {
                "host": receiver.ip_address,
                "modelName": receiver.model,
                "friendlyName": receiver.name,
                "presentationURL": None,
            }
            for receiver in (receivers or [])
        ]

    tasks = [
        async_query_mdns(),
        async_identify_denonavr_receivers(),
    ]

    results = await asyncio.gather(*tasks)
    combined: dict[str, dict] = {}
    for result in results:
        for entry in result:
            host = entry["host"]
            if host not in combined:
                combined[host] = entry
            elif (
                combined[host]["presentationURL"] is None
                and entry["presentationURL"] is not None
            ):
                combined[host] = entry
    return list(combined.values())


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
