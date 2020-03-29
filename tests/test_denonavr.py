#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import sys
from io import open

try:
    from urllib.parse import urlparse
except ImportError:  # Python 2 support
    from urlparse import urlparse
import testtools
import requests
import requests_mock
import denonavr

# Python 2 support: Define FileNotFoundError
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

FAKE_IP = "10.0.0.0"

NO_ZONES = None
ZONE2 = {"Zone2": None}
ZONE3 = {"Zone3": None}
ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}

TESTING_RECEIVERS = {"AVR-X4100W": NO_ZONES, "AVR-2312CI": NO_ZONES,
                     "AVR-1912": NO_ZONES, "AVR-3311CI": NO_ZONES,
                     "M-RC610": NO_ZONES, "AVR-X2100W-2": NO_ZONES,
                     "AVR-X2000": ZONE2_ZONE3, "AVR-X2000-2": NO_ZONES,
                     "SR5008": NO_ZONES, "M-CR603": NO_ZONES,
                     "NR1604": ZONE2_ZONE3, "AVR-4810": NO_ZONES,
                     "AVR-3312": NO_ZONES, "NR1609": ZONE2,
                     "AVC-8500H": ZONE2_ZONE3}

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


class TestMainFunctions(testtools.TestCase):
    """Test case for main functions of Denon AVR."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        if (sys.version_info > (3, 0)):
            super().__init__(*args, **kwargs)
        else:  # Python 2 support
            super(TestMainFunctions, self).__init__(*args, **kwargs)
        self._testing_receiver = None

    @requests_mock.mock()
    # pylint: disable=arguments-differ
    def setUp(self, mocker):
        """Initialize test functions, using the first receiver from list."""
        if (sys.version_info > (3, 0)):
            super().setUp()
        else:  # Python 2 support
            super(TestMainFunctions, self).setUp()
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
    def test_input_func_switch(self, mock):
        """Switch through all input functions of all tested receivers."""
        mock.add_matcher(self.custom_matcher)
        for receiver, zones in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=zones)
            # Switch through all functions and check if successful
            for zone in self.denon.zones.values():
                if receiver == 'AVC-8500H':
                    print(receiver, zone.input_func_list)
                for input_func in zone.input_func_list:
                    self.denon.set_input_func(input_func)
                    self.assertEqual(
                        input_func, self.denon.input_func,
                        ("Input function change to {func} "
                         "not successful for {receiver}").format(
                             func=input_func, receiver=receiver))

    @requests_mock.mock()
    def test_attributes_not_none(self, mock):
        """Check that certain attributes are not None."""
        mock.add_matcher(self.custom_matcher)
        for receiver, zones in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=zones)
            self.assertIsNotNone(
                self.denon.power,
                "Power status is None for receiver {}".format(receiver))
            self.assertIsNotNone(
                self.denon.state,
                "State is None for receiver {}".format(receiver))
