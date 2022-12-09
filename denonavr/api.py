#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST and Telnet APIs to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
from contextlib import suppress
import inspect
import logging
import xml.etree.ElementTree as ET

from io import BytesIO
from typing import Callable, Dict, Hashable, Optional, Tuple

import attr
import httpx

from asyncstdlib import lru_cache
from defusedxml.ElementTree import fromstring

from .appcommand import AppCommandCmd
from .decorators import (
    async_handle_receiver_exceptions,
    cache_clear_on_exception,
    set_cache_id)
from .exceptions import AvrIncompleteResponseError, AvrInvalidResponseError, AvrTimoutError
from .const import (
    APPCOMMAND_CMD_TEXT, APPCOMMAND_NAME, APPCOMMAND_URL, APPCOMMAND0300_URL,
    DENON_ATTR_SETATTR, MAIN_ZONE, ZONE2, ZONE3, TELNET_SOURCES)

_LOGGER = logging.getLogger(__name__)

_SOCKET_READ_SIZE = 135

def get_default_async_client() -> httpx.AsyncClient:
    """Get the default httpx.AsyncClient."""
    return httpx.AsyncClient()


@attr.s(auto_attribs=True, hash=False, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRApi:
    """Perform API calls to Denon AVR REST interface."""

    host: str = attr.ib(converter=str, default="localhost")
    port: int = attr.ib(converter=int, default=80)
    timeout: httpx.Timeout = attr.ib(
        validator=attr.validators.instance_of(httpx.Timeout),
        default=httpx.Timeout(2.0, read=15.0))
    _appcommand_update_tags: Tuple[AppCommandCmd] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(AppCommandCmd),
            attr.validators.instance_of(tuple)),
        default=attr.Factory(tuple))
    _appcommand0300_update_tags: Tuple[AppCommandCmd] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(AppCommandCmd),
            attr.validators.instance_of(tuple)),
        default=attr.Factory(tuple))
    async_client_getter: Callable[[], httpx.AsyncClient] = attr.ib(
        validator=attr.validators.is_callable(),
        default=get_default_async_client, init=False)

    def __hash__(self) -> int:
        """
        Hash the class in a custom way that caching works.

        It should react on changes of host and port.
        """
        return hash((self.host, self.port))

    @async_handle_receiver_exceptions
    async def async_get(
            self,
            request: str,
            port: Optional[int] = None) -> httpx.Response:
        """Call GET endpoint of Denon AVR receiver asynchronously."""
        # Use default port of the receiver if no different port is specified
        port = port if port is not None else self.port

        endpoint = "http://{host}:{port}{request}".format(
            host=self.host, port=port, request=request)

        client = self.async_client_getter()
        try:
            res = await client.get(endpoint, timeout=self.timeout)
            res.raise_for_status()
        finally:
            # Close the default AsyncClient but keep custom clients open
            if self.is_default_async_client():
                await client.aclose()

        return res

    @async_handle_receiver_exceptions
    async def async_post(
            self,
            request: str,
            content: Optional[bytes] = None,
            data: Optional[Dict] = None,
            port: Optional[int] = None) -> httpx.Response:
        """Call POST endpoint of Denon AVR receiver asynchronously."""
        # Use default port of the receiver if no different port is specified
        port = port if port is not None else self.port

        endpoint = "http://{host}:{port}{request}".format(
            host=self.host, port=port, request=request)

        client = self.async_client_getter()
        try:
            res = await client.post(
                endpoint, content=content, data=data, timeout=self.timeout)
            res.raise_for_status()
        finally:
            # Close the default AsyncClient but keep custom clients open
            if self.is_default_async_client():
                await client.aclose()

        return res

    @async_handle_receiver_exceptions
    async def async_get_command(self, request: str) -> str:
        """Send HTTP GET command to Denon AVR receiver asynchronously."""
        # HTTP GET to endpoint
        res = await self.async_get(request)
        # Return text
        return res.text

    @set_cache_id
    @cache_clear_on_exception
    @lru_cache(maxsize=32)
    @async_handle_receiver_exceptions
    async def async_get_xml(
            self,
            request: str,
            cache_id: Hashable = None
            ) -> ET.Element:
        """Return XML data from HTTP GET endpoint asynchronously."""
        # HTTP GET to endpoint
        res = await self.async_get(request)
        # create ElementTree
        xml_root = fromstring(res.text)
        # Check validity of XML
        self.check_xml_validity(request, xml_root)
        # Return ElementTree element
        return xml_root

    @set_cache_id
    @cache_clear_on_exception
    @lru_cache(maxsize=32)
    @async_handle_receiver_exceptions
    async def async_post_appcommand(
            self,
            request: str,
            cmds: Tuple[AppCommandCmd],
            cache_id: Hashable = None
            ) -> ET.Element:
        """Return XML from Appcommand(0300) endpoint asynchronously."""
        # Prepare XML body for POST call
        content = self.prepare_appcommand_body(cmds)
        _LOGGER.debug("Content for %s endpoint: %s", request, content)
        # HTTP POST to endpoint
        res = await self.async_post(request, content=content)
        # create ElementTree
        xml_root = fromstring(res.text)
        # Check validity of XML
        self.check_xml_validity(request, xml_root)
        # Add query tags to result
        xml_root = self.add_query_tags_to_result(request, cmds, xml_root)
        # Return ElementTree element
        return xml_root

    def add_appcommand_update_tag(self, tag: AppCommandCmd) -> None:
        """Add appcommand tag for full update."""
        if tag.cmd_id != "1":
            raise ValueError("cmd_id is {} but must be 1".format(tag.cmd_id))

        # Remove response pattern from tag because it is not relevant for query
        tag = attr.evolve(tag, response_pattern=tuple())

        if tag not in self._appcommand_update_tags:
            _LOGGER.debug("Add tag %s to AppCommand update tuple", tag)
            self._appcommand_update_tags = (*self._appcommand_update_tags, tag)

    def add_appcommand0300_update_tag(self, tag: AppCommandCmd) -> None:
        """Add appcommand0300 tag for full update."""
        if tag.cmd_id != "3":
            raise ValueError("cmd_id is {} but must be 3".format(tag.cmd_id))

        # Remove response pattern from tag because it is not relevant for query
        tag = attr.evolve(tag, response_pattern=tuple())

        if tag not in self._appcommand0300_update_tags:
            _LOGGER.debug("Add tag %s to AppCommand0300 update tuple", tag)
            self._appcommand0300_update_tags = (
                *self._appcommand0300_update_tags, tag)

    async def async_get_global_appcommand(
            self,
            appcommand0300: bool = False,
            cache_id: Optional[Hashable] = None) -> ET.Element:
        """Get XML structure for full AppCommand update."""
        if appcommand0300:
            tags = self._appcommand0300_update_tags
            url = APPCOMMAND0300_URL
        else:
            tags = self._appcommand_update_tags
            url = APPCOMMAND_URL

        res = await self.async_post_appcommand(url, tags, cache_id=cache_id)
        return res

    @staticmethod
    def add_query_tags_to_result(
            request: str,
            cmd_list: Tuple[AppCommandCmd],
            xml_root: ET.Element
            ) -> ET.Element:
        """
        Add query tags to corresponding elements of result XML.

        This is used to identitfy the result tags.
        """
        if len(cmd_list) != len(xml_root):
            raise AvrIncompleteResponseError(
                "Invalid length of response XML. Query has {} elements, "
                "response {}".format(len(cmd_list), len(xml_root)), request)

        for i, child in enumerate(xml_root):
            if child.tag not in ["cmd", "error"]:
                raise AvrInvalidResponseError(
                    "Returned document contains a tag other than \"cmd\" and "
                    "\"error\": {}".format(child.tag), request)
            # Find corresponding attributes from request XML if set and add
            # tag to cmd element
            if cmd_list[i].cmd_text is not None:
                child.set(APPCOMMAND_CMD_TEXT, cmd_list[i].cmd_text)
            if cmd_list[i].name is not None:
                child.set(APPCOMMAND_NAME, cmd_list[i].name)

        return xml_root

    @staticmethod
    def check_xml_validity(request: str, xml_root: ET.Element) -> None:
        """Check if there is a valid Denon XML and not a HTML page."""
        if xml_root.tag == "html":
            raise AvrInvalidResponseError(
                "Returned document contains HTML", request)

    @staticmethod
    def prepare_appcommand_body(cmd_list: Tuple[AppCommandCmd]) -> bytes:
        """Prepare HTTP POST body to AppCommand(0300).xml end point."""
        # Buffer XML body as binary IO
        body = BytesIO()

        # Denon AppCommand.xml acts weird. It returns an error when the tx
        # element consists of more than 5 cmd elements, but it accepts
        # multiple XML root elements
        chunks = [cmd_list[i:i+5] for i in range(
            0, len(cmd_list), 5)]

        for i, chunk in enumerate(chunks):
            # Prepare POST XML body for AppCommand.xml
            xml_root = ET.Element("tx")

            for cmd in chunk:
                # Append tags for each element
                cmd_element = ET.Element("cmd")
                cmd_element.set("id", cmd.cmd_id)

                # Optional cmd text
                cmd_element.text = cmd.cmd_text

                # Optional name tag
                if cmd.name is not None:
                    name_element = ET.Element("name")
                    name_element.text = cmd.name
                    cmd_element.append(name_element)

                # Optional list tag
                if cmd.param_list is not None:
                    param_list_element = ET.Element("list")
                    for param in cmd.param_list:
                        param_element = ET.Element("param")
                        param_element.set("name", param.name)
                        param_element.text = param.text
                        param_list_element.append(param_element)
                    cmd_element.append(param_list_element)

                xml_root.append(cmd_element)

                # Optional command parameter
                if cmd.set_command is not None:
                    command_element = ET.Element(cmd.set_command.name)
                    command_element.text = cmd.set_command.text
                    xml_root.append(command_element)

            xml_tree = ET.ElementTree(xml_root)
            # XML declaration only for the first chunk
            xml_tree.write(
                body, encoding="utf-8", xml_declaration=bool(i == 0))

        body_bytes = body.getvalue()

        # Buffered XML not needed anymore: close
        body.close()

        return body_bytes

    def is_default_async_client(self) -> bool:
        """Check if default httpx.AsyncCLient getter is used."""
        return self.async_client_getter is get_default_async_client

@attr.s(auto_attribs=True, hash=False, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRTelnetApi:

    host: str = attr.ib(converter=str, default="localhost")
    timeout: int = attr.ib(converter=int, default=10)
    _telnet_task: asyncio.Task = attr.ib(default=None)
    _callbacks: dict[str, Callable] = attr.ib(
        validator=attr.validators.instance_of(dict),
        default={}, init=False
    )
    
    async def async_connect(self) -> asyncio.Task:
        """ Connect to the receiver asynchronously."""
        try:
            self._socket_reader, self._socket_writer = await asyncio.wait_for(asyncio.open_connection(self.host, 23), timeout=self.timeout)
            self._telnet_task = asyncio.create_task(self._async_monitor())
            return self._telnet_task
        except asyncio.exceptions.TimeoutError as err:
            _LOGGER.debug(
                "Socket timeout exception on connect",
                exc_info=True)
            raise AvrTimoutError(
                "TimeoutException: {}".format(err), "connect") from err

    async def async_disconnect(self) -> None:
        """Close the connection to the receiver asynchronously."""
        if self._telnet_task:
            self._telnet_task.cancel()
            self._telnet_task = None
        if self._socket_writer:
            self._socket_writer.close()
            with suppress(ConnectionError):
                await self._socket_writer.wait_closed()
            self._socket_writer = None

    async def _async_monitor(self):
        """Reads the messages on the TCP socket."""
        data = bytearray()
        while not self._socket_reader.at_eof():
            try:
                chunk = await asyncio.wait_for(self._socket_reader.read(_SOCKET_READ_SIZE), self.timeout)
                for i in range(0,len(chunk)):
                    # Messages are CR terminated
                    if chunk[i] != 13:
                        data += chunk[i].to_bytes(1, byteorder='big')
                    else:
                        await self._process_event(str(data,'utf-8'))
                        data = bytearray()
            except asyncio.exceptions.TimeoutError as err:
                _LOGGER.debug("Lost connection to receiver, reconnecting")
                await self.async_disconnect()
                await self.async_connect()

    def register_callback(self, type: str="ALL", callback=lambda *args: any):
        """Registers a callback handler for an event type."""       
        if not type in self._callbacks.keys():
            self._callbacks[type] = []
        self._callbacks[type].append(callback)

    def unregister_callback(self, type: str="ALL", callback=lambda *args: any):
        """Unregisters a callback handler for an event type."""
        if not type in self._callbacks.keys():
            return
        self._callbacks[type].remove(callback)

    async def _process_event(self, message: str):
        """Process a realtime event."""
        if len(message) < 3:
            return None
        
        #Event is 2 characters
        event = message[0:2]
        #Parameter is the remaining characters
        parameter = message[2:]
        
        if event == 'PW':
            await self._process_power(MAIN_ZONE, parameter)
        elif event == 'MV':
            await self._process_volume(MAIN_ZONE, parameter)
        elif event == 'MU':
            await self._process_mute(MAIN_ZONE, parameter)
        elif event == 'SI':
            await self._process_input(MAIN_ZONE, parameter)
        elif event == 'MS':
            await self._process_surroundmode(MAIN_ZONE, parameter)
        elif event == 'PS':
            await self._process_sounddetail(MAIN_ZONE, parameter)
        
        elif event == 'Z2' or event == 'Z3':
            if event == 'Z2':
                zone = ZONE2
            else:
                zone = ZONE3
            if parameter == 'ON' or parameter == 'OFF':
                await self._process_power(zone, parameter)
            elif parameter == 'MUON' or parameter == 'MUOFF':
                await self._process_mute(zone, parameter)
            elif parameter in TELNET_SOURCES:
                await self._process_input(zone, parameter)
            elif parameter.isdigit():
                await self._process_volume(zone, parameter)        

    async def _trigger_callbacks(self, type: str, zone: str, value: any):
        """Handle triggering the registered callbacks for the specified type"""
        if type in self._callbacks.keys():
            for callback in self._callbacks[type]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(zone, value)
                    else:
                        callback(zone, value)
                except Exception as err:
                    # We don't want a single bad callback to trip up the whole system and prevent further 
                    # execution
                    print(err)
                    _LOGGER.error(f"Event callback triggered an unhandled exception {err}")

        if "ALL" in self._callbacks.keys():
            for callback in self._callbacks["ALL"]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        await callback(zone)
                    else:
                        callback(zone)
                except Exception as err:
                    _LOGGER.error(f"Event callback triggered an unhandled exception {err}")
        
    async def _process_power(self, zone, parameter):
        """Process a power event."""
        await self._trigger_callbacks("PW", zone, parameter)

    async def _process_volume(self, zone, parameter):
        """Process a volume event."""
        if parameter[0:3] == "MAX":
            return
        if parameter == "---":
            await self._trigger_callbacks("MV", zone, -80.0)
        else:
            if len(parameter) < 3:
                await self._trigger_callbacks("MV", zone, -80.0 + float(parameter))
            else:
                await self._trigger_callbacks("MV", zone, -80.0 + float(parameter[0:2]) + (0.1 * float(parameter[2])))

    async def _process_mute(self, zone, parameter):
        """Process a mute event."""
        await self._trigger_callbacks("MU", zone, parameter)

    async def _process_input(self, zone, parameter):
        """Process an input source change event."""
        await self._trigger_callbacks("SI", zone, parameter)

    async def _process_surroundmode(self, zone, parameter):
        """Process a surround mode event."""
        await self._trigger_callbacks("MS", zone, parameter)

    async def _process_sounddetail(self, zone, parameter):
        """Process a sound detail event."""
        if parameter[0:3] == "BAS":
            value = int(parameter[4:])
            await self._trigger_callbacks("BAS", zone, value)
        elif parameter[0:3] == "TRE":
            value = int(parameter[4:])
            await self._trigger_callbacks("TRE", zone, value)
        elif parameter[0:6] == "REFLEV":
            value = parameter[7:]
            await self._trigger_callbacks("REFLEV", zone, value)
        elif parameter[0:6] == "DYNVOL":
            value = parameter[7:]
            await self._trigger_callbacks("DYNVOL", zone, value)
        elif parameter[0:6] == "MULTEQ":
            value = parameter[7:]
            await self._trigger_callbacks("MULTEQ", zone, value)
        elif parameter == "DYNEQ ON":
            await self._trigger_callbacks("DYNEQ", zone, "1")
        elif parameter == "DYNEQ OFF":
            await self._trigger_callbacks("DYNEQ", zone, "0")
        if parameter == "TONE CTRL OFF":
            await self._trigger_callbacks("TONE", zone, "1")
        elif parameter == "TONE CTRL ON":
            await self._trigger_callbacks("TONE", zone, "0")