#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements a discovery function for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
# pylint: disable=no-else-return

import logging
import socket
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import requests

_LOGGER = logging.getLogger('DenonSSDP')

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900
SSDP_MX = 2
SSDP_TARGET = (SSDP_ADDR, SSDP_PORT)
SSDP_ST_1 = "ssdp:all"
SSDP_ST_2 = "upnp:rootdevice"
SSDP_ST_3 = "urn:schemas-upnp-org:device:MediaRenderer:1"

SSDP_ST_LIST = (SSDP_ST_1, SSDP_ST_2, SSDP_ST_3)

SCPD_XMLNS = "{urn:schemas-upnp-org:device-1-0}"
SCPD_DEVICE = "{xmlns}device".format(xmlns=SCPD_XMLNS)
SCPD_DEVICETYPE = "{xmlns}deviceType".format(xmlns=SCPD_XMLNS)
SCPD_MANUFACTURER = "{xmlns}manufacturer".format(xmlns=SCPD_XMLNS)
SCPD_MODELNAME = "{xmlns}modelName".format(xmlns=SCPD_XMLNS)
SCPD_SERIALNUMBER = "{xmlns}serialNumber".format(xmlns=SCPD_XMLNS)
SCPD_FRIENDLYNAME = "{xmlns}friendlyName".format(xmlns=SCPD_XMLNS)
SCPD_PRESENTATIONURL = "{xmlns}presentationURL".format(xmlns=SCPD_XMLNS)

DEVICETYPE_DENON = "urn:schemas-upnp-org:device:MediaRenderer:1"

SUPPORTED_MANUFACTURERS = ["Denon", "DENON", "Marantz"]

def ssdp_request(ssdp_st, ssdp_mx=SSDP_MX):
    """Return request bytes for given st and mx."""
    return "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'ST: {}'.format(ssdp_st),
        'MX: {:d}'.format(ssdp_mx),
        'MAN: "ssdp:discover"',
        'HOST: {}:{}'.format(*SSDP_TARGET),
        '', '']).encode('utf-8')

def get_local_ip(sock):
    ip_list = socket.gethostbyname_ex(socket.gethostname())[2]
    for ip in ip_list:
        if ip.startswith("192."):
            return ip

def identify_denonavr_receivers():
    """
    Identify DenonAVR using SSDP and SCPD queries.

    Returns a list of dictionaries which includes all discovered Denon AVR
    devices with keys "host", "modelName", "friendlyName", "presentationURL".
    """
    # Sending SSDP broadcast message to get devices
    devices = send_ssdp_broadcast()

    # Check which responding device is a DenonAVR device and prepare output
    receivers = []
    for device in devices:
        try:
            receiver = evaluate_scpd_xml(device["URL"])
        except ConnectionError:
            continue
        if receiver:
            receivers.append(receiver)

    return receivers


def send_ssdp_broadcast():
    """
    Send SSDP broadcast message to discover UPnP devices.

    Returns a list of dictionaries with "address" (IP, PORT) and "URL"
    of SCPD XML for all discovered devices.
    """
    # Send up to three different broadcast messages
    for i, ssdp_st in enumerate(SSDP_ST_LIST):
        # Prepare SSDP broadcast message
        sock = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.settimeout(SSDP_MX)
        sock.bind((get_local_ip(sock), 0))
        sock.sendto(ssdp_request(ssdp_st), (SSDP_ADDR, SSDP_PORT))

        # Collect all responses within the timeout period
        res = []
        try:
            while True:
                res.append(sock.recvfrom(10240))
        except socket.timeout:
            sock.close()

        if res:
            _LOGGER.debug("Got results after %s SSDP queries", i + 1)
            sock.close()
            break

    # Prepare output of responding devices
    devices = {}
    device = {}

    for entry in res:
        device["address"] = entry[1]
        # Some string operations to get the receivers URL
        # which could be found between LOCATION and end of line of the response
        en_decoded = entry[0].decode("utf-8")
        # If location is not found, skip the entry
        try:
            device["URL"] = (
                en_decoded[
                    en_decoded.lower().index(
                        "location:") + 10:en_decoded.index(
                            "\r\n", en_decoded.lower().index("location:"))]
            )
        except ValueError:
            continue
        devices[device["address"]] = device.copy()

    _LOGGER.debug("Following devices found: %s", list(devices.values()))
    return list(devices.values())


def evaluate_scpd_xml(url):
    """
    Get and evaluate SCPD XML to identified URLs.

    Returns dictionary with keys "host", "modelName", "friendlyName" and
    "presentationURL" if a Denon AVR device was found and "False" if not.
    """
    # Get SCPD XML via HTTP GET
    try:
        res = requests.get(url, timeout=2)
    except requests.exceptions.RequestException as err:
        _LOGGER.error(
            "When trying to request %s the following error occurred: %s",
            url, err)
        raise ConnectionError

    if res.status_code == 200:
        try:
            root = ET.fromstring(res.text)
            # Look for manufacturer "Denon" in response.
            # Using "try" in case tags are not available in XML
            device = {}
            device["manufacturer"] = (
                root.find(SCPD_DEVICE).find(SCPD_MANUFACTURER).text)
            
            _LOGGER.debug("Device %s has manufacturer %s", url,
                          device["manufacturer"])
            if (device["manufacturer"] in SUPPORTED_MANUFACTURERS and
                    root.find(SCPD_DEVICE).find(
                        SCPD_DEVICETYPE).text == DEVICETYPE_DENON):
                device["host"] = urlparse(
                    root.find(SCPD_DEVICE).find(
                        SCPD_PRESENTATIONURL).text).hostname
                device["presentationURL"] = (
                    root.find(SCPD_DEVICE).find(SCPD_PRESENTATIONURL).text)
                device["modelName"] = (
                    root.find(SCPD_DEVICE).find(SCPD_MODELNAME).text)
                device["serialNumber"] = (
                    root.find(SCPD_DEVICE).find(SCPD_SERIALNUMBER).text)
                device["friendlyName"] = (
                    root.find(SCPD_DEVICE).find(SCPD_FRIENDLYNAME).text)
                return device
            else:
                return False
        except (AttributeError, ValueError, ET.ParseError) as err:
            _LOGGER.error(
                "Error occurred during evaluation of SCPD XML: %s", err)
            return False
    else:
        _LOGGER.error("Host returned HTTP status %s when connecting to %s",
                      res.status_code, url)
        raise ConnectionError
