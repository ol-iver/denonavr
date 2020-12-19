#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
import socket
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
import requests
import netifaces

_LOGGER = logging.getLogger('DenonSSDP')

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 2
SSDP_TARGET = (SSDP_ADDR, SSDP_PORT)
SSDP_ST_1 = "ssdp:all"
SSDP_ST_2 = "upnp:rootdevice"
SSDP_ST_3 = "urn:schemas-upnp-org:device:MediaRenderer:1"

SSDP_ST_LIST = (SSDP_ST_1, SSDP_ST_2, SSDP_ST_3)

SSDP_LOCATION_PATTERN = re.compile(r'(?<=LOCATION:\s).+?(?=\r)')

SCPD_XMLNS = "{urn:schemas-upnp-org:device-1-0}"
SCPD_DEVICE = "{xmlns}device".format(xmlns=SCPD_XMLNS)
SCPD_DEVICELIST = "{xmlns}deviceList".format(xmlns=SCPD_XMLNS)
SCPD_DEVICETYPE = "{xmlns}deviceType".format(xmlns=SCPD_XMLNS)
SCPD_MANUFACTURER = "{xmlns}manufacturer".format(xmlns=SCPD_XMLNS)
SCPD_MODELNAME = "{xmlns}modelName".format(xmlns=SCPD_XMLNS)
SCPD_SERIALNUMBER = "{xmlns}serialNumber".format(xmlns=SCPD_XMLNS)
SCPD_FRIENDLYNAME = "{xmlns}friendlyName".format(xmlns=SCPD_XMLNS)
SCPD_PRESENTATIONURL = "{xmlns}presentationURL".format(xmlns=SCPD_XMLNS)

SUPPORTED_DEVICETYPES = [
    "urn:schemas-upnp-org:device:MediaRenderer:1",
    "urn:schemas-upnp-org:device:MediaServer:1",
    ]

SUPPORTED_MANUFACTURERS = ["Denon", "DENON", "DENON PROFESSIONAL", "Marantz"]


def ssdp_request(ssdp_st, ssdp_mx=SSDP_MX):
    """Return request bytes for given st and mx."""
    return "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'ST: {}'.format(ssdp_st),
        'MX: {:d}'.format(ssdp_mx),
        'MAN: "ssdp:discover"',
        'HOST: {}:{}'.format(*SSDP_TARGET),
        '', '']).encode('utf-8')


def get_local_ips():
    """Get IPs of local network adapters."""
    ips = []
    # pylint: disable=c-extension-no-member
    for interface in netifaces.interfaces():
        addresses = netifaces.ifaddresses(interface)
        for address in addresses.get(netifaces.AF_INET, []):
            ips.append(address["addr"])
    return ips


def identify_denonavr_receivers():
    """
    Identify DenonAVR using SSDP and SCPD queries.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    """
    # Sending SSDP broadcast message to get resource urls from devices
    urls = send_ssdp_broadcast()

    # Check which responding device is a DenonAVR device and prepare output
    receivers = []

    for url in urls:
        try:
            receiver = evaluate_scpd_xml(url)
        except requests.exceptions.RequestException:
            continue
        if receiver is not None:
            receivers.append(receiver)

    return receivers


def send_ssdp_broadcast():
    """
    Send SSDP broadcast messages to discover UPnP devices.

    Returns a set of SCPD XML resource urls for all discovered devices.
    """
    # Send up to three different broadcast messages
    ips = get_local_ips()
    res = []

    futures = []
    with ThreadPoolExecutor() as executor:
        for ip_addr in ips:
            futures.append(executor.submit(send_ssdp_broadcast_ip, ip_addr))

        for future in futures:
            res.extend(future.result())

    # Prepare output of responding devices
    urls = set()

    for entry in res:
        # Some string operations to get the receivers URL
        # which could be found between LOCATION and end of line of the response
        entry_text = entry[0].decode("utf-8")
        match = SSDP_LOCATION_PATTERN.search(entry_text)
        if match:
            urls.add(match.group(0))

    _LOGGER.debug("Following devices found: %s", urls)
    return urls


def send_ssdp_broadcast_ip(ip_addr):
    """Send SSDP broadcast messages to a single IP."""
    res = []
    # Ignore 169.254.0.0/16 adresses
    if re.search("169.254.*.*", ip_addr):
        return res
    # Prepare SSDP broadcast message
    sock = socket.socket(
        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.settimeout(SSDP_MX)
    sock.bind((ip_addr, 0))
    for ssdp_st in SSDP_ST_LIST:
        sock.sendto(ssdp_request(ssdp_st), (SSDP_ADDR, SSDP_PORT))

    # Collect all responses within the timeout period
    try:
        while True:
            res.append(sock.recvfrom(10240))
    except socket.timeout:
        pass
    finally:
        sock.close()

    if res:
        _LOGGER.debug(
            "Got %s results after SSDP queries using ip %s", len(res), ip_addr)

    return res


def evaluate_scpd_xml(url):
    """
    Get and evaluate SCPD XML to identified URLs.

    Returns dictionary with keys "host", "modelName", "friendlyName" and
    "presentationURL" if a Denon AVR device was found and "False" if not.
    """
    # Get SCPD XML via HTTP GET
    try:
        res = requests.get(url, timeout=2)
    except requests.exceptions.ConnectTimeout:
        raise
    except requests.exceptions.RequestException as err:
        _LOGGER.error(
            "During DenonAVR device identification, when trying to request %s "
            "the following error occurred: %s", url, err)
        raise

    if res.status_code == 200:
        try:
            root = ET.fromstring(res.text)
            # Look for manufacturer "Denon" in response.
            # Using "try" in case tags are not available in XML
            device = {}
            device_xml = None
            device["manufacturer"] = (
                root.find(SCPD_DEVICE).find(SCPD_MANUFACTURER).text)

            _LOGGER.debug("Device %s has manufacturer %s", url,
                          device["manufacturer"])

            if not device["manufacturer"] in SUPPORTED_MANUFACTURERS:
                return None

            if (root.find(SCPD_DEVICE).find(SCPD_DEVICETYPE).text
                    in SUPPORTED_DEVICETYPES):
                device_xml = root.find(SCPD_DEVICE)
            elif root.find(SCPD_DEVICE).find(SCPD_DEVICELIST) is not None:
                for dev in root.find(SCPD_DEVICE).find(SCPD_DEVICELIST):
                    if (dev.find(SCPD_DEVICETYPE).text in SUPPORTED_DEVICETYPES
                            and dev.find(SCPD_SERIALNUMBER) is not None):
                        device_xml = dev
                        break

            if device_xml is None:
                return None

            if device_xml.find(SCPD_PRESENTATIONURL) is not None:
                device["host"] = urlparse(
                    device_xml.find(
                        SCPD_PRESENTATIONURL).text).hostname
                device["presentationURL"] = (
                    device_xml.find(SCPD_PRESENTATIONURL).text)
            else:
                device["host"] = urlparse(url).hostname
            device["modelName"] = (
                device_xml.find(SCPD_MODELNAME).text)
            device["serialNumber"] = (
                device_xml.find(SCPD_SERIALNUMBER).text)
            device["friendlyName"] = (
                device_xml.find(SCPD_FRIENDLYNAME).text)
            return device
        except (AttributeError, ValueError, ET.ParseError) as err:
            _LOGGER.error(
                "Error occurred during evaluation of SCPD XML: %s", err)
            return None
    else:
        _LOGGER.debug("Host returned HTTP status %s when connecting to %s",
                      res.status_code, url)
        return None
