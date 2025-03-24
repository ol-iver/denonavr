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
from denonavr.api import DenonAVRTelnetApi, DenonAVRTelnetProtocol
from denonavr.const import SOUND_MODE_MAPPING
from denonavr.exceptions import AvrNetworkError, AvrTimoutError

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
    "AVC-A10H": (ZONE2_ZONE3, denonavr.const.AVR_X_2016),
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
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
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
                    f"{self.testing_receiver}-formMainZone_MainZoneXmlStatus"
                    f"{port_suffix}.xml"
                )
            elif request.url.path == STATUS_Z2_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formZone2_Zone2XmlStatus{port_suffix}.xml"
                )
            elif request.url.path == STATUS_Z3_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formZone3_Zone3XmlStatus{port_suffix}.xml"
                )
            elif request.url.path == MAINZONE_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formMainZone_MainZoneXml{port_suffix}.xml"
                )
            elif request.url.path == DEVICEINFO_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-Deviceinfo{port_suffix}.xml"
                )
            elif request.url.path == NETAUDIOSTATUS_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formNetAudio_StatusXml{port_suffix}.xml"
                )
            elif request.url.path == TUNERSTATUS_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formTuner_TunerXml{port_suffix}.xml"
                )
            elif request.url.path == HDTUNERSTATUS_URL:
                content = get_sample_content(
                    f"{self.testing_receiver}-formTuner_HdXml{port_suffix}.xml"
                )
            elif request.url.path == APPCOMMAND_URL:
                content_str = request.read().decode("utf-8")
                if "GetFriendlyName" in content_str:
                    ep_suffix = "-setup"
                elif "GetAllZoneSource" in content_str:
                    ep_suffix = "-update"
                elif "GetSurroundModeStatus" in content_str:
                    ep_suffix = "-update-soundmode"
                else:
                    ep_suffix = "-update-tonecontrol"
                content = get_sample_content(
                    f"{self.testing_receiver}-AppCommand{ep_suffix}{port_suffix}.xml"
                )
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
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_receiver_type(self, httpx_mock: HTTPXMock):
        """Check that receiver type is determined correctly."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            print(f"Receiver: {receiver}")
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            await self.denon.async_setup()
            assert self.denon.receiver_type == spec[1].type, (
                f"Receiver type is {self.denon.receiver_type} not {spec[1].type} for"
                f" receiver {receiver}"
            )
            assert self.denon.receiver_port == spec[1].port, (
                f"Receiver port is {self.denon.receiver_port} not {spec[1].port} for"
                f" receiver {receiver}"
            )

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_input_func_switch(self, httpx_mock: HTTPXMock):
        """Switch through all input functions of all tested receivers."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            # Switch through all functions and check if successful
            for name, zone in self.denon.zones.items():
                print(f"Receiver: {receiver}, Zone: {name}")
                await self.denon.zones[name].async_update()
                assert len(zone.input_func_list) > 0
                for input_func in zone.input_func_list:
                    await self.denon.zones[name].async_set_input_func(input_func)

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_attributes_not_none(self, httpx_mock: HTTPXMock):
        """Check that certain attributes are not None."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            print(f"Receiver: {receiver}")
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            await self.denon.async_setup()
            assert self.denon.name is not None, f"Name is None for receiver {receiver}"
            assert (
                self.denon.support_sound_mode is not None
            ), f"support_sound_mode is None for receiver {receiver}"
            await self.denon.async_update()
            assert (
                self.denon.power is not None
            ), f"Power status is None for receiver {receiver}"
            assert (
                self.denon.state is not None
            ), f"State is None for receiver {receiver}"

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_sound_mode(self, httpx_mock: HTTPXMock):
        """Check if a valid sound mode is returned."""
        httpx_mock.add_callback(self.custom_matcher)
        for receiver, spec in TESTING_RECEIVERS.items():
            # Switch receiver and update to load new sample files
            self.testing_receiver = receiver
            self.denon = denonavr.DenonAVR(FAKE_IP, add_zones=spec[0])
            # Switch through all functions and check if successful
            for name in self.denon.zones:
                print(f"Receiver: {receiver}, Zone: {name}")
                await self.denon.zones[name].async_update()
                support_sound_mode = self.denon.zones[name].support_sound_mode
                sound_mode = self.denon.zones[name].sound_mode
                assert (
                    sound_mode in [*SOUND_MODE_MAPPING, None]
                    or support_sound_mode is not True
                )

    @pytest.mark.asyncio
    async def test_protocol_connected(self):
        """Connected after connection made."""
        proto = DenonAVRTelnetProtocol(None, None)
        transport = mock.Mock(is_closing=lambda: False)
        proto.connection_made(transport)

        assert proto.connected

    @pytest.mark.asyncio
    async def test_protocol_not_connected(self):
        """Not connected when connection not made."""
        proto = DenonAVRTelnetProtocol(None, None)

        assert not proto.connected

    @pytest.mark.asyncio
    async def test_protocol_closing(self):
        """Not connected when connection is closing."""
        proto = DenonAVRTelnetProtocol(None, None)
        transport = mock.Mock(is_closing=lambda: True)
        proto.connection_made(transport)

        assert not proto.connected

    @pytest.mark.asyncio
    async def test_protocol_writes_to_transport(self):
        """Write writes to transport."""
        proto = DenonAVRTelnetProtocol(None, None)
        transport = mock.Mock(is_closing=lambda: False)
        proto.connection_made(transport)

        proto.write("abc")

        transport.write.assert_called_with("abc".encode("utf-8"))

    @pytest.mark.asyncio
    async def test_protocol_close_closes_transport(self):
        """Write writes to transport."""
        proto = DenonAVRTelnetProtocol(None, None)
        transport = mock.Mock()
        proto.connection_made(transport)

        proto.close()

        transport.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_protocol_full_message_triggers_callback(self):
        """Read callback triggered for CR terminated message."""
        data_received_mock = mock.Mock()
        proto = DenonAVRTelnetProtocol(data_received_mock, None)
        transport = mock.Mock(is_closing=lambda: False)
        proto.connection_made(transport)
        proto.data_received(b"abc\r")

        data_received_mock.assert_called_with(b"abc".decode("utf-8"))

    @pytest.mark.asyncio
    async def test_protocol_partial_message_does_not_triggers_callback(self):
        """Read callback not triggered for non CR terminated message."""
        data_received_mock = mock.Mock()
        proto = DenonAVRTelnetProtocol(data_received_mock, None)
        transport = mock.Mock(is_closing=lambda: False)
        proto.connection_made(transport)
        proto.data_received(b"abc")

        data_received_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_protocol_connection_lost_triggers_callback(self):
        """Connection lost triggers callback."""
        conn_lost_mock = mock.Mock()
        proto = DenonAVRTelnetProtocol(None, conn_lost_mock)
        transport = mock.Mock(is_closing=lambda: False)
        proto.connection_made(transport)
        proto.connection_lost(Exception())

        conn_lost_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_telnetapi_not_healthy_if_protocol_not_connected(self):
        """Not healthy when not connected."""
        protocol = mock.Mock()
        api = DenonAVRTelnetApi()
        # pylint: disable=protected-access
        api._protocol = protocol
        protocol.connected = False

        assert not api.healthy

    @pytest.mark.asyncio
    async def test_telnetapi_healthy_if_protocol_connected(self):
        """Healthy when connected."""
        protocol = mock.Mock()
        api = DenonAVRTelnetApi()
        # pylint: disable=protected-access
        api._protocol = protocol
        protocol.connected = True

        assert api.healthy

    @pytest.mark.asyncio
    async def test_register_callback_invalid_event_raises_valueerror(self):
        """Callback raises on invalid event."""
        mock_callback = mock.Mock()
        api = DenonAVRTelnetApi()
        with pytest.raises(ValueError):
            api.register_callback("INVALIDEVENT", mock_callback.method)

    @pytest.mark.asyncio
    async def test_register_callback_valid_event_does_not_raise(self):
        """Callback succeeds on valid event."""
        mock_callback = mock.Mock()
        api = DenonAVRTelnetApi()
        api.register_callback("ALL", mock_callback.method)

    @pytest.mark.asyncio
    async def test_unregister_callback_succeeds(self):
        """Unregister callback succeeds."""
        mock_callback = mock.Mock()
        api = DenonAVRTelnetApi()
        api.unregister_callback("ALL", mock_callback.method)

    @pytest.mark.asyncio
    async def test_connect_connectionrefused_raises_networkerror(self):
        """Connect raises NetworkError when ConnectionRefused."""
        api = DenonAVRTelnetApi()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=ConnectionRefusedError()
            )
            with pytest.raises(AvrNetworkError):
                await api.async_connect()

    @pytest.mark.asyncio
    async def test_connect_oserror_raises_networkerror(self):
        """Connect raises NetworkError when OSError."""
        api = DenonAVRTelnetApi()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=OSError()
            )
            with pytest.raises(AvrNetworkError):
                await api.async_connect()

    @pytest.mark.asyncio
    async def test_connect_ioerror_raises_networkerror(self):
        """Connect raises NetworkError when IOError."""
        api = DenonAVRTelnetApi()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=IOError()
            )
            with pytest.raises(AvrNetworkError):
                await api.async_connect()

    @pytest.mark.asyncio
    async def test_connect_timeouterror_raises_timeouterror(self):
        """Connect raises AvrTimeoutError when TimeoutError."""
        api = DenonAVRTelnetApi()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=asyncio.TimeoutError()
            )
            with pytest.raises(AvrTimoutError):
                await api.async_connect()

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_receive_callback_called(self, httpx_mock: HTTPXMock):
        """Check that the callback is triggered whena message is received."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_connection_lost = proto._on_connection_lost
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)

        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            mock_obj = mock.Mock()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", mock_obj.method)
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MUON\r")
            await self.future
            mock_obj.method.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_mute_on(self, httpx_mock: HTTPXMock):
        """Check that mute on is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MUON\r")
            await self.future
            assert self.denon.muted

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_mute_off(self, httpx_mock: HTTPXMock):
        """Check that mute off is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MUOFF\r")
            await self.future
            assert not self.denon.muted

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_power_on(self, httpx_mock: HTTPXMock):
        """Check that power on is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"ZMON\r")
            await self.future
            assert self.denon.power == "ON"

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_power_off(self, httpx_mock: HTTPXMock):
        """Check that power off is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"ZMOFF\r")
            await self.future
            assert self.denon.power == "OFF"

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_volume_min(self, httpx_mock: HTTPXMock):
        """Check that minimum volume is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MV00\r")
            await self.future
            assert self.denon.volume == -80.0

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_volume_wholenumber(self, httpx_mock: HTTPXMock):
        """Check that whole number volume is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MV56\r")
            await self.future
            assert self.denon.volume == -24.0

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_volume_fraction(self, httpx_mock: HTTPXMock):
        """Check that fractional volume is processed."""
        transport = mock.Mock(is_closing=lambda: False)
        protocol = DenonAVRTelnetProtocol(None, None)

        def create_conn(proto_lambda, host, port):
            proto = proto_lambda()
            # pylint: disable=protected-access
            protocol._on_message = proto._on_message
            proto.connection_made(transport)
            protocol.connection_made(transport)
            return [transport, proto]

        httpx_mock.add_callback(self.custom_matcher)
        self.denon = denonavr.DenonAVR(FAKE_IP)
        # pylint: disable=protected-access
        self.denon._device.telnet_api._send_confirmation_timeout = 0.1
        await self.denon.async_setup()
        with mock.patch("asyncio.get_event_loop", new_callable=mock.Mock) as debug_mock:
            debug_mock.return_value.create_connection = mock.AsyncMock(
                side_effect=create_conn
            )
            await self.denon.async_telnet_connect()
            self.future = asyncio.Future()
            self.denon.register_callback("ALL", self._callback)
            protocol.data_received(b"MV565\r")
            await self.future
            assert self.denon.volume == -23.5
