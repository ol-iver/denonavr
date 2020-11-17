"""Audyssey Settings."""
import logging
from io import BytesIO
import xml.etree.ElementTree as ET
from requests.exceptions import ConnectTimeout, RequestException

_LOGGER = logging.getLogger("Audyssey")

MULTI_EQ_MAP = {"0": "Off", "1": "Flat", "2": "L/R Bypass", "3": "Reference"}
MULTI_EQ_MAP_LABELS = dict((value, key) for key, value in MULTI_EQ_MAP.items())

REF_LVL_OFFSET_MAP = {"0": "0dB", "1": "+5dB", "2": "+10dB", "3": "+15dB"}
REF_LVL_OFFSET_MAP_LABELS = dict(
    (value, key) for key, value in REF_LVL_OFFSET_MAP.items()
)

DYNAMIC_VOLUME_MAP = {"0": "Off", "1": "Light", "2": "Medium", "3": "Heavy"}
DYNAMIC_VOLUME_MAP_LABELS = dict(
    (value, key) for key, value in DYNAMIC_VOLUME_MAP.items()
)

COMMAND_ENDPOINT = "/goform/AppCommand0300.xml"


class Audyssey:
    """Audyssey Settings."""

    def __init__(self, receiver):
        """
        Initialize Audyssey Settings of DenonAVR.

        :param receiver: DenonAVR Receiver
        :type receiver: DenonAVR
        """
        self.receiver = receiver

        self.dynamiceq = None
        self.dynamiceq_control = None
        self.reflevoffset = None
        self.reflevoffset_control = None
        self.dynamicvol = None
        self.dynamicvol_control = None
        self.multeq = None
        self.multeq_control = None

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
        ET.SubElement(cmd, "name").text = "GetAudyssey"
        param_list = ET.SubElement(cmd, "list")
        for param in ["dynamiceq", "reflevoffset", "dynamicvol", "multeq"]:
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
            if param.get("name") == "multeq":
                self.multeq = MULTI_EQ_MAP.get(param.text)
            elif param.get("name") == "dynamiceq":
                self.dynamiceq = bool(int(param.text))
            elif param.get("name") == "reflevoffset":
                # Reference level offset can only be used with DynamicEQ
                if self.dynamiceq is False:
                    self.reflevoffset = False
                else:
                    self.reflevoffset = REF_LVL_OFFSET_MAP.get(param.text)
            elif param.get("name") == "dynamicvol":
                self.dynamicvol = DYNAMIC_VOLUME_MAP.get(param.text)
            setattr(
                self,
                "{name}_control".format(name=param.get("name")),
                bool(int(param.get("control"))),
            )
        return True

    def _set_audyssey(self, parameter, value):
        root = ET.Element("tx")
        cmd = ET.SubElement(root, "cmd", id="3")
        ET.SubElement(cmd, "name").text = "SetAudyssey"
        param_list = ET.SubElement(cmd, "list")
        ET.SubElement(param_list, "param", name=parameter).text = str(value)
        tree = ET.ElementTree(root)

        response = self.send_command(xml_tree=tree)
        if response is None:
            return False

        if response.find("cmd").text == "OK":
            return True

        return False

    def dynamiceq_off(self):
        """Turn DynamicEQ off."""
        if self._set_audyssey(parameter="dynamiceq", value=0) is True:
            self.dynamiceq = False

    def dynamiceq_on(self):
        """Turn DynamicEQ on."""
        if self._set_audyssey(parameter="dynamiceq", value=1) is True:
            self.dynamiceq = True

    def set_mutlieq(self, setting):
        """Set MultiEQ mode."""
        if (
            self._set_audyssey(
                parameter="multeq", value=MULTI_EQ_MAP_LABELS.get(setting)
            )
            is True
        ):
            self.multeq = setting

    def set_reflevoffset(self, setting):
        """Set Reference Level Offset."""
        # Reference level offset can only be used with DynamicEQ
        if self.dynamiceq is True:
            if (
                self._set_audyssey(
                    parameter="reflevoffset",
                    value=REF_LVL_OFFSET_MAP_LABELS.get(setting),
                )
                is True
            ):
                self.reflevoffset = setting

    def set_dynamicvol(self, setting):
        """Set Dynamic Volume."""
        if (
            self._set_audyssey(
                parameter="dynamicvol",
                value=DYNAMIC_VOLUME_MAP_LABELS.get(setting),
            )
            is True
        ):
            self.dynamicvol = setting
