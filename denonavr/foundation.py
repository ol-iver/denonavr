#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the foundation classes for Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
import xml.etree.ElementTree as ET

from copy import deepcopy
from typing import Dict, Hashable, List, Optional

import attr
import httpx

from .appcommand import AppCommandCmd, AppCommands
from .api import DenonAVRApi, DenonAVRTelnetApi
from .exceptions import (
    AvrForbiddenError, AvrIncompleteResponseError, AvrNetworkError,
    AvrProcessingError, AvrRequestError, AvrTimoutError)
from .const import (
    APPCOMMAND_CMD_TEXT, APPCOMMAND_NAME, AVR, AVR_X, AVR_X_2016,
    DENON_ATTR_SETATTR, DENONAVR_URLS, DESCRIPTION_TYPES,
    DEVICEINFO_AVR_X_PATTERN, DEVICEINFO_COMMAPI_PATTERN, MAIN_ZONE,
    VALID_RECEIVER_TYPES, VALID_ZONES, ReceiverType, ReceiverURLs, ZONE2,
    ZONE2_URLS, ZONE3, ZONE3_URLS)
from .ssdp import evaluate_scpd_xml


_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRDeviceInfo:
    """Implements a class with device information of the receiver."""

    api: DenonAVRApi = attr.ib(
        validator=attr.validators.instance_of(DenonAVRApi),
        default=attr.Factory(DenonAVRApi),
        kw_only=True)
    telnet_api: DenonAVRTelnetApi = attr.ib(
        validator=attr.validators.instance_of(DenonAVRTelnetApi),
        default=attr.Factory(DenonAVRTelnetApi),
        kw_only=True
    )
    receiver: Optional[ReceiverType] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.in_(VALID_RECEIVER_TYPES)),
        default=None)
    urls: ReceiverURLs = attr.ib(
        validator=attr.validators.instance_of(ReceiverURLs), init=False)
    zone: str = attr.ib(
        validator=attr.validators.in_(VALID_ZONES),
        default=MAIN_ZONE,
        kw_only=True)
    friendly_name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    manufacturer: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    model_name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    serial_number: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    use_avr_2016_update: Optional[bool] = attr.ib(
        converter=attr.converters.optional(bool), default=None)
    _power: Optional[str] = attr.ib(
        converter=attr.converters.optional(str),
        default=None)
    _is_setup: bool = attr.ib(converter=bool, default=False, init=False)
    _allow_recovery: bool = attr.ib(
        converter=bool, default=False, init=False)
    _setup_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))

    def __attrs_post_init__(self) -> None:
        """Initialize special attributes and callbacks."""
        # URLs depending from value of self.zone attribute
        if self.zone == MAIN_ZONE:
            self.urls = DENONAVR_URLS
        elif self.zone == ZONE2:
            self.urls = ZONE2_URLS
        elif self.zone == ZONE3:
            self.urls = ZONE3_URLS
        else:
            raise ValueError("Invalid zone {}".format(self.zone))

    async def _power_callback(
            self,
            zone: str,
            event: str,
            parameter: str) -> None:
        """Handle a power change event."""
        if self.zone == zone:
            self._power = parameter

    def get_own_zone(self):
        """
        Get zone from actual instance.

        These zone information are used to evaluate responses of HTTP POST
        commands.
        """
        if self.zone == MAIN_ZONE:
            return "zone1"
        return self.zone.lower()

    async def async_setup(self) -> None:
        """Ensure that configuration is loaded from receiver asynchronously."""
        async with self._setup_lock:
            # Own setup
            # Reduce read timeout during receiver identification
            # deviceinfo endpoint takes very long to return 404
            timeout = self.api.timeout
            self.api.timeout = httpx.Timeout(self.api.timeout.connect)
            try:
                await self.async_identify_receiver()
                await self.async_get_device_info()
            finally:
                self.api.timeout = timeout
            await self.async_identify_update_method()

            # Add tags for a potential AppCommand.xml update
            self.api.add_appcommand_update_tag(
                AppCommands.GetAllZonePowerStatus)

            self.telnet_api.register_callback("PW", self._power_callback)

            self._is_setup = True

    async def async_update(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None) -> None:
        """Update status asynchronously."""
        # Ensure instance is setup before updating
        if self._is_setup is False:
            await self.async_setup()

        # Update power status
        await self.async_update_power(
            global_update=global_update, cache_id=cache_id)

    async def async_identify_receiver(self) -> None:
        """Identify receiver asynchronously."""
        # Test Deviceinfo.xml if receiver is a AVR-X with port 80 for pre 2016
        # devices and port 8080 devices 2016 and later
        # 2016 models has also some of the XML but not all, try first 2016
        r_types = [AVR_X, AVR_X_2016]

        timeout_errors = 0
        for r_type in r_types:
            self.api.port = r_type.port
            # This XML is needed to get the sources of the receiver
            try:
                # Deviceinfo.xml is static and can be cached for the whole time
                xml = await self.api.async_get_xml(
                    self.urls.deviceinfo, cache_id=id(self))
            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error on port %s when identifying receiver",
                    r_type.port, exc_info=err)

                # Raise error only when occured at both types
                timeout_errors += 1
                if timeout_errors == len(r_types):
                    raise

            except AvrRequestError as err:
                _LOGGER.debug(
                    "Request error on port %s when identifying receiver, "
                    "device is not a %s receivers", r_type.port,
                    r_type.type, exc_info=err)
            else:
                is_avr_x = self._is_avr_x(xml)
                if is_avr_x:
                    self.receiver = r_type
                    # Receiver identified, return
                    return

        # If check of Deviceinfo.xml was not successfull, receiver is type AVR
        self.receiver = AVR
        self.api.port = AVR.port

    @staticmethod
    def _is_avr_x(deviceinfo: ET.Element) -> bool:
        """Evaluate Deviceinfo.xml if the device is a AVR-X device."""
        # First test by CommApiVers
        try:
            if bool(DEVICEINFO_COMMAPI_PATTERN.search(
                    deviceinfo.find("CommApiVers").text) is not None):
                # receiver found , return True
                return True
        except AttributeError:
            # AttributeError occurs when ModelName tag is not found.
            # In this case there is no AVR-X device
            pass

        # if first test did not find AVR-X device, check by model name
        try:
            if bool(DEVICEINFO_AVR_X_PATTERN.search(
                    deviceinfo.find("ModelName").text) is not None):
                # receiver found , return True
                return True
        except AttributeError:
            # AttributeError occurs when ModelName tag is not found
            # In this case there is no AVR-X device
            pass

        return False

    async def async_identify_update_method(self) -> None:
        """
        Identify the correct update method for the receiver asynchronously.

        As a result this method sets friendly name too.
        """
        # AVR receivers do not support AppCommand.xml interface
        if self.receiver == AVR:
            self.use_avr_2016_update = False
            _LOGGER.info("AVR device, AppCommand.xml interface not supported")
        else:
            try:
                xml = await self.api.async_post_appcommand(
                    self.urls.appcommand,
                    (AppCommands.GetFriendlyName,))
            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error when identifying update method",
                    exc_info=err)
                raise
            except AvrRequestError as err:
                _LOGGER.debug(
                    "Request error when identifying update method",
                    exc_info=err)
                self.use_avr_2016_update = False
                _LOGGER.info(
                    "AVR-X device, AppCommand.xml interface not supported")
            else:
                self.use_avr_2016_update = True
                _LOGGER.info("AVR-X device, using AppCommand.xml interface")
                self._set_friendly_name(xml)

        if self.use_avr_2016_update is False:
            try:
                xml = await self.api.async_get_xml(self.urls.mainzone)
            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error when identifying update method",
                    exc_info=err)
                raise
            except AvrRequestError as err:
                _LOGGER.debug(
                    "Request error getting friendly name", exc_info=err)
                _LOGGER.info(
                    "Receiver name could not be determined. Using standard"
                    " name: Denon AVR")
                if self.friendly_name is None:
                    self.friendly_name = "Denon AVR"
            else:
                self._set_friendly_name(xml)

    async def async_verify_avr_2016_update_method(
            self, cache_id: Hashable = None) -> None:
        """Verify if avr 2016 update method is working."""
        # Nothing to do if Appcommand.xml interface is not supported
        if self.use_avr_2016_update is False:
            return

        try:
            # Result is cached that it can be reused during update
            await self.api.async_get_global_appcommand(cache_id=cache_id)
        except (AvrTimoutError, AvrNetworkError) as err:
            _LOGGER.debug(
                "Connection error when verifying update method",
                exc_info=err)
            raise
        except AvrForbiddenError:
            # Recovery in case receiver changes port from 80 to 8080 which
            # might happen at Denon AVR-X 2016 receivers
            if self._allow_recovery is True:
                self._allow_recovery = False
                _LOGGER.warning(
                    "AppCommand.xml returns HTTP status 403. Running setup"
                    " again once to check if receiver interface switched "
                    "ports")
                self._is_setup = False
                await self.async_setup()
                await self.async_verify_avr_2016_update_method(
                    cache_id=cache_id)
            else:
                raise
        except AvrIncompleteResponseError as err:
            _LOGGER.debug(
                "Request error when verifying update method", exc_info=err)
            # Only AVR_X devices support both interfaces
            if self.receiver == AVR_X:
                _LOGGER.warning(
                    "Error verifying Appcommand.xml update method, it returns "
                    "an incomplete result set. Deactivating the interface")
                self.use_avr_2016_update = False
        else:
            if self._allow_recovery is False:
                _LOGGER.info(
                    "AppCommand.xml recovered from HTTP status 403 error")
            self._allow_recovery = True

    def _set_friendly_name(self, xml: ET.Element) -> None:
        """Set FriendlyName from result xml."""
        # friendlyname tag of AppCommand.xml, FriendlyName tag main zone xml
        tags = ("./cmd/friendlyname", "./FriendlyName/value")
        for tag in tags:
            try:
                name = xml.find(tag).text
            except AttributeError:
                pass
            else:
                if name is not None:
                    self.friendly_name = name.strip()
                    break
        if self.friendly_name is None:
            _LOGGER.warning(
                "No FriendlyName found, using standard name: Denon AVR")
            self.friendly_name = "Denon AVR"

    async def async_get_device_info(self) -> None:
        """Get device information."""
        port = DESCRIPTION_TYPES[self.receiver.type].port
        command = DESCRIPTION_TYPES[self.receiver.type].url
        url = "http://{host}:{port}{command}".format(
            host=self.api.host, port=port, command=command)

        device_info = None
        try:
            res = await self.api.async_get(command, port=port)
        except AvrTimoutError as err:
            _LOGGER.debug("Timeout when getting device info", exc_info=err)
            raise
        except AvrNetworkError as err:
            _LOGGER.debug("Network error getting device info", exc_info=err)
            raise
        except AvrRequestError as err:
            _LOGGER.error(
                "During DenonAVR device identification, when trying to request"
                " %s the following error occurred: %s", url, err)
        else:
            device_info = evaluate_scpd_xml(url, res.text)

        if device_info is None:
            self.manufacturer = "Denon"
            self.model_name = "Unknown"
            self.serial_number = None
            _LOGGER.warning(
                "Unable to get device information of host %s, Device might be "
                "in a corrupted state. Continuing without device information. "
                "Disconnect and reconnect power to the device and try again.",
                self.api.host)
            return

        if self.friendly_name is None and "friendlyName" in device_info:
            self.friendly_name = device_info["friendlyName"]
        self.manufacturer = device_info["manufacturer"]
        self.model_name = device_info["modelName"]
        self.serial_number = device_info["serialNumber"]

    async def async_update_power(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update power status of device."""
        if self.use_avr_2016_update is True:
            await self.async_update_power_appcommand(
                global_update=global_update, cache_id=cache_id)
        elif self.use_avr_2016_update is False:
            await self.async_update_power_status_xml(cache_id=cache_id)
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set")

    async def async_update_power_appcommand(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update power status from AppCommand.xml."""
        power_appcommand = AppCommands.GetAllZonePowerStatus
        try:
            if global_update:
                xml = await self.api.async_get_global_appcommand(
                    cache_id=cache_id)
            else:
                xml = await self.api.async_post_appcommand(
                    self.urls.appcommand, tuple(power_appcommand),
                    cache_id=cache_id)
        except AvrRequestError as err:
            _LOGGER.debug(
                "Error when getting power status", exc_info=err)
            raise

        # Extract relevant information
        zone = self.get_own_zone()

        # Search for power tag
        power_tag = xml.find("./cmd[@{attribute}='{cmd}']/{zone}".format(
            attribute=APPCOMMAND_CMD_TEXT,
            cmd=power_appcommand.cmd_text,
            zone=zone))

        if power_tag is None:
            raise AvrProcessingError(
                "Power attribute of zone {} not found on update".format(
                    self.zone))

        self._power = power_tag.text

    async def async_update_power_status_xml(
            self,
            cache_id: Optional[Hashable] = None):
        """Update power status from status xml."""
        # URLs to be scanned
        urls = [self.urls.status]
        if self.zone == MAIN_ZONE:
            urls.append(self.urls.mainzone)
        else:
            urls.append("{}?ZoneName={}".format(self.urls.mainzone, self.zone))
        # Tags in XML which might contain information about zones power status
        # ordered by their priority
        tags = ["./ZonePower/value", "./Power/value"]

        for tag in tags:
            for url in urls:
                try:
                    xml = await self.api.async_get_xml(
                        url, cache_id=cache_id)
                except AvrRequestError as err:
                    _LOGGER.debug(
                        "Error when getting power status from url %s", url,
                        exc_info=err)
                    continue

                # Search for power tag
                power_tag = xml.find(tag)
                if power_tag is not None and power_tag.text is not None:
                    self._power = power_tag.text
                    return

        raise AvrProcessingError(
            "Power attribute of zone {} not found on update".format(self.zone))

    ##############
    # Properties #
    ##############
    @property
    def power(self) -> Optional[str]:
        """
        Return the power state of the device.

        Possible values are: "ON", "STANDBY" and "OFF"
        """
        return self._power

    ##########
    # Setter #
    ##########

    async def async_power_on(self) -> None:
        """Turn on receiver via HTTP get command."""
        await self.api.async_get_command(self.urls.command_power_on)

    async def async_power_off(self) -> None:
        """Turn off receiver via HTTP get command."""
        await self.api.async_get_command(self.urls.command_power_standby)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRFoundation:
    """
    Implements the foundation class of DenonAVR functions.

    All functions like the receiver, zones, sound modes, media settings, tone
    control use this class.
    """

    _device: DenonAVRDeviceInfo = attr.ib(
        validator=attr.validators.instance_of(DenonAVRDeviceInfo),
        default=attr.Factory(DenonAVRDeviceInfo),
        kw_only=True)
    _is_setup: bool = attr.ib(converter=bool, default=False, init=False)

    async def async_update_attrs_appcommand(
            self,
            update_attrs: Dict[AppCommandCmd, None],
            appcommand0300: bool = False,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None,
            ignore_missing_response: bool = False):
        """Update attributes from AppCommand.xml."""
        # Copy that we do not accidently change the wrong dict
        update_attrs = deepcopy(update_attrs)
        # Collect tags for AppCommand.xml call
        tags = tuple(i for i in update_attrs.keys())
        # Execute call
        try:
            if global_update:
                xml = await self._device.api.async_get_global_appcommand(
                    appcommand0300=appcommand0300, cache_id=cache_id)
            else:
                # Determine endpoint
                if appcommand0300:
                    url = self._device.urls.appcommand0300
                else:
                    url = self._device.urls.appcommand
                xml = await self._device.api.async_post_appcommand(
                    url, tags, cache_id=cache_id)
        except AvrRequestError as err:
            _LOGGER.debug(
                "Error when getting status update", exc_info=err)
            raise

        # Extract relevant information
        zone = self._device.get_own_zone()

        attrs = deepcopy(update_attrs)
        for app_command in attrs.keys():
            search_strings = self.create_appcommand_search_strings(
                app_command, zone)
            start = 0
            success = 0
            for i, pattern in enumerate(app_command.response_pattern):
                try:
                    start += 1
                    # Check if attribute exists
                    getattr(self, pattern.update_attribute)
                    # Set new value either from XML attribute or text
                    if pattern.get_xml_attribute is not None:
                        set_value = xml.find(
                            search_strings[i]).get(pattern.get_xml_attribute)
                    else:
                        set_value = xml.find(search_strings[i]).text

                    setattr(
                        self,
                        pattern.update_attribute,
                        set_value)
                    success += 1

                    _LOGGER.debug(
                        "Changing variable %s to value %s",
                        pattern.update_attribute, set_value)

                except (AttributeError, IndexError) as err:
                    _LOGGER.debug(
                        "Failed updating attribute %s for zone %s",
                        pattern.update_attribute, self._device.zone,
                        exc_info=err)

            if start == success:
                # Done
                update_attrs.pop(app_command, None)

        # Check if each attribute was updated
        if update_attrs and ignore_missing_response is False:
            raise AvrProcessingError(
                "Some attributes of zone {} not found on update: {}".format(
                    self._device.zone, update_attrs))
        if update_attrs and ignore_missing_response is True:
            _LOGGER.debug(
                "Some attributes of zone %s not found on update: %s",
                self._device.zone, update_attrs)

    async def async_update_attrs_status_xml(
            self,
            update_attrs: Dict[str, str],
            urls: List[str],
            cache_id: Optional[Hashable] = None,
            ignore_missing_response: bool = False):
        """
        Update attributes from status xml.

        # URLs to be scanned. Like:
        urls = [self._device.urls.status, self._device.urls.mainzone]

        # Variables with their tags to be updated.
        # Key = Variable, Value = XML tag Like:
        update_attrs = {"power": "./Power/value"}
        """
        # Copy that we do not accidently change the wrong dict
        update_attrs = deepcopy(update_attrs)

        for url in urls:
            try:
                xml = await self._device.api.async_get_xml(
                    url, cache_id=cache_id)
            except AvrRequestError as err:
                _LOGGER.debug(
                    "Error when getting status update from url %s", url,
                    exc_info=err)
                continue
            attrs = deepcopy(update_attrs)
            for name, tag in attrs.items():
                try:
                    # Check if attribute exists
                    getattr(self, name)
                    # Set new value
                    setattr(self, name, xml.find(tag).text)
                    # Done
                    update_attrs.pop(name, None)

                    _LOGGER.debug(
                        "Changing variable %s to value %s", name,
                        xml.find(tag).text)

                except (AttributeError, IndexError) as err:
                    _LOGGER.debug(
                        "Failed updating attribute %s for zone %s", name,
                        self._device.zone, exc_info=err)

            # All done, no need for continuing
            if not update_attrs:
                break

        # Check if each attribute was updated
        if update_attrs and ignore_missing_response is False:
            raise AvrProcessingError(
                "Some attributes of zone {} not found on update: {}".format(
                    self._device.zone, update_attrs))

    @staticmethod
    def create_appcommand_search_strings(
            app_command_cmd: AppCommandCmd, zone: str) -> List[str]:
        """Create search pattern for AppCommand(0300).xml response."""
        result = []

        for resp in app_command_cmd.response_pattern:
            string = "./cmd"
            # Text of cmd tag in query was added as attribute to response
            if app_command_cmd.cmd_text:
                string = string + "[@{}='{}']".format(
                    APPCOMMAND_CMD_TEXT, app_command_cmd.cmd_text)
            # Text of name tag in query was added as attribute to response
            if app_command_cmd.name:
                string = string + "[@{}='{}']".format(
                    APPCOMMAND_NAME, app_command_cmd.name)
            # Some results include a zone tag
            if resp.add_zone:
                string = string + "/{}".format(zone)
            # Suffix like /status, /volume
            string = string + resp.suffix

            # A complete search string with all strributes set looks like
            # ./cmd[@cmd_text={cmd_text}][@name={name}]/zone1/volume
            result.append(string)

        return result


def set_api_host(
        instance: DenonAVRFoundation,
        attribute: attr.Attribute,
        value: str) -> str:
    """Change API host on host changes too."""
    # First change _device.api.host then return value
    # pylint: disable=protected-access
    instance._device.api.host = value
    instance._device.telnet_api.host = value
    return value


def set_api_timeout(
        instance: DenonAVRFoundation,
        attribute: attr.Attribute,
        value: float) -> float:
    """Change API timeout on timeout changes too."""
    # First change _device.api.host then return value
    timeout = httpx.Timeout(value, read=max(value, 15.0))
    # pylint: disable=protected-access
    instance._device.api.timeout = timeout
    instance._device.telnet_api.timeout = value
    return value


def convert_string_int_bool(value: str) -> bool:
    """Convert an integer from string format to bool."""
    if value is None:
        return None
    return bool(int(value))
