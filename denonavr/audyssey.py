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
from denonavr.commands import (
    COMMAND_ENDPOINT,
    AUDYSSEY_GET_CMD,
    AUDYSSEY_PARAMS,
    AUDYSSEY_SET_CMD,
    SURROUND_PARAMETER_GET_CMD,
    SURROUND_PARAMETER_PARAMS,
    SURROUND_PARAMETER_SET_CMD,
)

_LOGGER = logging.getLogger("AppCommand0300")


class AppCommand0300:
    """AppCommand0300 Base Class."""

    def __init__(self, receiver):
        """
        Initialize Command Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """
        self.receiver = receiver
        self._set_cmd = None
        self._get_cmd = None
        self._params = None
        self._param_labels = None

    def _init_commands(self, set_cmd, get_cmd, params):
        """Initialize the commands."""
        self._set_cmd = set_cmd
        self._get_cmd = get_cmd
        self._params = params
        self._param_labels = {
            param: {value: key for key, value in inner.items()}
            for param, inner in self._params.items()
        }

    def list_parameter_options(self, param):
        """List the valid options for param."""
        labels = self._param_labels.get(param)
        if labels is None:
            _LOGGER.warning("Parameter: %s not found.", param)
            return []
        return list(labels.keys())

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
        ET.SubElement(cmd, "name").text = self._get_cmd
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
        ET.SubElement(cmd, "name").text = self._set_cmd
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

        super().__init__(receiver)
        self._init_commands(
            set_cmd=AUDYSSEY_SET_CMD, get_cmd=AUDYSSEY_GET_CMD, params=AUDYSSEY_PARAMS
        )
        self.dynamiceq = None
        self.multeq = None
        self.reflevoffset = None
        self.dynamicvol = None

    def dynamiceq_off(self):
        """Turn DynamicEQ off."""
        success = self._set(parameter="dynamiceq", value=0)
        if success:
            self.dynamiceq = False

    def dynamiceq_on(self):
        """Turn DynamicEQ on."""
        success = self._set(parameter="dynamiceq", value=1)
        if success:
            self.dynamiceq = True

    def set_multieq(self, setting):
        """Set MultiEQ mode."""
        value = self._param_labels["multeq"].get(setting)
        success = self._set(parameter="multeq", value=value)
        if success:
            self.multeq = setting

    def set_reflevoffset(self, setting):
        """Set Reference Level Offset."""
        # Reference level offset can only be used with DynamicEQ
        if self.dynamiceq is False:
            return
        value = self._param_labels["reflevoffset"].get(setting)
        success = self._set(parameter="reflevoffset", value=value)
        if success:
            self.reflevoffset = setting

    def set_dynamicvol(self, setting):
        """Set Dynamic Volume."""
        value = self._param_labels["dynamicvol"].get(setting)
        success = self._set(parameter="dynamicvol", value=value)
        if success:
            self.dynamicvol = setting


class SurroundParameter(AppCommand0300):
    """SurroundParameter Commands."""

    def __init__(self, receiver):
        """
        Initialize SurroundParameter Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """
        super().__init__(receiver)
        self._init_commands(
            set_cmd=SURROUND_PARAMETER_SET_CMD,
            get_cmd=SURROUND_PARAMETER_GET_CMD,
            params=SURROUND_PARAMETER_PARAMS,
        )
        self.dyncomp = None
        self.lfe = None

    def set_dyncomp(self, setting):
        """Set Dolby Dynamic Compression mode."""
        value = self._param_labels["dyncomp"].get(setting)
        success = self._set(parameter="dyncomp", value=value)
        if success:
            self.dyncomp = setting

    def set_lfe(self, setting):
        """Set Dynamic Volume."""
        value = self._param_labels["lfe"].get(setting)
        success = self._set(parameter="lfe", value=value)
        if success:
            self.lfe = setting
