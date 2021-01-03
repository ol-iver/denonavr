#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from urllib.parse import urlparse
import unittest
import requests
import requests_mock
import denonavr

FAKE_IP = "10.0.0.0"

NO_ZONES = None
ZONE2 = {"Zone2": None}
ZONE3 = {"Zone3": None}
ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}

TESTING_RECEIVERS = {
    "AVR-X4100W": (NO_ZONES, denonavr.denonavr.AVR_X),
    "AVR-2312CI": (NO_ZONES, denonavr.denonavr.AVR),
    "AVR-1912": (NO_ZONES, denonavr.denonavr.AVR),
    "AVR-3311CI": (NO_ZONES, denonavr.denonavr.AVR),
    "M-RC610": (NO_ZONES, denonavr.denonavr.AVR_X),
    "AVR-X2100W-2": (NO_ZONES, denonavr.denonavr.AVR_X),
    "AVR-X2000": (ZONE2_ZONE3, denonavr.denonavr.AVR_X),
    "AVR-X2000-2": (NO_ZONES, denonavr.denonavr.AVR_X),
    "SR5008": (NO_ZONES, denonavr.denonavr.AVR_X),
    "M-CR603": (NO_ZONES, denonavr.denonavr.AVR),
    "NR1604": (ZONE2_ZONE3, denonavr.denonavr.AVR_X),
    "AVR-4810": (NO_ZONES, denonavr.denonavr.AVR),
    "AVR-3312": (NO_ZONES, denonavr.denonavr.AVR),
    "NR1609": (ZONE2, denonavr.denonavr.AVR_X_2016),
    "AVC-8500H": (ZONE2_ZONE3, denonavr.denonavr.AVR_X_2016),
    "AVR-X4300H": (ZONE2_ZONE3, denonavr.denonavr.AVR_X_2016),
    "AVR-X1100W": (ZONE2, denonavr.denonavr.AVR_X)
    }

APPCOMMAND_URL = "/goform/AppCommand.xml"
STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
STATUS_Z2_URL = "/goform/formZone2_Zone2XmlStatus.xml"
STATUS_Z3_URL = "/goform/formZone3_Zone3XmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"


def get_sample_content(filename):
    """Return sample content form file."""
    with open("tests/xml/{filename}".format(filename=filename),
              encoding="utf-8") as file:
        return file.read()


class TestMainFunctions(unittest.TestCase):
    """Test case for main functions of Denon AVR."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._testing_receiver = None

    @requests_mock.mock()
    # pylint: disable=arguments-differ
    def setUp(self, mocker):
        """Initialize test functions, using the first receiver from list."""
        super().setUp()
        self.denon = None

    def custom_matcher(self, request):
        """Match URLs to sample files."""
        port_suffix = ""

        if urlparse(request.url).port == 8080:
            port_suffix = "-8080"

        resp = requests.Response()
        resp.encoding = "utf-8"

        try:
            if request.path_url == STATUS_URL:
                content = get_sample_content(
                    "{receiver}-formMainZone_MainZoneXmlStatus{port}"
                    ".xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == STATUS_Z2_URL:
                content = get_sample_content(
                    "{receiver}-formZone2_Zone2XmlStatus{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == STATUS_Z3_URL:
                content = get_sample_content(
                    "{receiver}-formZone3_Zone3XmlStatus{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == MAINZONE_URL:
                content = get_sample_content(
                    "{receiver}-formMainZone_MainZoneXml{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == DEVICEINFO_URL:
                content = get_sample_content(
                    "{receiver}-Deviceinfo{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == NETAUDIOSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formNetAudio_StatusXml{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == TUNERSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formTuner_TunerXml{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == HDTUNERSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formTuner_HdXml{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            elif request.path_url == APPCOMMAND_URL:
                content = get_sample_content(
                    "{receiver}-AppCommand{port}.xml".format(
                        receiver=self._testing_receiver, port=port_suffix))
            else:
                content = "DATA"
        except FileNotFoundError:
            resp = requests.Response()
            content = "Error 403: Forbidden\nAccess Forbidden"
            resp.status_code = 403
        else:
            resp.status_code = 200

        resp._content = content.encode()  # pylint: disable=protected-access

        return resp

    @requests_mock.mock()
    def test_receiver_type(self, mock):
        """Check that receiver type is determined correctly."""
        mock.add_matcher(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            self.assertEqual(
                self.denon.receiver_type,
                spec[1].type,
                "Receiver type is {} not {} for receiver {}".format(
                    self.denon.receiver_type, spec[1].type, receiver))
            self.assertEqual(
                self.denon.receiver_port,
                spec[1].port,
                "Receiver port is {} not {} for receiver {}".format(
                    self.denon.receiver_port, spec[1].port, receiver))

    @requests_mock.mock()
    def test_input_func_switch(self, mock):
        """Switch through all input functions of all tested receivers."""
        mock.add_matcher(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            # Switch through all functions and check if successful
            for name, zone in self.denon.zones.items():
                print("Receiver: {}, Zone: {}".format(receiver, name))
                self.assertGreater(len(zone.input_func_list), 0)
                for input_func in zone.input_func_list:
                    self.denon.zones[name].set_input_func(input_func)
                    self.assertEqual(
                        input_func, self.denon.zones[name].input_func,
                        ("Input function change to {func} "
                         "not successful for {receiver}").format(
                             func=input_func, receiver=receiver))

    @requests_mock.mock()
    def test_attributes_not_none(self, mock):
        """Check that certain attributes are not None."""
        mock.add_matcher(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            self.assertIsNotNone(
                self.denon.power,
                "Power status is None for receiver {}".format(receiver))
            self.assertIsNotNone(
                self.denon.state,
                "State is None for receiver {}".format(receiver))
