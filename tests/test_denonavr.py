#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import testtools
import requests
import requests_mock
import denonavr

FAKE_IP = "10.0.0.0"
TESTING_RECEIVERS = ("AVR-X4100W", "AVR-2312CI", "AVR-1912", "AVR-3311CI")

STATUS_URL = "/goform/formMainZone_MainZoneXmlStatus.xml"
MAINZONE_URL = "/goform/formMainZone_MainZoneXml.xml"
DEVICEINFO_URL = "/goform/Deviceinfo.xml"
NETAUDIOSTATUS_URL = "/goform/formNetAudio_StatusXml.xml"
TUNERSTATUS_URL = "/goform/formTuner_TunerXml.xml"
HDTUNERSTATUS_URL = "/goform/formTuner_HdXml.xml"


def get_sample_content(filename):
    """Returns sample content form file"""
    with open("tests/xml/{filename}".format(filename=filename),
              encoding="utf-8") as file:
        return file.read()


class TestMainFunctions(testtools.TestCase):
    """Test case for main functions of Denon AVR"""

    @requests_mock.mock()
    def setUp(self, m):
        """Setup method, using the first receiver from list"""
        self._testing_receiver = TESTING_RECEIVERS[0]
        super(TestMainFunctions, self).setUp()
        m.add_matcher(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)

    def custom_matcher(self, request):
        """Match URLs to sample files"""
        if request.path_url == STATUS_URL:
            content = get_sample_content(
                        "{receiver}-formMainZone_MainZoneXmlStatus.xml"
                        .format(receiver=self._testing_receiver))
        elif request.path_url == MAINZONE_URL:
            content = get_sample_content(
                        "{receiver}-formMainZone_MainZoneXml.xml"
                        .format(receiver=self._testing_receiver))
        elif request.path_url == DEVICEINFO_URL:
            content = get_sample_content(
                        "{receiver}-Deviceinfo.xml"
                        .format(receiver=self._testing_receiver))
        elif request.path_url == NETAUDIOSTATUS_URL:
            content = get_sample_content(
                        "{receiver}-formNetAudio_StatusXml.xml"
                        .format(receiver=self._testing_receiver))
        elif request.path_url == TUNERSTATUS_URL:
            content = get_sample_content(
                        "{receiver}-formTuner_TunerXml.xml"
                        .format(receiver=self._testing_receiver))
        elif request.path_url == HDTUNERSTATUS_URL:
            content = get_sample_content(
                        "{receiver}-formTuner_HdXml.xml"
                        .format(receiver=self._testing_receiver))
        else:
            content = "DATA"

        resp = requests.Response()
        resp.encoding = "utf-8"
        resp._content = content.encode()
        resp.status_code = 200
        return resp

    @requests_mock.mock()
    def test_input_func_switch(self, m):
        """Switch through all input functions of all tested receivers"""
        m.add_matcher(self.custom_matcher)
        for receiver in TESTING_RECEIVERS:
            # Switch receiver and update to load new sample files
            self._testing_receiver = receiver
            self.denon.update()
            # Switch through all functions and check if successful
            for input_func in self.denon.input_func_list:
                self.denon.set_input_func(input_func)
                self.assertEqual(input_func, self.denon.input_func,
                                 "Input function change to {func} not \
                                 successful".format(func=input_func))
