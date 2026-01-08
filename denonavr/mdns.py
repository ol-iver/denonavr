#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers via mDNS.

:copyright: (c) 2025 by Henrik Widlund.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
import threading
from dataclasses import dataclass

from zeroconf import ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

_LOGGER = logging.getLogger(__name__)


@dataclass
class ServiceInfoRecord:
    """Record for a discovered mDNS service."""

    name: str
    type: str
    info: ServiceInfo | None


class MDNSListener(ServiceListener):
    """Listener for mDNS service discovery."""

    def __init__(self):
        """Initialize the MDNSListener."""
        self.services: list[ServiceInfoRecord] = []
        self.lock = threading.Lock()

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle the addition of a new service."""
        info = zc.get_service_info(type_, name)
        with self.lock:
            self.services.append(ServiceInfoRecord(name=name, type=type_, info=info))
        _LOGGER.debug("Service %s added for type %s", name, type_)
        if info:
            _LOGGER.debug("Address: %s, Port: %s", info.parsed_addresses(), info.port)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle the removal of a service."""
        with self.lock:
            self.services = [
                service
                for service in self.services
                if not (service.name == name and service.type == type_)
            ]
            _LOGGER.debug("Service %s removed for type %s", name, type_)

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """Handle the update of an existing service."""
        info = zc.get_service_info(type_, name)
        with self.lock:
            for record in self.services:
                if record.name == name and record.type == type_:
                    record.info = info
                    break
            else:
                # If the service was not previously recorded, add it now.
                self.services.append(
                    ServiceInfoRecord(name=name, type=type_, info=info)
                )
        _LOGGER.debug("Service %s updated for type %s", name, type_)
        if info:
            _LOGGER.debug("Address: %s, Port: %s", info.parsed_addresses(), info.port)


async def query_receivers(timeout: float = 5) -> list[ServiceInfoRecord] | None:
    """Query for Denon/Marantz receivers using mDNS."""
    async with AsyncZeroconf() as zeroconf:
        listener = MDNSListener()
        ServiceBrowser(zeroconf.zeroconf, "_heos-audio._tcp.local.", listener)

        await asyncio.sleep(timeout)
        with listener.lock:
            return list(listener.services)
