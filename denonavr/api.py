#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST API to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

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
from .exceptions import AvrInvalidResponseError
from .const import (
    APPCOMMAND_CMD_TEXT, APPCOMMAND_NAME, APPCOMMAND_URL, APPCOMMAND0300_URL,
    DENON_ATTR_SETATTR)

_LOGGER = logging.getLogger(__name__)


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
            raise AvrInvalidResponseError(
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
