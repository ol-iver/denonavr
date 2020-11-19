#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the XML Commands of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
from io import BytesIO
import xml.etree.ElementTree as ET
from requests.exceptions import ConnectTimeout, RequestException

_LOGGER = logging.getLogger("AppCommand0300")

COMMAND_ENDPOINT = "/goform/AppCommand0300.xml"


class AppCommand0300:
    """AppCommand0300 Base Class."""

    def __init__(self, receiver):
        """
        Initialize Command Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """
        self.receiver = receiver
        if self._params:
            self.param_labels = {
                param: {value: key for key, value in inner.items()}
                for param, inner in self._params.items()
            }
        else:
            _LOGGER.warning("Class AppCommand0300 initialized without params.")

    def send_command(self, xml_tree):
        """Send commands."""
        body = BytesIO()
        xml_tree.write(body, encoding="utf-8", xml_declaration=True)
        try:
            result = self.receiver.send_post_command(
                command=COMMAND_ENDPOINT, body=body.getvalue()
            )
        except (ConnectTimeout, RequestException):
            _LOGGER.error(
                "No connection to %s end point on host %s",
                COMMAND_ENDPOINT,
                self.receiver.host,
            )
            return

        if result is None:
            return

        _LOGGER.debug("Command:\n%s\nResponse:\n%s", body.getvalue(), result)

        try:
            # Return XML ElementTree
            return ET.fromstring(result)

        except (ET.ParseError, TypeError):
            _LOGGER.error(
                "End point %s on host %s returned malformed XML.",
                COMMAND_ENDPOINT,
                self.receiver.host,
            )
            return

    def update(self):
        """Update settings."""
        root = ET.Element("tx")
        cmd = ET.SubElement(root, "cmd", id="3")
        ET.SubElement(cmd, "name").text = self._get_cmd_name
        param_list = ET.SubElement(cmd, "list")
        for param in self._params.keys():
            ET.SubElement(param_list, "param", name=param)
        tree = ET.ElementTree(root)

        response = self.send_command(xml_tree=tree)
        if response is None:
            return False

        try:
            audyssey_params = response.find("./cmd/list")
        except (AttributeError, IndexError, TypeError):
            return False

        for param in audyssey_params:
            name = param.get("name")
            if not name:
                continue

            map_key = self._params.get(name)
            if not map_key:
                _LOGGER.warning("Unmapped name: %s", name)
                continue

            param_text = param.text
            if not param_text:
                _LOGGER.debug(
                    "Parameter: %s has no text attribute (state). param control=%s",
                    param,
                    param.get("control"),
                )
                continue

            param_state = map_key.get(param.text)
            if not param_state:
                _LOGGER.warning("State: %s not found in map for %s", param_text, name)
                continue

            setattr(self, name, param_state)
            setattr(self, f"{name}_control", bool(int(param.get("control"))))

        return True

    def _set(self, parameter, value):
        root = ET.Element("tx")
        cmd = ET.SubElement(root, "cmd", id="3")
        ET.SubElement(cmd, "name").text = self._set_cmd_name
        param_list = ET.SubElement(cmd, "list")
        ET.SubElement(param_list, "param", name=parameter).text = str(value)
        tree = ET.ElementTree(root)

        response = self.send_command(xml_tree=tree)
        if response is None:
            return False

        if response.find("cmd").text == "OK":
            return True

        return False


class Audyssey(AppCommand0300):
    """Audyssey Commands."""

    def __init__(self, receiver):
        """
        Initialize Audyssey Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """

        self._set_cmd_name = "SetAudyssey"
        self._get_cmd_name = "GetAudyssey"
        self._params = {
            "dynamiceq": {
                "0": "Off",
                "1": "On",
            },
            "reflevoffset": {
                "0": "0dB",
                "1": "+5dB",
                "2": "+10dB",
                "3": "+15dB",
            },
            "dynamicvol": {
                "0": "Off",
                "1": "Light",
                "2": "Medium",
                "3": "Heavy",
            },
            "multeq": {
                "0": "Off",
                "1": "Flat",
                "2": "L/R Bypass",
                "3": "Reference",
            },
        }
        super().__init__(receiver)

    def dynamiceq_off(self):
        """Turn DynamicEQ off."""
        if self._set(parameter="dynamiceq", value=0) is True:
            self.dynamiceq = False

    def dynamiceq_on(self):
        """Turn DynamicEQ on."""
        if self._set(parameter="dynamiceq", value=1) is True:
            self.dynamiceq = True

    def set_multieq(self, setting):
        """Set MultiEQ mode."""
        if (
            self._set(
                parameter="multeq", value=self.param_labels["multeq"].get(setting)
            )
            is True
        ):
            self.multeq = setting

    def set_reflevoffset(self, setting):
        """Set Reference Level Offset."""
        # Reference level offset can only be used with DynamicEQ
        # TODO: Let's take advantage of the "control" attr given by API
        if self.dynamiceq is True:
            if (
                self._set(
                    parameter="reflevoffset",
                    value=self.param_labels["reflevoffset"].get(setting),
                )
                is True
            ):
                self.reflevoffset = setting

    def set_dynamicvol(self, setting):
        """Set Dynamic Volume."""
        if (
            self._set(
                parameter="dynamicvol",
                value=self.param_labels["dynamicvol"].get(setting),
            )
            is True
        ):
            self.dynamicvol = setting


class SurroundParameter(AppCommand0300):
    """SurroundParameter Commands."""

    def __init__(self, receiver):
        """
        Initialize SurroundParameter Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """

        self._set_cmd_name = "SetSurroundParameter"
        self._get_cmd_name = "GetSurroundParameter"
        self._params = {
            "dyncomp": {
                "0": "Off",
                "1": "Low",
                "2": "Medium",
                "3": "High",
            },
            "lfe": {str(gain): f"{str(gain)}dB" for gain in range(0, -11, -1)},
        }
        super().__init__(receiver)

    def set_dyncomp(self, setting):
        """Set Dolby Dynamic Compression mode."""
        if (
            self._set(
                parameter="dyncomp", value=self.param_labels["dyncomp"].get(setting)
            )
            is True
        ):
            self.dyncomp = setting

    def set_lfe(self, setting):
        """Set Dynamic Volume."""
        if (
            self._set(
                parameter="lfe",
                value=self.param_labels["lfe"].get(setting),
            )
            is True
        ):
            self.lfe = setting
