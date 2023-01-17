#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers some basic automated tests of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
from unittest import mock
import httpx
import pytest
from pytest_httpx import HTTPXMock

import denonavr
from denonavr.const import SOUND_MODE_MAPPING

FAKE_IP = "10.0.0.0"

NO_ZONES = None
ZONE2 = {"Zone2": None}
ZONE3 = {"Zone3": None}
ZONE2_ZONE3 = {"Zone2": None, "Zone3": None}

TESTING_RECEIVERS = {
    "AVR-X4100W": (NO_ZONES, denonavr.const.AVR_X),
    "AVR-2312CI": (NO_ZONES, denonavr.const.AVR),
    "AVR-1912": (NO_ZONES, denonavr.const.AVR),
    "AVR-3311CI": (NO_ZONES, denonavr.const.AVR),
    "M-RC610": (NO_ZONES, denonavr.const.AVR_X),
    "AVR-X2100W-2": (NO_ZONES, denonavr.const.AVR_X),
    "AVR-X2000": (ZONE2_ZONE3, denonavr.const.AVR_X),
    "AVR-X2000-2": (NO_ZONES, denonavr.const.AVR_X),
    "SR5008": (NO_ZONES, denonavr.const.AVR_X),
    "M-CR603": (NO_ZONES, denonavr.const.AVR),
    "NR1604": (ZONE2_ZONE3, denonavr.const.AVR_X),
    "AVR-4810": (NO_ZONES, denonavr.const.AVR),
    "AVR-3312": (NO_ZONES, denonavr.const.AVR),
    "NR1609": (ZONE2, denonavr.const.AVR_X_2016),
    "AVC-8500H": (ZONE2_ZONE3, denonavr.const.AVR_X_2016),
    "AVR-X4300H": (ZONE2_ZONE3, denonavr.const.AVR_X_2016),
    "AVR-X1100W": (ZONE2, denonavr.const.AVR_X),
    "SR6012": (ZONE2, denonavr.const.AVR_X_2016),
    "M-CR510": (NO_ZONES, denonavr.const.AVR_X),
    "M-CR510-2": (NO_ZONES, denonavr.const.AVR_X),
    "AVC-X3700H": (ZONE2, denonavr.const.AVR_X_2016),
    "AVR-X4000": (ZONE2_ZONE3, denonavr.const.AVR_X),
    "SR6011": (ZONE2, denonavr.const.AVR_X),
    "AV7703": (ZONE2_ZONE3, denonavr.const.AVR_X_2016),
    "AVR-1713": (NO_ZONES, denonavr.const.AVR_X),
    "AVR-3313": (ZONE2_ZONE3, denonavr.const.AVR_X),
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
DESCRIPTION_URL1 = "/description.xml"
DESCRIPTION_URL2 = "/upnp/desc/aios_device/aios_device.xml"


def get_sample_content(filename):
    """Return sample content form file."""
    with open("tests/xml/{filename}".format(filename=filename),
              encoding="utf-8") as file:
        return file.read()


class TestMainFunctions:
    """Test case for main functions of Denon AVR."""

    testing_receiver = None
    denon = None
    future = None

    def custom_matcher(self, request: httpx.Request, *args, **kwargs):
        """Match URLs to sample files."""
        port_suffix = ""

        if request.url.port == 8080:
            port_suffix = "-8080"

        try:
            if request.url.path == STATUS_URL:
                content = get_sample_content(
                    "{receiver}-formMainZone_MainZoneXmlStatus{port}"
                    ".xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == STATUS_Z2_URL:
                content = get_sample_content(
                    "{receiver}-formZone2_Zone2XmlStatus{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == STATUS_Z3_URL:
                content = get_sample_content(
                    "{receiver}-formZone3_Zone3XmlStatus{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == MAINZONE_URL:
                content = get_sample_content(
                    "{receiver}-formMainZone_MainZoneXml{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == DEVICEINFO_URL:
                content = get_sample_content(
                    "{receiver}-Deviceinfo{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == NETAUDIOSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formNetAudio_StatusXml{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == TUNERSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formTuner_TunerXml{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == HDTUNERSTATUS_URL:
                content = get_sample_content(
                    "{receiver}-formTuner_HdXml{port}.xml".format(
                        receiver=self.testing_receiver, port=port_suffix))
            elif request.url.path == APPCOMMAND_URL:
                content_str = request.read().decode("utf-8")
                if "GetFriendlyName" in content_str:
                    ep_suffix = "-setup"
                else:
                    ep_suffix = "-update"
                content = get_sample_content(
                    "{receiver}-AppCommand{ep}{port}.xml".format(
                        receiver=self.testing_receiver,
                        port=port_suffix,
                        ep=ep_suffix))
            elif request.url.path in [DESCRIPTION_URL1, DESCRIPTION_URL2]:
                content = get_sample_content("AVR-X1600H_upnp.xml")
            else:
                content = "DATA"
        except FileNotFoundError:
            content = "Error 403: Forbidden\nAccess Forbidden"
            status_code = 403
        else:
            status_code = 200

        resp = httpx.Response(status_code=status_code, content=content)

        return resp

    async def _callback(self, zone, event, parameter):
        self.future.set_result(True)

    @pytest.mark.asyncio
    async def test_receiver_type(self, httpx_mock: HTTPXMock):
        """Check that receiver type is determined correctly."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            print("Receiver: {}".format(receiver))
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            await self.denon.async_setup()
            assert self.denon.receiver_type == spec[1].type, (
                "Receiver type is {} not {} for receiver {}".format(
                    self.denon.receiver_type, spec[1].type, receiver))
            assert self.denon.receiver_port == spec[1].port, (
                "Receiver port is {} not {} for receiver {}".format(
                    self.denon.receiver_port, spec[1].port, receiver))

    @pytest.mark.asyncio
    async def test_input_func_switch(self, httpx_mock: HTTPXMock):
        """Switch through all input functions of all tested receivers."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            # Switch through all functions and check if successful
            for name, zone in self.denon.zones.items():
                print("Receiver: {}, Zone: {}".format(receiver, name))
                await self.denon.zones[name].async_update()
                assert len(zone.input_func_list) > 0
                for input_func in zone.input_func_list:
                    await self.denon.zones[name].async_set_input_func(
                        input_func)

    @pytest.mark.asyncio
    async def test_attributes_not_none(self, httpx_mock: HTTPXMock):
        """Check that certain attributes are not None."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            print("Receiver: {}".format(receiver))
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            await self.denon.async_setup()
            assert self.denon.name is not None, (
                "Name is None for receiver {}".format(receiver))
            assert self.denon.support_sound_mode is not None, (
                "support_sound_mode is None for receiver {}".format(receiver))
            await self.denon.async_update()
            assert self.denon.power is not None, (
                "Power status is None for receiver {}".format(receiver))
            assert self.denon.state is not None, (
                "State is None for receiver {}".format(receiver))

    @pytest.mark.asyncio
    async def test_sound_mode(self, httpx_mock: HTTPXMock):
        """Check if a valid sound mode is returned."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            # Switch through all functions and check if successful
            for name in self.denon.zones:
                print("Receiver: {}, Zone: {}".format(receiver, name))
                await self.denon.zones[name].async_update()
                support_sound_mode = self.denon.zones[name].support_sound_mode
                sound_mode = self.denon.zones[name].sound_mode
                assert (
                    sound_mode in [*SOUND_MODE_MAPPING, None] or
                    support_sound_mode is not True)

    @pytest.mark.asyncio
    async def test_receive_callback_called(self, httpx_mock: HTTPXMock):
        """Check that the callback is triggered whena message is received."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            mock_obj = mock.Mock()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", mock_obj.method)
            self.denon.register_callback("ALL", self._callback)
            reader.feed_data(b"MUON\r")
            await self.future
            mock_obj.method.assert_called_once()

    @pytest.mark.asyncio
    async def test_mute_on(self, httpx_mock: HTTPXMock):
        """Check that mute on is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"MUON\r")
            await self.future
            assert self.denon.muted

    @pytest.mark.asyncio
    async def test_mute_off(self, httpx_mock: HTTPXMock):
        """Check that mute off is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"MUOFF\r")
            await self.future
            assert not self.denon.muted

    @pytest.mark.asyncio
    async def test_power_on(self, httpx_mock: HTTPXMock):
        """Check that power on is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"PWON\r")
            await self.future
            assert self.denon.power == "ON"

    @pytest.mark.asyncio
    async def test_power_off(self, httpx_mock: HTTPXMock):
        """Check that power off is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"PWSTANDBY\r")
            await self.future
            assert self.denon.power == "STANDBY"

    @pytest.mark.asyncio
    async def test_volume_min(self, httpx_mock: HTTPXMock):
        """Check that minimum volume is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"MV00\r")
            await self.future
            assert self.denon.volume == -80.0

    @pytest.mark.asyncio
    async def test_volume_wholenumber(self, httpx_mock: HTTPXMock):
        """Check that whole number volume is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"MV56\r")
            await self.future
            assert self.denon.volume == -24.0

    @pytest.mark.asyncio
    async def test_volume_fraction(self, httpx_mock: HTTPXMock):
        """Check that fractional volume is processed."""
        with mock.patch("asyncio.open_connection",
                        new_callable=AsyncMock) as debug_mock:
            reader = asyncio.StreamReader()
            debug_mock.return_value = (reader, asyncio.StreamReader())
            httpx_mock.add_callback(self.custom_matcher)

            self.denon = denonavr.DenonAVR(FAKE_IP)
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            await self.denon.async_setup()
            await self.denon.async_telnet_connect()
            reader.feed_data(b"MV565\r")
            await self.future
            assert self.denon.volume == -23.5


class AsyncMock(mock.MagicMock):
    """Mocking async methods compatible to python 3.7."""

    # pylint: disable=invalid-overridden-method,useless-super-delegation
    async def __call__(self, *args, **kwargs):
        """Call."""
        return super().__call__(*args, **kwargs)
