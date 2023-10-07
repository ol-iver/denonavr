#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
import re
import socket
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import httpx
import netifaces
from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError, fromstring

_LOGGER = logging.getLogger(__name__)

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 2
SSDP_TARGET = (SSDP_ADDR, SSDP_PORT)
SSDP_ST_1 = "ssdp:all"
SSDP_ST_2 = "upnp:rootdevice"
SSDP_ST_3 = "urn:schemas-upnp-org:device:MediaRenderer:1"

SSDP_ST_LIST = (SSDP_ST_1, SSDP_ST_2, SSDP_ST_3)

SSDP_LOCATION_PATTERN = re.compile(r"(?<=LOCATION:\s).+?(?=\r)")

SCPD_XMLNS = "{urn:schemas-upnp-org:device-1-0}"
SCPD_DEVICE = f"{SCPD_XMLNS}device"
SCPD_DEVICELIST = f"{SCPD_XMLNS}deviceList"
SCPD_DEVICETYPE = f"{SCPD_XMLNS}deviceType"
SCPD_MANUFACTURER = f"{SCPD_XMLNS}manufacturer"
SCPD_MODELNAME = f"{SCPD_XMLNS}modelName"
SCPD_SERIALNUMBER = f"{SCPD_XMLNS}serialNumber"
SCPD_FRIENDLYNAME = f"{SCPD_XMLNS}friendlyName"
SCPD_PRESENTATIONURL = f"{SCPD_XMLNS}presentationURL"

SUPPORTED_DEVICETYPES = [
    "urn:schemas-upnp-org:device:MediaRenderer:1",
    "urn:schemas-upnp-org:device:MediaServer:1",
]

SUPPORTED_MANUFACTURERS = ["Denon", "DENON", "DENON PROFESSIONAL", "Marantz"]


def ssdp_request(ssdp_st: str, ssdp_mx: float = SSDP_MX) -> bytes:
    """Return request bytes for given st and mx."""
    return "\r\n".join(
        [
            "M-SEARCH * HTTP/1.1",
            f"ST: {ssdp_st}",
            f"MX: {ssdp_mx:d}",
            'MAN: "ssdp:discover"',
            f"HOST: {SSDP_ADDR}:{SSDP_PORT}",
            "",
            "",
        ]
    ).encode("utf-8")


def get_local_ips() -> List[str]:
    """Get IPs of local network adapters."""
    ips = []
    # pylint: disable=c-extension-no-member
    for interface in netifaces.interfaces():
        addresses = netifaces.ifaddresses(interface)
        for address in addresses.get(netifaces.AF_INET, []):
            ips.append(address["addr"])
    return ips


async def async_identify_denonavr_receivers() -> List[Dict]:
    """
    Identify DenonAVR using SSDP and SCPD queries.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    """
    # Sending SSDP broadcast message to get resource urls from devices
    urls = await async_send_ssdp_broadcast()

    # Check which responding device is a DenonAVR device and prepare output
    receivers = []

    for url in urls:
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=5.0)
                res.raise_for_status()
        except httpx.HTTPError:
            continue
        else:
            receiver = evaluate_scpd_xml(url, res.text)
            if receiver is not None:
                receivers.append(receiver)

    return receivers


async def async_send_ssdp_broadcast() -> Set[str]:
    """
    Send SSDP broadcast messages to discover UPnP devices.

    Returns a set of SCPD XML resource urls for all discovered devices.
    """
    # Send up to three different broadcast messages
    ips = get_local_ips()
    # Prepare output of responding devices
    urls = set()

    tasks = []
    for ip_addr in ips:
        tasks.append(async_send_ssdp_broadcast_ip(ip_addr))

    results = await asyncio.gather(*tasks)

    for result in results:
        _LOGGER.debug("SSDP broadcast result received: %s", result)
        urls = urls.union(result)

    _LOGGER.debug("Following devices found: %s", urls)
    return urls


async def async_send_ssdp_broadcast_ip(ip_addr: str) -> Set[str]:
    """Send SSDP broadcast messages to a single IP."""
    # Ignore 169.254.0.0/16 addresses
    if ip_addr.startswith("169.254."):
        return set()

    # Prepare socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind((ip_addr, 0))

    # Get asyncio loop
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(DenonAVRSSDP, sock=sock)

    # Wait for the timeout period
    await asyncio.sleep(SSDP_MX)

    # Close the connection
    transport.close()

    _LOGGER.debug(
        "Got %s results after SSDP queries using ip %s", len(protocol.urls), ip_addr
    )

    return protocol.urls


def evaluate_scpd_xml(url: str, body: str) -> Optional[Dict]:
    """
    Evaluate SCPD XML.

    Returns dictionary with keys "host", "modelName", "friendlyName" and
    "presentationURL" if a Denon AVR device was found and "None" if not.
    """
    try:
        root = fromstring(body)
        # Look for manufacturer "Denon" in response.
        # Using "try" in case tags are not available in XML
        device = {}
        device_xml = None
        device["manufacturer"] = root.find(SCPD_DEVICE).find(SCPD_MANUFACTURER).text

        _LOGGER.debug("Device %s has manufacturer %s", url, device["manufacturer"])

        if not device["manufacturer"] in SUPPORTED_MANUFACTURERS:
            return None

        if root.find(SCPD_DEVICE).find(SCPD_DEVICETYPE).text in SUPPORTED_DEVICETYPES:
            device_xml = root.find(SCPD_DEVICE)
        elif root.find(SCPD_DEVICE).find(SCPD_DEVICELIST) is not None:
            for dev in root.find(SCPD_DEVICE).find(SCPD_DEVICELIST):
                if (
                    dev.find(SCPD_DEVICETYPE).text in SUPPORTED_DEVICETYPES
                    and dev.find(SCPD_SERIALNUMBER) is not None
                ):
                    device_xml = dev
                    break

        if device_xml is None:
            return None

        if device_xml.find(SCPD_PRESENTATIONURL) is not None:
            device["host"] = urlparse(
                device_xml.find(SCPD_PRESENTATIONURL).text
            ).hostname
            device["presentationURL"] = device_xml.find(SCPD_PRESENTATIONURL).text
        else:
            device["host"] = urlparse(url).hostname

        device["modelName"] = device_xml.find(SCPD_MODELNAME).text
        device["serialNumber"] = device_xml.find(SCPD_SERIALNUMBER).text
        device["friendlyName"] = device_xml.find(SCPD_FRIENDLYNAME).text
        return device
    except (
        AttributeError,
        ValueError,
        ET.ParseError,
        DefusedXmlException,
        ParseError,
        UnicodeDecodeError,
    ) as err:
        _LOGGER.error(
            "Error occurred during evaluation of SCPD XML from URI %s: %s", url, err
        )
        return None


class DenonAVRSSDP(asyncio.DatagramProtocol):
    """Implements datagram protocol for SSDP discovery of Denon AVR devices."""

    def __init__(self) -> None:
        """Create instance."""
        self.urls = set()

    def connection_made(self, transport: asyncio.DatagramTransport) -> None:
        """Send SSDP request when connection was made."""
        # Prepare SSDP and send broadcast message
        for ssdp_st in SSDP_ST_LIST:
            request = ssdp_request(ssdp_st)
            transport.sendto(request, SSDP_TARGET)
            _LOGGER.debug("SSDP request sent %s", request)

    def datagram_received(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Receive responses to SSDP call."""
        # Some string operations to get the receivers URL
        # which could be found between LOCATION and end of line of the response
        _LOGGER.debug("Response to SSDP call received: %s", data)
        data_text = data.decode("utf-8")
        match = SSDP_LOCATION_PATTERN.search(data_text)
        if match:
            self.urls.add(match.group(0))
