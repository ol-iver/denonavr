#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the handler for input functions of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
from collections.abc import Hashable
from copy import deepcopy
from typing import Dict, List, Optional, Set, Tuple

import attr
import httpx
from ftfy import fix_text

from .appcommand import AppCommands
from .const import (
    ALBUM_COVERS_URL,
    APPCOMMAND_CMD_TEXT,
    AVR,
    AVR_X,
    AVR_X_2016,
    CHANGE_INPUT_MAPPING,
    DENON_ATTR_SETATTR,
    HDTUNER_SOURCES,
    MAIN_ZONE,
    NETAUDIO_SOURCES,
    PLAYING_SOURCES,
    POWER_ON,
    SOURCE_MAPPING,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
    STATIC_ALBUM_URL,
    TELNET_MAPPING,
    TUNER_SOURCES,
    ZONE2,
    ZONE3,
)
from .exceptions import AvrCommandError, AvrProcessingError, AvrRequestError
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)

_MEDIA_UPDATE_INTERVAL = 5


def lower_string(value: Optional[str]) -> Optional[str]:
    """Convert string to lower case."""
    if value is None:
        return value
    return str(value).lower()


def fix_string(value: Optional[str]) -> Optional[str]:
    """Fix errors in string like unescaped HTML and wrong utf-8 encoding."""
    if value is None:
        return value
    return fix_text(str(value)).strip()


def set_input_func(
    instance: "DenonAVRInput", attribute: attr.Attribute, value: str
) -> str:
    """Set input_func after mapping from input_func_map."""
    # pylint: disable=protected-access
    # No changes for None
    if value is None:
        return value
    # Map from input_func_map
    # AirPlay and Internet Radio are not always listed in available sources
    if value in ["AirPlay", "Internet Radio"]:
        if value not in instance._input_func_map:
            instance._additional_input_funcs.add(value)
            instance._input_func_map[value] = value
            instance._input_func_map_rev[value] = value
            instance._netaudio_func_list.append(value)
            instance._playing_func_list.append(value)
    try:
        input_func = instance._input_func_map_rev[value]
    except KeyError:
        _LOGGER.info("No mapping for source %s found", value)
        input_func = value

    return input_func


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRInput(DenonAVRFoundation):
    """This class implements input functions of Denon AVR receiver."""

    _show_all_inputs: bool = attr.ib(converter=bool, default=False)
    _input_func_map: Dict[str, str] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str), attr.validators.instance_of(str)
        ),
        default=attr.Factory(dict),
    )
    _input_func_map_rev: Dict[str, str] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str), attr.validators.instance_of(str)
        ),
        default=attr.Factory(dict),
    )
    _netaudio_func_list: List[str] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(str), attr.validators.instance_of(list)
        ),
        default=attr.Factory(list),
    )
    _playing_func_list: List[str] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(str), attr.validators.instance_of(list)
        ),
        default=attr.Factory(list),
    )
    _favorite_func_list: List[str] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(str), attr.validators.instance_of(list)
        ),
        default=attr.Factory(list),
    )
    _additional_input_funcs: Set[str] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(str), attr.validators.instance_of(set)
        ),
        default=attr.Factory(set),
    )
    _media_update_handle: asyncio.TimerHandle = attr.ib(default=None)
    _input_func_update_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))

    _state: Optional[str] = attr.ib(
        converter=attr.converters.optional(lower_string), default=None
    )
    _input_func: Optional[str] = attr.ib(
        converter=attr.converters.optional(str),
        on_setattr=[*DENON_ATTR_SETATTR, set_input_func],
        default=None,
    )

    _artist: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _album: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _band: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _title: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _frequency: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _station: Optional[str] = attr.ib(
        converter=attr.converters.optional(fix_string), default=None
    )
    _image_url: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _image_available: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )

    _renamed_sources_warnings: Set[Tuple[str, str]] = attr.ib(
        validator=attr.validators.deep_iterable(
            attr.validators.instance_of(tuple), attr.validators.instance_of(set)
        ),
        default=attr.Factory(set),
    )

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {AppCommands.GetAllZoneSource: None}
    # Status.xml interface
    status_xml_attrs = {"_input_func": "./InputFuncSelect/value"}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        # For update of input function list
        self._device.api.add_appcommand_update_tag(AppCommands.GetAllZoneSource)
        self._device.api.add_appcommand_update_tag(AppCommands.GetRenameSource)
        self._device.api.add_appcommand_update_tag(AppCommands.GetDeletedSource)
        # For update of state
        for tag in self.appcommand_attrs:
            self._device.api.add_appcommand_update_tag(tag)

        power_event = "ZM"
        if self._device.zone == ZONE2:
            power_event = "Z2"
        elif self._device.zone == ZONE3:
            power_event = "Z3"
        self._device.telnet_api.register_callback(
            power_event, self._async_power_callback
        )
        self._device.telnet_api.register_callback("SI", self._async_input_callback)
        self._device.telnet_api.register_callback("NSE", self._async_netaudio_callback)
        self._device.telnet_api.register_callback("TF", self._async_tuner_callback)
        self._device.telnet_api.register_callback("HD", self._async_hdtuner_callback)
        self._device.telnet_api.register_callback(
            "SS", self._async_input_func_update_callback
        )

        self._is_setup = True

    async def _async_input_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle an input change event."""
        if self._device.zone != zone:
            return

        self._input_func = TELNET_MAPPING.get(parameter, parameter)

        if self._device.power != POWER_ON:
            return

        if self._schedule_media_updates():
            self._state = STATE_PLAYING
        else:
            self._unset_media_state()
            self._state = STATE_ON

    async def _async_power_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a power change event."""
        if self._device.zone != zone:
            return

        if parameter != POWER_ON:
            self._stop_media_update()
            self._unset_media_state()
            self._state = STATE_OFF
        elif self._schedule_media_updates():
            self._state = STATE_PLAYING
        else:
            self._unset_media_state()
            self._state = STATE_ON

    def _schedule_media_updates(self) -> bool:
        """Schedule media state updates in telnet callbacks."""
        if self._input_func in self._netaudio_func_list:
            self._stop_media_update()
            self._schedule_netaudio_update()
            return True
        if self._input_func in TUNER_SOURCES:
            self._stop_media_update()
            self._schedule_tuner_update()
            return True
        if self._input_func in HDTUNER_SOURCES:
            self._stop_media_update()
            self._schedule_hdtuner_update()
            return True

        self._stop_media_update()
        return False

    def _stop_media_update(self) -> None:
        """Stop the media update task."""
        if self._media_update_handle is not None:
            self._media_update_handle.cancel()
            self._media_update_handle = None

    def _schedule_netaudio_update(self) -> None:
        """Schedule a netaudio update task."""
        loop = asyncio.get_event_loop()
        delay = _MEDIA_UPDATE_INTERVAL
        if self._media_update_handle is None:
            delay = 0
        self._media_update_handle = loop.call_later(delay, self._update_netaudio)

    def _update_netaudio(self) -> None:
        """Update netaudio information."""
        if self._device.telnet_available:
            self._device.telnet_api.send_commands("NSE", skip_confirmation=True)
            self._schedule_netaudio_update()
        else:
            self._stop_media_update()

    async def _async_netaudio_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a netaudio update event."""
        if self._device.power != POWER_ON:
            return
        if self._input_func not in self._netaudio_func_list:
            return

        if parameter.startswith("1"):
            self._title = parameter[1:]
        elif parameter.startswith("2"):
            self._artist = parameter[1:]
        elif parameter.startswith("4"):
            self._album = parameter[1:]
        self._band = None
        self._frequency = None
        self._station = None

        # Refresh cover with a hash for media URL when track is changing
        self._image_url = ALBUM_COVERS_URL.format(
            host=self._device.api.host,
            port=self._device.api.port,
            hash=hash((self._title, self._artist, self._album)),
        )
        await self._async_test_image_accessible()

    def _schedule_tuner_update(self) -> None:
        """Schedule a tuner update task."""
        loop = asyncio.get_event_loop()
        delay = _MEDIA_UPDATE_INTERVAL
        if self._media_update_handle is None:
            delay = 0
        self._media_update_handle = loop.call_later(delay, self._update_tuner)

    def _update_tuner(self) -> None:
        """Update tuner information."""
        if self._device.telnet_available:
            self._device.telnet_api.send_commands(
                "TFAN?", "TFANNAME?", skip_confirmation=True
            )
            self._schedule_tuner_update()
        else:
            self._stop_media_update()

    async def _async_tuner_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a tuner update event."""
        if self._device.power != POWER_ON:
            return
        if self._input_func not in ["Tuner", "TUNER"]:
            return

        if parameter.startswith("ANNAME"):
            self._station = parameter[6:]
        elif len(parameter) == 8:
            self._frequency = f"{parameter[2:6]}.{parameter[6:]}".strip("0")
            if parameter[2:] > "050000":
                self._band = "AM"
            else:
                self._band = "FM"

        self._title = None
        self._artist = None
        self._album = None

        # No special cover, using a static one
        self._image_url = STATIC_ALBUM_URL.format(
            host=self._device.api.host, port=self._device.api.port
        )
        await self._async_test_image_accessible()

    def _schedule_hdtuner_update(self) -> None:
        """Schedule a HD tuner update task."""
        loop = asyncio.get_event_loop()
        delay = _MEDIA_UPDATE_INTERVAL
        if self._media_update_handle is None:
            delay = 0
        self._media_update_handle = loop.call_later(delay, self._update_hdtuner)

    def _update_hdtuner(self) -> None:
        """Update HD tuner information."""
        if self._device.telnet_available:
            self._device.telnet_api.send_commands("HD?", skip_confirmation=True)
            self._schedule_hdtuner_update()
        else:
            self._stop_media_update()

    async def _async_hdtuner_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle an HD tuner update event."""
        if self._device.power != POWER_ON:
            return
        if self._input_func not in ["HD Radio", "HDRADIO"]:
            return

        if parameter.startswith("ARTIST"):
            self._artist = parameter[6:]
        elif parameter.startswith("TITLE"):
            self._title = parameter[5:]
        elif parameter.startswith("ALBUM"):
            self._album = parameter[5:]
        elif parameter.startswith("ST NAME"):
            self._station = parameter[7:]

        self._band = None
        self._frequency = None

        # No special cover, using a static one
        self._image_url = STATIC_ALBUM_URL.format(
            host=self._device.api.host, port=self._device.api.port
        )
        await self._async_test_image_accessible()

    async def _async_input_func_update_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle input func update events."""
        if self._input_func_update_lock.locked():
            return
        async with self._input_func_update_lock:
            await self.async_update_inputfuncs()

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update input functions asynchronously."""
        _LOGGER.debug("Starting input update")
        # Ensure instance is setup before updating
        if not self._is_setup:
            self.setup()

        # Update input functions
        _LOGGER.debug("Updating input functions")
        await self.async_update_inputfuncs(
            global_update=global_update, cache_id=cache_id
        )
        # Update state
        _LOGGER.debug("Updating input state")
        await self.async_update_state(global_update=global_update, cache_id=cache_id)
        # Update media state
        _LOGGER.debug("Updating media state")
        await self.async_update_media_state(cache_id=cache_id)
        _LOGGER.debug("Finished input update")

    async def async_get_sources_deviceinfo(self) -> Dict[str, str]:
        """Get sources from Deviceinfo.xml."""
        try:
            # Deviceinfo.xml is static and can be cached for the whole time
            xml = await self._device.api.async_get_xml(
                self._device.urls.deviceinfo, cache_id=id(self._device)
            )
        except AvrRequestError as err:
            _LOGGER.debug("Error when getting sources: %s", err)
            raise

        receiver_sources = {}
        # Source determination from XML
        favorites = xml.find(".//FavoriteStation")
        if favorites is not None:
            favorite_func_list = []
            for child in favorites:
                if not child.tag.startswith("Favorite"):
                    continue
                func_name = child.tag.upper()
                favorite_func_list.append(func_name)
                receiver_sources[func_name] = child.find("Name").text
            self._favorite_func_list = favorite_func_list
        for xml_zonecapa in xml.findall("DeviceZoneCapabilities"):
            zone_no = "0"
            if self._device.zone == ZONE2:
                zone_no = "1"
            elif self._device.zone == ZONE3:
                zone_no = "2"
            if xml_zonecapa.find("./Zone/No").text == zone_no:
                # Get list of all input sources of receiver
                xml_list = xml_zonecapa.find("./InputSource/List")
                for xml_source in xml_list.findall("Source"):
                    receiver_sources[xml_source.find("FuncName").text] = (
                        xml_source.find("DefaultName").text
                    )

        return receiver_sources

    async def async_get_changed_sources_appcommand(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Get renamed and deleted sources lists from receiver .

        Internal method which queries device via HTTP to get names of renamed
        input sources. In this method AppCommand.xml is used.
        """
        # renamed_sources and deleted_sources are dicts with "source" as key
        # and "renamed_source" or deletion flag as value.
        renamed_sources = {}
        deleted_sources = {}

        # Collect tags for AppCommand.xml call
        tags = (AppCommands.GetRenameSource, AppCommands.GetDeletedSource)
        # Execute call
        try:
            if global_update:
                xml = await self._device.api.async_get_global_appcommand(
                    cache_id=cache_id
                )
            else:
                xml = await self._device.api.async_post_appcommand(
                    self._device.urls.appcommand, tags, cache_id=cache_id
                )
        except AvrRequestError as err:
            _LOGGER.debug("Error when getting changed sources: %s", err)
            raise

        for child in xml.findall(
            f"./cmd[@{APPCOMMAND_CMD_TEXT}='{AppCommands.GetRenameSource.cmd_text}']"
            "/functionrename/list"
        ):
            try:
                renamed_sources[child.find("name").text.strip()] = child.find(
                    "rename"
                ).text.strip()
            except AttributeError:
                continue

        for child in xml.findall(
            f"./cmd[@{APPCOMMAND_CMD_TEXT}='{AppCommands.GetDeletedSource.cmd_text}']"
            "/functiondelete/list"
        ):
            try:
                deleted_sources[child.find("FuncName").text.strip()] = (
                    "DEL" if (child.find("use").text.strip() == "0") else None
                )
            except AttributeError:
                continue

        self._replace_duplicate_sources(renamed_sources)

        return (renamed_sources, deleted_sources)

    async def async_get_changed_sources_status_xml(
        self, cache_id: Optional[Hashable] = None
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Get renamed and deleted sources lists from receiver .

        Internal method which queries device via HTTP to get names of renamed
        input sources.
        """
        # renamed_sources and deleted_sources are dicts with "source" as key
        # and "renamed_source" or deletion flag as value.
        renamed_sources = {}
        deleted_sources = {}
        xml_inputfunclist = []
        xml_renamesource = []
        xml_deletesource = []

        # This XML is needed to get names of eventually renamed sources
        try:
            # AVR-X and AVR-nonX using different XMLs to provide info about
            # deleted sources
            if self._device.receiver == AVR_X:
                xml = await self._device.api.async_get_xml(
                    self._device.urls.status, cache_id=cache_id
                )
            # These are the input functions of Main Zone.
            elif self._device.receiver == AVR:
                xml = await self._device.api.async_get_xml(
                    self._device.urls.mainzone, cache_id=cache_id
                )
            else:
                raise AvrProcessingError(
                    "Method does not work for receiver type"
                    f" {self._device.receiver.type}"
                )
        except AvrRequestError as err:
            _LOGGER.debug("Error when getting changed sources: %s", err)
            raise

        # Get the relevant tags from XML structure
        for child in xml:
            # Default names of the sources
            if child.tag == "InputFuncList":
                for value in child:
                    xml_inputfunclist.append(value.text)
            # Renamed sources
            if child.tag == "RenameSource":
                for value in child:
                    # Two different kinds of source structure types exist
                    # 1. <RenameSource><Value>...
                    if value.text is not None:
                        xml_renamesource.append(value.text.strip())
                    # 2. <RenameSource><Value><Value>
                    else:
                        try:
                            xml_renamesource.append(value[0].text.strip())
                        # Exception covers empty tags and appends empty line
                        # in this case, to ensure that sources and
                        # renamed_sources lists have always the same length
                        except IndexError:
                            xml_renamesource.append(None)
            # Deleted sources
            if child.tag == "SourceDelete":
                for value in child:
                    xml_deletesource.append(value.text)

        # If the deleted source list is empty then use all sources.
        if not xml_deletesource:
            xml_deletesource = ["USE"] * len(xml_inputfunclist)

        # Renamed and deleted sources are in the same row as the default ones
        # Only values which are not None are considered. Otherwise translation
        # is not valid and original name is taken
        for i, item in enumerate(xml_inputfunclist):
            try:
                if xml_renamesource[i] is not None:
                    renamed_sources[item] = xml_renamesource[i]
                else:
                    renamed_sources[item] = item
            except IndexError:
                _LOGGER.error("List of renamed sources incomplete, continuing anyway")
            try:
                deleted_sources[item] = xml_deletesource[i]
            except IndexError:
                _LOGGER.error("List of deleted sources incomplete, continuing anyway")

        self._replace_duplicate_sources(renamed_sources)

        return (renamed_sources, deleted_sources)

    async def async_update_inputfuncs(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update sources list from receiver."""
        if self._device.receiver in [AVR_X, AVR_X_2016]:
            await self._async_update_inputfuncs_avr_x(
                global_update=global_update, cache_id=cache_id
            )
        elif self._device.receiver in [AVR]:
            await self._async_update_inputfuncs_avr(cache_id=cache_id)
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, receiver type not set"
            )

    async def _async_update_inputfuncs_avr_x(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """
        Update sources list from receiver for AVR-X and AVR-X-2016 devices.

        Internal method which updates sources list of receiver after getting
        sources and potential renaming information from receiver.
        """
        # Get all sources from receiver
        receiver_sources = await self.async_get_sources_deviceinfo()

        if not receiver_sources:
            _LOGGER.debug(
                "Receiver sources list empty. Please check if device is powered on."
            )

        # Add additional input functions discovered at run-time
        for function in self._additional_input_funcs:
            receiver_sources[function] = function

        # Get renamed and deleted sources
        # From Appcommand.xml if supported
        if self._device.use_avr_2016_update:
            (
                renamed_sources,
                deleted_sources,
            ) = await self.async_get_changed_sources_appcommand(
                global_update=global_update, cache_id=cache_id
            )
        else:
            # Else from status xml
            (
                renamed_sources,
                deleted_sources,
            ) = await self.async_get_changed_sources_status_xml(cache_id=cache_id)

        # Add new renamed_sources to receiver_sources
        for key, value in renamed_sources.items():
            if key not in receiver_sources:
                receiver_sources[key] = value

        # Remove all deleted sources
        if not self._show_all_inputs:
            for deleted_source in deleted_sources.items():
                if deleted_source[1] == "DEL":
                    receiver_sources.pop(deleted_source[0], None)

        # Rebuild the sources lists
        input_func_map = {}
        input_func_map_rev = {}
        netaudio_func_list = []
        playing_func_list = []

        for item in receiver_sources.items():
            # Mapping of item[0] because some func names are inconsistent
            # at AVR-X receivers

            m_item_0 = SOURCE_MAPPING.get(item[0], item[0])

            # For renamed sources use those names and save the default name
            # for a later mapping
            if item[0] in renamed_sources:
                input_func_map[renamed_sources[item[0]]] = m_item_0
                input_func_map_rev[m_item_0] = renamed_sources[item[0]]
                # If the source is a netaudio source, save its renamed name
                if item[0] in NETAUDIO_SOURCES:
                    netaudio_func_list.append(renamed_sources[item[0]])
                # If the source is a playing source, save its renamed name
                if item[0] in PLAYING_SOURCES:
                    playing_func_list.append(renamed_sources[item[0]])
            # Otherwise the default names are used
            else:
                input_func_map[item[1]] = m_item_0
                input_func_map_rev[m_item_0] = item[1]
                # If the source is a netaudio source, save its name
                if item[1] in NETAUDIO_SOURCES:
                    netaudio_func_list.append(item[1])
                # If the source is a playing source, save its name
                if item[1] in PLAYING_SOURCES:
                    playing_func_list.append(item[1])

        self._input_func_map = input_func_map
        self._input_func_map_rev = input_func_map_rev
        self._netaudio_func_list = netaudio_func_list
        self._playing_func_list = playing_func_list

    async def _async_update_inputfuncs_avr(
        self, cache_id: Optional[Hashable] = None
    ) -> None:
        """
        Update sources list from receiver for AVR devices.

        Internal method which updates sources list of receiver after getting
        sources and potential renaming information from receiver.
        """
        # Get source from status xml
        (
            receiver_sources,
            deleted_sources,
        ) = await self.async_get_changed_sources_status_xml(cache_id=cache_id)

        # Add additional input functions discovered at run-time
        for function in self._additional_input_funcs:
            receiver_sources[function] = function

        # Remove all deleted sources
        if not self._show_all_inputs:
            for deleted_source in deleted_sources.items():
                if deleted_source[1] == "DEL":
                    receiver_sources.pop(deleted_source[0], None)

        # Rebuild the sources lists
        input_func_map = {}
        input_func_map_rev = {}
        netaudio_func_list = []
        playing_func_list = []
        for item in receiver_sources.items():
            input_func_map[item[1]] = item[0]
            input_func_map_rev[item[0]] = item[1]
            # If the source is a netaudio source, save its name
            if item[0] in NETAUDIO_SOURCES:
                netaudio_func_list.append(item[1])
            # If the source is a playing source, save its name
            if item[0] in PLAYING_SOURCES:
                playing_func_list.append(item[1])

        self._input_func_map = input_func_map
        self._input_func_map_rev = input_func_map_rev
        self._netaudio_func_list = netaudio_func_list
        self._playing_func_list = playing_func_list

    async def async_update_state(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ):
        """Update state of device."""
        if self._device.use_avr_2016_update is None:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set"
            )

        if self._device.use_avr_2016_update:
            await self.async_update_attrs_appcommand(
                self.appcommand_attrs, global_update=global_update, cache_id=cache_id
            )
        else:
            urls = [self._device.urls.status]
            if self._device.zone == MAIN_ZONE:
                urls.append(self._device.urls.mainzone)
            await self.async_update_attrs_status_xml(
                self.status_xml_attrs, urls, cache_id=cache_id
            )

    async def async_update_media_state(self, cache_id: Optional[Hashable] = None):
        """Update media state of device."""
        # Now playing information is not implemented for 2016+ models, as
        # a HEOS API query needed. So only sync the power state for now.
        if self._device.receiver == AVR_X_2016:
            self._state = STATE_ON if self._device.power == POWER_ON else STATE_OFF
        elif (
            self._device.power == POWER_ON
            and self._input_func in self._playing_func_list
        ):
            await self._async_update_media_data(cache_id)
        else:
            self._state = STATE_ON if self._device.power == POWER_ON else STATE_OFF
            self._unset_media_state()

    async def _async_update_media_data(
        self, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update media data of device."""
        urls = []
        status_xml_attrs = {}

        if self._input_func in self._netaudio_func_list:
            urls = [self._device.urls.netaudiostatus]
            status_xml_attrs = {
                "_title": "./szLine/value[2]",
                "_artist": "./szLine/value[3]",
                "_album": "./szLine/value[5]",
            }
            self._band = None
            self._frequency = None
            self._station = None
            # Image URL and state are detected after update
        elif self._input_func in TUNER_SOURCES:
            urls = [self._device.urls.tunerstatus]
            status_xml_attrs = {
                "_band": "./Band/value",
                "_frequency": "./Frequency/value",
            }
            self._title = None
            self._artist = None
            self._album = None
            self._station = None
            # No special cover, using a static one
            self._image_url = STATIC_ALBUM_URL.format(
                host=self._device.api.host, port=self._device.api.port
            )
            # Assume Tuner is always PLAYING
            self._state = STATE_PLAYING
        elif self._input_func in HDTUNER_SOURCES:
            urls = [self._device.urls.hdtunerstatus]
            status_xml_attrs = {
                "_artist": "./Artist/value",
                "_album": "./Album/value",
                "_title": "./Title/value",
                "_band": "./Band/value",
                "_frequency": "./Frequency/value",
                "_station": "./StationNameSh /value",
            }
            # No special cover, using a static one
            self._image_url = STATIC_ALBUM_URL.format(
                host=self._device.api.host, port=self._device.api.port
            )
            # Assume Tuner is always PLAYING
            self._state = STATE_PLAYING

        await self.async_update_attrs_status_xml(
            status_xml_attrs, urls, cache_id=cache_id
        )

        if self._input_func in self._netaudio_func_list:
            # Refresh cover with a hash for media URL when track is changing
            self._image_url = ALBUM_COVERS_URL.format(
                host=self._device.api.host,
                port=self._device.api.port,
                hash=hash((self._title, self._artist, self._album)),
            )
            # On track change assume device is PLAYING
            self._state = STATE_PLAYING

        await self._async_test_image_accessible()

    async def _async_test_image_accessible(self) -> None:
        """Test if image URL is accessible."""
        if self._image_available is None and self._image_url is not None:
            client = self._device.api.httpx_async_client.client_getter()
            try:
                res = await client.get(
                    self._image_url,
                    timeout=httpx.Timeout(
                        self._device.api.timeout, read=self._device.api.read_timeout
                    ),
                )
                res.raise_for_status()
            except httpx.TimeoutException:
                # No result set image URL to None
                self._image_url = None
            except httpx.HTTPStatusError:
                _LOGGER.info("No album art available for your receiver")
                # No image available. Save this status.
                self._image_available = False
                #  Set image URL to None.
                self._image_url = None
            else:
                self._image_available = True
            finally:
                # Close the default AsyncClient but keep custom clients open
                if self._device.api.httpx_async_client.is_default_async_client():
                    await client.aclose()
        # Already tested that image URL is not accessible
        elif not self._image_available:
            self._image_url = None

    def _unset_media_state(self) -> None:
        """Unsets media state attributes."""
        self._title = None
        self._artist = None
        self._album = None
        self._band = None
        self._frequency = None
        self._station = None
        self._image_url = None

    def _replace_duplicate_sources(self, sources: Dict[str, str]) -> None:
        """Replace duplicate renamed sources (values) with their original names."""
        seen_values = set()
        duplicate_values = set()

        for value in sources.values():
            if value in seen_values:
                duplicate_values.add(value)
            seen_values.add(value)

        for duplicate in duplicate_values:
            for key, value in sources.items():
                if value == duplicate:
                    sources[key] = key

                    if (key, value) not in self._renamed_sources_warnings:
                        _LOGGER.warning(
                            (
                                "Input source '%s' is renamed to non-unique name '%s'. "
                                "Using original name. Please choose unique names in "
                                "your receiver's web-interface"
                            ),
                            key,
                            value,
                        )
                        self._renamed_sources_warnings.add((key, value))

    ##############
    # Properties #
    ##############
    @property
    def state(self) -> Optional[str]:
        """
        Return the state of the device.

        Possible values are: "on", "off", "playing", "paused"
        "playing" and "paused" are only available for input functions
        in PLAYING_SOURCES.
        """
        return self._state

    @property
    def input_func(self) -> Optional[str]:
        """Return the current input source as string."""
        return self._input_func

    @property
    def input_func_list(self) -> List[str]:
        """Return a list of available input sources as string."""
        return sorted(self._input_func_map.keys())

    @property
    def image_url(self) -> Optional[str]:
        """Return image URL of current playing media when powered on."""
        if self._device.power == POWER_ON:
            return self._image_url
        return None

    @property
    def title(self) -> Optional[str]:
        """Return title of current playing media as string."""
        return self._title

    @property
    def artist(self) -> Optional[str]:
        """Return artist of current playing media as string."""
        return self._artist

    @property
    def album(self) -> Optional[str]:
        """Return album name of current playing media as string."""
        return self._album

    @property
    def band(self) -> Optional[str]:
        """Return band of current radio station as string."""
        return self._band

    @property
    def frequency(self) -> Optional[str]:
        """Return frequency of current radio station as string."""
        return self._frequency

    @property
    def station(self) -> Optional[str]:
        """Return current radio station as string."""
        return self._station

    @property
    def netaudio_func_list(self) -> List[str]:
        """Return list of network audio devices.

        Those devices should react to play, pause, next and previous
        track commands.
        """
        return deepcopy(self._netaudio_func_list)

    @property
    def playing_func_list(self) -> List[str]:
        """Return list of playing devices.

        Those devices offer additional information about what they are playing
        (e.g. title, artist, album, band, frequency, station, image_url).
        """
        return deepcopy(self._playing_func_list)

    ##########
    # Setter #
    ##########

    async def async_set_input_func(self, input_func: str) -> None:
        """
        Set input_func of device.

        Valid values depend on the device and should be taken from
        "input_func_list".
        """
        # For selection of sources other names then at receiving sources
        # have to be used
        # AVR-X receiver needs source mapping to set input_func
        linp = ""
        direct_mapping = True
        if self._device.receiver in [AVR_X, AVR_X_2016]:
            try:
                linp = CHANGE_INPUT_MAPPING[self._input_func_map[input_func]]
            except KeyError:
                direct_mapping = True
            else:
                direct_mapping = False
        # AVR-nonX receiver and if no mapping was found get parameter for
        # setting input_func directly
        if direct_mapping:
            try:
                linp = self._input_func_map[input_func]
            except KeyError as err:
                raise AvrCommandError(
                    f"No mapping for input source {input_func}"
                ) from err
        # Create command URL and send command via HTTP GET
        if linp in self._favorite_func_list:
            command_url = self._device.urls.command_fav_src + linp
            telnet_command = self._device.telnet_commands.command_fav_src + linp
        else:
            command_url = self._device.urls.command_sel_src + linp
            telnet_command = self._device.telnet_commands.command_sel_src + linp
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(telnet_command)
        else:
            await self._device.api.async_get_command(command_url)

    async def async_toggle_play_pause(self) -> None:
        """Toggle play pause media player."""
        # Use Play/Pause button only for sources which support NETAUDIO
        if (
            self._state == STATE_PLAYING
            and self._input_func in self._netaudio_func_list
        ):
            await self.async_pause()
        elif self._input_func in self._netaudio_func_list:
            await self.async_play()

    async def async_play(self) -> None:
        """Send play command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            # In fact play command is a play/pause toggle. Thus checking state
            if self._state == STATE_PLAYING:
                _LOGGER.info("Already playing, play command not sent")
                return
            if self._device.telnet_available:
                await self._device.telnet_api.async_send_commands(
                    self._device.telnet_commands.command_play
                )
            else:
                await self._device.api.async_get_command(self._device.urls.command_play)
            self._state = STATE_PLAYING

    async def async_pause(self) -> None:
        """Send pause command to receiver command via HTTP post."""
        # Use pause command only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            if self._device.telnet_available:
                await self._device.telnet_api.async_send_commands(
                    self._device.telnet_commands.command_play
                )
            else:
                await self._device.api.async_get_command(
                    self._device.urls.command_pause
                )
            self._state = STATE_PAUSED

    async def async_previous_track(self) -> None:
        """Send previous track command to receiver command via HTTP post."""
        # Use previous track button only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {
                "cmd0": "PutNetAudioCommand/CurUp",
                "cmd1": "aspMainZone_WebUpdateStatus/",
                "ZoneName": "MAIN ZONE",
            }
            await self._device.api.async_post(
                self._device.urls.command_netaudio_post, data=body
            )

    async def async_next_track(self) -> None:
        """Send next track command to receiver command via HTTP post."""
        # Use next track button only for sources which support NETAUDIO
        if self._input_func in self._netaudio_func_list:
            body = {
                "cmd0": "PutNetAudioCommand/CurDown",
                "cmd1": "aspMainZone_WebUpdateStatus/",
                "ZoneName": "MAIN ZONE",
            }
            await self._device.api.async_post(
                self._device.urls.command_netaudio_post, data=body
            )


def input_factory(instance: DenonAVRFoundation) -> DenonAVRInput:
    """Create DenonAVRInput at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRInput(
        device=instance._device, show_all_inputs=instance._show_all_inputs
    )
    return new
