#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
import socket
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests

_LOGGER = logging.getLogger('DenonSSDP')

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_ST = "ssdp:all"

SSDP_QUERY = (
    "M-SEARCH * HTTP/1.1\r\n" +
    "HOST: {addr}:{port}\r\n".format(addr=SSDP_ADDR, port=SSDP_PORT) +
    "MAN: \"ssdp:discover\"\r\n" +
    "MX: 2\r\n" +
    "ST: {st}\r\n".format(st=SSDP_ST) + "\r\n"
)

SCPD_XMLNS = "{urn:schemas-upnp-org:device-1-0}"
SCPD_DEVICE = "{xmlns}device".format(xmlns=SCPD_XMLNS)
SCPD_DEVICETYPE = "{xmlns}deviceType".format(xmlns=SCPD_XMLNS)
SCPD_MANUFACTURER = "{xmlns}manufacturer".format(xmlns=SCPD_XMLNS)
SCPD_MODELNAME = "{xmlns}modelName".format(xmlns=SCPD_XMLNS)
SCPD_PRESENTATIONURL = "{xmlns}presentationURL".format(xmlns=SCPD_XMLNS)

DEVICETYPE_DENON = "urn:schemas-upnp-org:device:MediaRenderer:1"


def identify_denonavr_receivers(attempts):
    """
    Identify DenonAVR using SSDP and SCPD queries.

    Returns a list of dictionaries which includes all discovered DenonAVR
    devices with keys "host", "ModelName" and "PresentationURL".
    Returns "None" if no DenonAVR receiver was found.
    """
    # Sending SSDP broadcast message to get devices
    devices = send_ssdp_broadcast(attempts)

    # Check which responding device is a DenonAVR device and prepare output
    receivers = []
    for device in devices:
        try:
            receiver = evaluate_scpd_xml(device["URL"])
        except ConnectionError:
            continue
        if receiver:
            receivers.append(receiver)

    if receivers:
        return receivers
    else:
        return None


def send_ssdp_broadcast(attempts):
    """
    Send SSDP broadcast message to discover UPnP devices.

    Returns a list of dictionaries with "address" (IP, PORT) and "URL"
    of SCPD XML for all discovered devices.
    """
    # Prepare SSDP broadcast message
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(2)
    sock.sendto(SSDP_QUERY.encode(), (SSDP_ADDR, SSDP_PORT))

    # Collect all responses within the timeout period
    res = []
    # Repeat up to 3 times if there is no response
    for i in range(attempts):
        try:
            while True:
                res.append(sock.recvfrom(10240))
        except socket.timeout:
            pass

        if res:
            _LOGGER.debug("Results after %s SSDP queries", i + 1)
            break

    # Prepare output of responding devices
    devices = {}
    device = {}

    for entry in res:
        device["address"] = entry[1]
        # Some string operations to get the receivers URL
        # which could be found between LOCATION and end of line of the response
        en_decoded = entry[0].decode("utf-8")
        device["URL"] = (
            en_decoded[
                en_decoded.lower().find("location:") + 10:en_decoded.find(
                    "\r\n", en_decoded.lower().find("location:"))]
        )
        devices[device["address"]] = device.copy()

    _LOGGER.debug("Following devices found: %s", list(devices.values()))
    return list(devices.values())


def evaluate_scpd_xml(url):
    """
    Get and evaluate SCPD XML to identified URLs.

    Returns dictionary with keys "host", "ModelName" and "PresentationURL"
    if a Denon device was found and "False" if not.
    """
    # Get SCPD XML via HTTP GET
    try:
        res = requests.get(url, timeout=2)
    except requests.exceptions.ConnectTimeout:
        raise ConnectionError
    except requests.exceptions.ConnectionError:
        raise ConnectionError

    if res.status_code == 200:
        root = ET.fromstring(res.text)
        # Look for manufacturer "Denon" in response.
        # Using "try" in case tags are not available in XML
        try:
            _LOGGER.debug("Device %s has manufacturer %s", url,
                          root.find(SCPD_DEVICE).find(SCPD_MANUFACTURER).text)
            if (root.find(SCPD_DEVICE).find(
                    SCPD_MANUFACTURER).text == "Denon" and root.find(
                        SCPD_DEVICE).find(
                            SCPD_DEVICETYPE).text == DEVICETYPE_DENON):
                device = {}
                device["host"] = urlparse(
                    root.find(SCPD_DEVICE).find(
                        SCPD_PRESENTATIONURL).text).hostname
                device["PresentationURL"] = (
                    root.find(SCPD_DEVICE).find(SCPD_PRESENTATIONURL).text)
                device["ModelName"] = (
                    root.find(SCPD_DEVICE).find(SCPD_MODELNAME).text)
                return device
            else:
                return False
        except AttributeError:
            return False
    else:
        raise ConnectionError
