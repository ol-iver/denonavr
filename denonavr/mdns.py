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

import httpx
from httpx import AsyncClient
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

from .const import DESCRIPTION_TYPES, DescriptionType
from .ssdp import async_is_av_receiver, evaluate_scpd_xml

_LOGGER = logging.getLogger(__name__)


@dataclass
class ServiceInfoRecord:
    """Record for a discovered mDNS service."""

    name: str
    type: str
    info: ServiceInfo | None


@dataclass
class FoundReceiver:
    """Representation of a found Denon/Marantz receiver."""

    name: str
    ip_address: str
    model: str
    network_id: str
    did: str
    serial_number: str | None


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


async def async_query_receivers(timeout: float = 2.5) -> list[FoundReceiver] | None:
    """
    Query for Denon/Marantz receivers using mDNS.

    Args:
        timeout: Number of seconds to wait for mDNS responses before
            collecting and returning the discovered services. During this
            period the service browser listens for receiver announcements.
    """
    async with AsyncZeroconf() as zeroconf:
        listener = MDNSListener()
        ServiceBrowser(zeroconf.zeroconf, "_heos-audio._tcp.local.", listener)

        await asyncio.sleep(timeout)
        with listener.lock:
            if not listener.services:
                return None

            async with httpx.AsyncClient() as client:
                services: list[FoundReceiver] = []
                for service in listener.services:
                    if not service.info or service.info.decoded_properties is None:
                        continue

                    ip_addresses = service.info.parsed_addresses(
                        version=IPVersion.V4Only
                    )
                    if not ip_addresses:
                        ip_addresses = service.info.parsed_addresses(
                            version=IPVersion.V6Only
                        )
                    if not ip_addresses:
                        _LOGGER.info(
                            "No IP address found for service %s (%s)",
                            service.name,
                            service.type,
                        )
                        continue
                    ip = ip_addresses[0]
                    if not await async_is_av_receiver(ip, client, timeout):
                        continue
                    serial_number = await _async_get_serial_number(ip, client, timeout)

                    services.append(
                        FoundReceiver(
                            name=service.name,
                            ip_address=ip,
                            model=service.info.decoded_properties.get(
                                "model", "Unknown"
                            ),
                            network_id=service.info.decoded_properties.get(
                                "networkid", "Unknown"
                            ),
                            did=service.info.decoded_properties.get("did", "Unknown"),
                            serial_number=serial_number,
                        )
                    )
                return services or None


async def _async_get_serial_number(
    ip: str, client: AsyncClient, timeout: float
) -> str | None:
    async def _async_get_serial_number_inner(
        description: DescriptionType,
    ) -> str | None:
        url = f"http://{ip}:{description.port}{description.url}"
        try:
            async with client.stream("GET", url, timeout=timeout) as res:
                if res.status_code != 200:
                    return None
                await res.aread()

                device_info = evaluate_scpd_xml(url, res.text)
                if device_info is None or "serialNumber" not in device_info:
                    return None
                return device_info["serialNumber"]
        except Exception:  # pylint: disable=broad-exception-caught
            return None

    # Try all description types and return the first serial number found
    for desc in DESCRIPTION_TYPES.values():
        serial = await _async_get_serial_number_inner(desc)
        if serial:
            return serial
    return None
