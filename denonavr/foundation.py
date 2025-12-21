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
from collections.abc import Hashable
from copy import deepcopy
from typing import Callable, Dict, List, Literal, Optional, Union, get_args

import attr

from .api import DenonAVRApi, DenonAVRTelnetApi
from .appcommand import AppCommandCmd, AppCommands
from .const import (
    APPCOMMAND_CMD_TEXT,
    APPCOMMAND_NAME,
    AUDIO_RESTORER_MAP,
    AUDIO_RESTORER_MAP_LABELS,
    AVR,
    AVR_X,
    AVR_X_2016,
    BLUETOOTH_OUTPUT_MAP_LABELS,
    BLUETOOTH_OUTPUT_MODES_MAP,
    CHANNEL_VOLUME_MAP,
    DENON_ATTR_SETATTR,
    DENONAVR_TELNET_COMMANDS,
    DENONAVR_URLS,
    DESCRIPTION_TYPES,
    DEVICEINFO_AVR_X_PATTERN,
    DEVICEINFO_COMMAPI_PATTERN,
    DIMMER_MODE_MAP,
    DIMMER_MODE_MAP_LABELS,
    ECO_MODE_MAP,
    ECO_MODE_MAP_LABELS,
    HDMI_OUTPUT_MAP,
    HDMI_OUTPUT_MAP_LABELS,
    ILLUMINATION_MAP,
    ILLUMINATION_MAP_LABELS,
    MAIN_ZONE,
    POWER_STATES,
    SETTINGS_MENU_STATES,
    VALID_RECEIVER_TYPES,
    VALID_ZONES,
    VIDEO_PROCESSING_MODES_MAP,
    VIDEO_PROCESSING_MODES_MAP_LABELS,
    ZONE2,
    ZONE2_TELNET_COMMANDS,
    ZONE2_URLS,
    ZONE3,
    ZONE3_TELNET_COMMANDS,
    ZONE3_URLS,
    AudioRestorers,
    AutoStandbys,
    BluetoothOutputModes,
    DimmerModes,
    EcoModes,
    HDMIAudioDecodes,
    HDMIOutputs,
    Illuminations,
    InputModes,
    PanelLocks,
    ReceiverType,
    ReceiverURLs,
    RoomSizes,
    TelnetCommands,
    TransducerLPFs,
    VideoProcessingModes,
)
from .exceptions import (
    AvrCommandError,
    AvrForbiddenError,
    AvrIncompleteResponseError,
    AvrNetworkError,
    AvrProcessingError,
    AvrRequestError,
    AvrTimoutError,
)
from .ssdp import evaluate_scpd_xml

_LOGGER = logging.getLogger(__name__)


def convert_on_off_bool(value: str) -> Optional[bool]:
    """Convert a ON/OFF string to bool."""
    if value is None:
        return None
    if value.lower() == "on":
        return True
    if value.lower() == "off":
        return False
    return None


def convert_on_off_bool_str(value: str) -> Optional[Union[bool, str]]:
    """Convert a ON/OFF string to bool with fallback to raw value."""
    val = convert_on_off_bool(value)
    if val is not None:
        return val

    return value


def convert_string_int(value: Union[str, bool]) -> Optional[int | str]:
    """Convert an integer or string to itself."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    return int(value)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRDeviceInfo:
    """Implements a class with device information of the receiver."""

    api: DenonAVRApi = attr.ib(
        validator=attr.validators.instance_of(DenonAVRApi),
        default=attr.Factory(DenonAVRApi),
        kw_only=True,
    )
    telnet_api: DenonAVRTelnetApi = attr.ib(
        validator=attr.validators.instance_of(DenonAVRTelnetApi),
        default=attr.Factory(DenonAVRTelnetApi),
        kw_only=True,
    )
    receiver: Optional[ReceiverType] = attr.ib(
        validator=attr.validators.optional(attr.validators.in_(VALID_RECEIVER_TYPES)),
        default=None,
    )
    telnet_commands: TelnetCommands = attr.ib(
        validator=attr.validators.instance_of(TelnetCommands), init=False
    )
    urls: ReceiverURLs = attr.ib(
        validator=attr.validators.instance_of(ReceiverURLs), init=False
    )
    zone: str = attr.ib(
        validator=attr.validators.in_(VALID_ZONES), default=MAIN_ZONE, kw_only=True
    )
    friendly_name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    manufacturer: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    model_name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    serial_number: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    use_avr_2016_update: Optional[bool] = attr.ib(
        converter=attr.converters.optional(bool), default=None
    )
    _power: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _settings_menu: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _dimmer: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _dimmer_modes = get_args(DimmerModes)
    _auto_standby: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _auto_standbys = get_args(AutoStandbys)
    _sleep: Optional[Union[str, int]] = attr.ib(
        converter=attr.converters.optional(convert_string_int), default=None
    )
    _delay: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )
    _eco_mode: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _eco_modes = get_args(EcoModes)
    _hdmi_output: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _hdmi_outputs = get_args(HDMIOutputs)
    _hdmi_audio_decode: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _hdmi_audio_decodes = get_args(HDMIAudioDecodes)
    _video_processing_mode: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _video_processing_modes = get_args(VideoProcessingModes)
    _tactile_transducer: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _tactile_transducer_level: Optional[float] = attr.ib(
        converter=attr.converters.optional(float), default=None
    )
    _tactile_transducer_lpf: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _tactile_transducer_lpfs = get_args(TransducerLPFs)
    _room_size: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _room_sizes = get_args(RoomSizes)
    _triggers: Optional[Dict[int, str]] = attr.ib(default=None)
    _speaker_preset: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )
    _bt_transmitter: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _bt_output_mode: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _bt_output_modes = get_args(BluetoothOutputModes)
    _delay_time: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )
    _audio_restorer: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _audio_restorers = get_args(AudioRestorers)
    _panel_locks = get_args(PanelLocks)
    _graphic_eq: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _headphone_eq: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _illumination: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _illuminations = get_args(Illuminations)
    _auto_lip_sync: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_on_off_bool), default=None
    )
    _input_modes = get_args(InputModes)
    _is_setup: bool = attr.ib(converter=bool, default=False, init=False)
    _allow_recovery: bool = attr.ib(converter=bool, default=True, init=True)
    _setup_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))
    _ps_handlers: Dict[str, Callable[[str], None]] = attr.ib(factory=dict, init=False)
    _ss_handlers: Dict[str, Callable[[str], None]] = attr.ib(factory=dict, init=False)
    _vs_handlers: Dict[str, Callable[[str], None]] = attr.ib(factory=dict, init=False)

    def __attrs_post_init__(self) -> None:
        """Initialize special attributes and callbacks."""
        # URLs depending from value of self.zone attribute
        if self.zone == MAIN_ZONE:
            self.telnet_commands = DENONAVR_TELNET_COMMANDS
            self.urls = DENONAVR_URLS
        elif self.zone == ZONE2:
            self.telnet_commands = ZONE2_TELNET_COMMANDS
            self.urls = ZONE2_URLS
        elif self.zone == ZONE3:
            self.telnet_commands = ZONE3_TELNET_COMMANDS
            self.urls = ZONE3_URLS
        else:
            raise ValueError(f"Invalid zone {self.zone}")

        self._ps_handlers: Dict[str, Callable[[str], None]] = {
            # Note order, 'DELAY' must be before 'DEL' because of startswith check
            "DELAY": self._delay_callback,
            "DEL": self._delay_time_callback,
            "RSZ": self._room_size_callback,
            "RSTR": self._audio_restorer_callback,
            "GEQ": self._graphic_eq_callback,
            "HEQ": self._headphone_eq_callback,
        }

        self._ss_handlers: Dict[str, Callable[[str], None]] = {
            "TTR": self._tactile_transducer_callback,
            "HOS": self._auto_lip_sync_callback,
        }

        self._vs_handlers: Dict[str, Callable[[str], None]] = {
            "MONI": self._hdmi_output_callback,
            "AUDIO": self._hdmi_audio_decode_callback,
            "VPM": self._video_processing_mode_callback,
        }

    def _power_callback(self, zone: str, _event: str, parameter: str) -> None:
        """Handle a power change event."""
        if self.zone == zone and parameter in POWER_STATES:
            self._power = parameter

    def _settings_menu_callback(self, _zone: str, event: str, parameter: str) -> None:
        """Handle a settings menu event."""
        if (
            event == "MN"
            and parameter.startswith("MEN")
            and (value := parameter[4:]) in SETTINGS_MENU_STATES
        ):
            self._settings_menu = value

    def _dimmer_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a dimmer change event."""
        if (value := parameter[1:]) in DIMMER_MODE_MAP_LABELS:
            self._dimmer = DIMMER_MODE_MAP_LABELS[value]

    def _auto_standby_callback(self, zone: str, _event: str, parameter: str) -> None:
        """Handle an auto standby change event."""
        if zone == "Main":
            self._auto_standby = parameter

    def _auto_sleep_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a sleep change event."""
        if parameter == "OFF":
            self._sleep = parameter
        else:
            self._sleep = int(parameter)

    def _room_size_callback(self, parameter: str) -> None:
        """Handle a room size change event."""
        self._room_size = parameter[4:]

    def _trigger_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a trigger change event."""
        values = parameter.split()
        if len(values) != 2:
            return

        if self._triggers is None:
            self._triggers = {}

        self._triggers[int(values[0])] = values[1]

    def _vs_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a VS change event."""
        for prefix, handler in self._vs_handlers.items():
            if parameter.startswith(prefix):
                handler(parameter)
                return

    def _ps_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a PS change event."""
        for prefix, handler in self._ps_handlers.items():
            if parameter.startswith(prefix):
                handler(parameter)
                return

    def _delay_callback(self, parameter: str) -> None:
        """Handle a delay change event."""
        if parameter.startswith("DELAY"):
            self._delay = int(parameter[6:])

    def _eco_mode_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle an Eco-mode change event."""
        if parameter in ECO_MODE_MAP_LABELS:
            self._eco_mode = ECO_MODE_MAP_LABELS[parameter]

    def _hdmi_output_callback(self, parameter: str) -> None:
        """Handle a HDMI output change event."""
        self._hdmi_output = HDMI_OUTPUT_MAP_LABELS[parameter]

    def _hdmi_audio_decode_callback(self, parameter: str) -> None:
        """Handle a HDMI Audio Decode mode change event."""
        self._hdmi_audio_decode = parameter[6:]

    def _video_processing_mode_callback(self, parameter: str) -> None:
        """Handle a Video Processing Mode change event."""
        self._video_processing_mode = VIDEO_PROCESSING_MODES_MAP_LABELS[parameter[3:]]

    def _ss_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a SS change event."""
        for prefix, handler in self._ss_handlers.items():
            if parameter.startswith(prefix):
                handler(parameter)
                return

    def _tactile_transducer_callback(self, parameter: str) -> None:
        """Handle a tactile transducer change event."""
        key_value = parameter.split()
        if len(key_value) != 2:
            return

        key = key_value[0]
        value = key_value[1]
        if value == "END":
            return

        if key == "TTR":
            self._tactile_transducer = value
        elif key == "TTRLEV":
            self._tactile_transducer_level = CHANNEL_VOLUME_MAP[value]
        elif key == "TTRLPF":
            self._tactile_transducer_lpf = f"{int(value)} Hz"

    def _speaker_preset_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a speaker preset change event."""
        if parameter.startswith("PR"):
            self._speaker_preset = int(parameter[3:])

    def _bt_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle a Bluetooth change event."""
        key_value = parameter.split()
        if len(key_value) != 2:
            return

        if key_value[0] != "TX":
            return

        value = key_value[1]
        if value in ("ON", "OFF"):
            self._bt_transmitter = value
        else:
            self._bt_output_mode = BLUETOOTH_OUTPUT_MAP_LABELS[value]

    def _delay_time_callback(self, parameter: str) -> None:
        """Handle a delay time change event."""
        # do not match "DELAY" as it's another event
        if parameter.startswith("DELAY"):
            return

        self._delay_time = int(parameter[4:])

    def _audio_restorer_callback(self, parameter: str) -> None:
        """Handle an audio restorer change event."""
        self._audio_restorer = AUDIO_RESTORER_MAP_LABELS[parameter[5:]]

    def _graphic_eq_callback(self, parameter: str) -> None:
        """Handle a Graphic EQ change event."""
        self._graphic_eq = parameter[4:]

    def _headphone_eq_callback(self, parameter: str) -> None:
        """Handle a Headphone EQ change event."""
        if parameter.startswith("HEQ"):
            self._headphone_eq = parameter[4:]

    def _illumination_callback(self, zone: str, event: str, parameter: str) -> None:
        """Handle an illumination change event."""
        if parameter.startswith("ILL"):
            self._illumination = ILLUMINATION_MAP_LABELS[parameter[4:]]

    def _auto_lip_sync_callback(self, parameter: str) -> None:
        """Handle a auto lip sync change event."""
        if parameter.startswith("HOSALS"):
            self._auto_lip_sync = parameter[5:]
        elif parameter.startswith("HOS"):
            self._auto_lip_sync = parameter[4:]

    def get_own_zone(self) -> str:
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
            _LOGGER.debug("Starting device setup")
            # Reduce read timeout during receiver identification
            # deviceinfo endpoint takes very long to return 404
            read_timeout = self.api.read_timeout
            self.api.read_timeout = self.api.timeout
            try:
                _LOGGER.debug("Identifying receiver")
                await self.async_identify_receiver()
                _LOGGER.debug("Getting device info")
                await self.async_get_device_info()
            finally:
                self.api.read_timeout = read_timeout
            _LOGGER.debug("Identifying update method")
            await self.async_identify_update_method()

            # Add tags for a potential AppCommand.xml update
            self.api.add_appcommand_update_tag(AppCommands.GetAllZonePowerStatus)

            self._register_callbacks()

            self._is_setup = True
            _LOGGER.debug("Finished device setup")

    def _register_callbacks(self):
        power_event = "ZM"
        if self.zone == ZONE2:
            power_event = "Z2"
        elif self.zone == ZONE3:
            power_event = "Z3"
        self.telnet_api.register_callback(power_event, self._power_callback)

        self.telnet_api.register_callback("MN", self._settings_menu_callback)
        self.telnet_api.register_callback("DIM", self._dimmer_callback)
        self.telnet_api.register_callback("ECO", self._eco_mode_callback)
        self.telnet_api.register_callback("VS", self._vs_callback)
        self.telnet_api.register_callback("SS", self._ss_callback)
        self.telnet_api.register_callback("STBY", self._auto_standby_callback)
        self.telnet_api.register_callback("SLP", self._auto_sleep_callback)
        self.telnet_api.register_callback("TR", self._trigger_callback)
        self.telnet_api.register_callback("SP", self._speaker_preset_callback)
        self.telnet_api.register_callback("BT", self._bt_callback)
        self.telnet_api.register_callback("PS", self._ps_callback)
        if not self.is_denon:
            self.telnet_api.register_callback("ILB", self._illumination_callback)

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update status asynchronously."""
        _LOGGER.debug("Starting device update")
        # Ensure instance is setup before updating
        if not self._is_setup:
            await self.async_setup()

        # Update power status
        await self.async_update_power(global_update=global_update, cache_id=cache_id)
        _LOGGER.debug("Finished device update")

    async def async_identify_receiver(self) -> None:
        """Identify receiver asynchronously."""
        # Test Deviceinfo.xml if receiver is an AVR-X with port 80 for pre 2016
        # devices and port 8080 devices 2016 and later
        # 2016 models has also some of the XML but not all, try first 2016
        r_types = [AVR_X_2016, AVR_X, AVR]

        async def test_receiver_type(r_type):
            """Test a single receiver type."""
            original_timeout = self.api.timeout
            try:
                # Use shorter timeout for faster identification
                self.api.timeout = min(1.0, original_timeout)
                self.api.port = r_type.port

                # This XML is needed to get the sources of the receiver
                # Deviceinfo.xml is static and can be cached for the whole time
                xml = await self.api.async_get_xml(
                    self.urls.deviceinfo, cache_id=id(self)
                )

                # Check if this is the correct receiver type
                if r_type != AVR:  # AVR is the fallback, always "matches"
                    is_avr_x = self._is_avr_x(xml)
                    if not is_avr_x:
                        return None

                return r_type

            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error on port %s when identifying receiver: %s",
                    r_type.port,
                    err,
                )
                return None
            except AvrRequestError as err:
                _LOGGER.debug(
                    (
                        "Request error on port %s when identifying receiver, "
                        "device is not a %s receiver: %s"
                    ),
                    r_type.port,
                    r_type.type,
                    err,
                )
                return None
            finally:
                self.api.timeout = original_timeout

        tasks = [asyncio.create_task(test_receiver_type(r_type)) for r_type in r_types]

        try:  # pylint: disable=R1702
            for completed_task in asyncio.as_completed(tasks):
                try:
                    result = await completed_task
                    if result is not None:
                        # Success! Cancel remaining tasks immediately
                        for task in tasks:
                            if not task.done():
                                task.cancel()

                        r_type = result
                        self.receiver = r_type
                        self.api.port = r_type.port
                        _LOGGER.info(
                            "Identified %s receiver using port %s",
                            r_type.type,
                            r_type.port,
                        )
                        return
                except Exception as e:  # pylint: disable=W0718
                    _LOGGER.debug("Task failed with exception: %s", e)
                    continue

            # If we get here, no tasks succeeded
            # Fall back to AVR type
            self.receiver = AVR
            self.api.port = AVR.port
            _LOGGER.info(
                "Identified %s receiver using port %s (fallback)",
                AVR.type,
                AVR.port,
            )

        finally:
            # Ensure all tasks are cancelled if we exit early
            for task in tasks:
                if not task.done():
                    task.cancel()

            # Wait for all cancelled tasks to complete cleanup
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def _is_avr_x(deviceinfo: ET.Element) -> bool:
        """Evaluate Deviceinfo.xml if the device is an AVR-X device."""
        # First test by CommApiVers
        try:
            if bool(
                DEVICEINFO_COMMAPI_PATTERN.search(deviceinfo.find("CommApiVers").text)
                is not None
            ):
                # receiver found , return True
                return True
        except AttributeError:
            # AttributeError occurs when ModelName tag is not found.
            # In this case there is no AVR-X device
            pass

        # if first test did not find AVR-X device, check by model name
        try:
            if bool(
                DEVICEINFO_AVR_X_PATTERN.search(deviceinfo.find("ModelName").text)
                is not None
            ):
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
                    self.urls.appcommand, (AppCommands.GetFriendlyName,)
                )
            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error when identifying update method: %s", err
                )
                raise
            except AvrRequestError as err:
                _LOGGER.debug("Request error when identifying update method: %s", err)
                self.use_avr_2016_update = False
                _LOGGER.info("AVR-X device, AppCommand.xml interface not supported")
            else:
                self.use_avr_2016_update = True
                _LOGGER.info("AVR-X device, using AppCommand.xml interface")
                self._set_friendly_name(xml)

        if not self.use_avr_2016_update:
            try:
                xml = await self.api.async_get_xml(self.urls.mainzone)
            except (AvrTimoutError, AvrNetworkError) as err:
                _LOGGER.debug(
                    "Connection error when identifying update method: %s", err
                )
                raise
            except AvrRequestError as err:
                _LOGGER.debug("Request error getting friendly name: %s", err)
                _LOGGER.info(
                    "Receiver name could not be determined. Using standard"
                    " name: Denon AVR"
                )
                if self.friendly_name is None:
                    self.friendly_name = "Denon AVR"
            else:
                self._set_friendly_name(xml)

    async def async_verify_avr_2016_update_method(
        self, *, cache_id: Hashable = None
    ) -> None:
        """Verify if avr 2016 update method is working."""
        # Nothing to do if Appcommand.xml interface is not supported
        if self._is_setup and not self.use_avr_2016_update:
            return

        try:
            # Result is cached that it can be reused during update
            await self.api.async_get_global_appcommand(cache_id=cache_id)
        except (AvrTimoutError, AvrNetworkError) as err:
            _LOGGER.debug("Connection error when verifying update method: %s", err)
            raise
        except AvrForbiddenError:
            # Recovery in case receiver changes port from 80 to 8080 which
            # might happen at Denon AVR-X 2016 receivers
            if self._allow_recovery:
                self._allow_recovery = False
                _LOGGER.warning(
                    "AppCommand.xml returns HTTP status 403. Running setup"
                    " again once to check if receiver interface switched "
                    "ports"
                )
                self._is_setup = False
                await self.async_setup()
                await self.async_verify_avr_2016_update_method(cache_id=cache_id)
            else:
                raise
        except AvrIncompleteResponseError as err:
            _LOGGER.debug("Request error when verifying update method: %s", err)
            # Only AVR_X devices support both interfaces
            if self.receiver == AVR_X:
                _LOGGER.warning(
                    "Error verifying Appcommand.xml update method, it returns "
                    "an incomplete result set. Deactivating the interface"
                )
                self.use_avr_2016_update = False
        else:
            if not self._allow_recovery:
                _LOGGER.info("AppCommand.xml recovered from HTTP status 403 error")
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
            _LOGGER.warning("No FriendlyName found, using standard name: Denon AVR")
            self.friendly_name = "Denon AVR"

    async def async_get_device_info(self) -> None:
        """Get device information."""
        port = DESCRIPTION_TYPES[self.receiver.type].port
        command = DESCRIPTION_TYPES[self.receiver.type].url
        url = f"http://{self.api.host}:{port}{command}"

        device_info = None
        try:
            res = await self.api.async_get(
                command, port=port, record_latency=False, skip_rate_limiter=True
            )
        except AvrTimoutError as err:
            _LOGGER.debug("Timeout when getting device info: %s", err)
            raise
        except AvrNetworkError as err:
            _LOGGER.debug("Network error getting device info: %s", err)
            raise
        except AvrRequestError as err:
            _LOGGER.error(
                (
                    "During DenonAVR device identification, when trying to request"
                    " %s the following error occurred: %s"
                ),
                url,
                err,
            )
        else:
            device_info = evaluate_scpd_xml(url, res.text)

        if device_info is None:
            self.manufacturer = "Denon"
            self.telnet_api.is_denon = self.is_denon
            self.model_name = "Unknown"
            self.serial_number = None
            _LOGGER.warning(
                (
                    "Unable to get device information of host %s, Device might be "
                    "in a corrupted state. Continuing without device information. "
                    "Disconnect and reconnect power to the device and try again."
                ),
                self.api.host,
            )
            return

        if self.friendly_name is None and "friendlyName" in device_info:
            self.friendly_name = device_info["friendlyName"]
        self.manufacturer = device_info["manufacturer"]
        self.telnet_api.is_denon = self.is_denon
        self.model_name = device_info["modelName"]
        self.serial_number = device_info["serialNumber"]

    async def async_update_power(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update power status of device."""
        if self.use_avr_2016_update is None:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set"
            )

        if self.use_avr_2016_update:
            await self.async_update_power_appcommand(
                global_update=global_update, cache_id=cache_id
            )
        else:
            await self.async_update_power_status_xml(cache_id=cache_id)

    async def async_update_power_appcommand(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update power status from AppCommand.xml."""
        power_appcommand = AppCommands.GetAllZonePowerStatus
        try:
            if global_update:
                xml = await self.api.async_get_global_appcommand(cache_id=cache_id)
            else:
                xml = await self.api.async_post_appcommand(
                    self.urls.appcommand, tuple(power_appcommand), cache_id=cache_id
                )
        except AvrRequestError as err:
            _LOGGER.debug("Error when getting power status: %s", err)
            raise

        # Extract relevant information
        zone = self.get_own_zone()

        # Search for power tag
        power_tag = xml.find(
            f"./cmd[@{APPCOMMAND_CMD_TEXT}='{power_appcommand.cmd_text}']/{zone}"
        )

        if power_tag is None:
            raise AvrProcessingError(
                f"Power attribute of zone {self.zone} not found on update"
            )

        self._power = power_tag.text

    async def async_update_power_status_xml(
        self, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update power status from status xml."""
        # URLs to be scanned
        urls = [self.urls.status]
        if self.zone == MAIN_ZONE:
            urls.append(self.urls.mainzone)
        else:
            urls.append(f"{self.urls.mainzone}?ZoneName={self.zone}")
        # Tags in XML which might contain information about zones power status
        # ordered by their priority
        tags = ["./ZonePower/value", "./Power/value"]

        for tag in tags:
            for url in urls:
                try:
                    xml = await self.api.async_get_xml(url, cache_id=cache_id)
                except AvrRequestError as err:
                    _LOGGER.debug(
                        "Error when getting power status from url %s: %s", url, err
                    )
                    continue

                # Search for power tag
                power_tag = xml.find(tag)
                if power_tag is not None and power_tag.text is not None:
                    self._power = power_tag.text
                    return

        raise AvrProcessingError(
            f"Power attribute of zone {self.zone} not found on update"
        )

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

    @property
    def settings_menu(self) -> Optional[bool]:
        """
        Returns the settings menu state of the device.

        Only available if using Telnet.
        """
        return self._settings_menu

    @property
    def dimmer(self) -> Optional[str]:
        """
        Returns the dimmer state of the device.

        Only available if using Telnet.

        Possible values are: "Off", "Dark", "Dim" and "Bright"
        """
        return self._dimmer

    @property
    def auto_standby(self) -> Optional[str]:
        """
        Return the auto-standby state of the device.

        Only available if using Telnet.

        Possible values are: "OFF", "15M", "30M", "60M"
        """
        return self._auto_standby

    @property
    def sleep(self) -> Optional[Union[str, int]]:
        """
        Return the sleep timer for the device.

        Only available if using Telnet.

        Possible values are: "OFF" and 1-120 (in minutes)
        """
        return self._sleep

    @property
    def delay(self) -> Optional[int]:
        """
        Return the audio delay for the device in ms.

        Only available if using Telnet.
        """
        return self._delay

    @property
    def eco_mode(self) -> Optional[str]:
        """
        Returns the eco-mode for the device.

        Only available if using Telnet.

        Possible values are: "Off", "On", "Auto"
        """
        return self._eco_mode

    @property
    def hdmi_output(self) -> Optional[str]:
        """
        Returns the HDMI-output for the device.

        Only available if using Telnet.

        Possible values are: "Auto", "HDMI1", "HDMI2"
        """
        return self._hdmi_output

    @property
    def hdmi_audio_decode(self) -> Optional[str]:
        """
        Returns the HDMI Audio Decode for the device.

        Only available if using Telnet.

        Possible values are: "AMP", "TV"
        """
        return self._hdmi_audio_decode

    @property
    def video_processing_mode(self) -> Optional[str]:
        """
        Return the video processing mode for the device.

        Only available if using Telnet.

        Possible values are: "Auto", "Game", "Movie", "Bypass"
        """
        return self._video_processing_mode

    @property
    def tactile_transducer(self) -> Optional[str]:
        """
        Return the tactile transducer state of the device.

        Only available if using Telnet.
        """
        return self._tactile_transducer

    @property
    def tactile_transducer_level(self) -> Optional[float]:
        """
        Return the tactile transducer level in dB.

        Only available if using Telnet.
        """
        return self._tactile_transducer_level

    @property
    def tactile_transducer_lpf(self) -> Optional[str]:
        """
        Return the tactile transducer low pass filter frequency.

        Only available if using Telnet.
        """
        return self._tactile_transducer_lpf

    @property
    def room_size(self) -> Optional[str]:
        """
        Return the room size for the device.

        Only available if using Telnet.

        Possible values are: "S", "MS", "M", "ML", "L"
        """
        return self._room_size

    @property
    def triggers(self) -> Optional[Dict[int, str]]:
        """
        Return the triggers and their statuses for the device.

        Only available if using Telnet.
        """
        return self._triggers

    @property
    def speaker_preset(self) -> Optional[int]:
        """
        Return the speaker preset for the device.

        Only available if using Telnet.

        Possible values are: "1", "2"
        """
        return self._speaker_preset

    @property
    def bt_transmitter(self) -> Optional[bool]:
        """
        Return the Bluetooth transmitter state for the device.

        Only available if using Telnet.
        """
        return self._bt_transmitter

    @property
    def bt_output_mode(self) -> Optional[str]:
        """
        Return the Bluetooth output mode for the device.

        Only available if using Telnet.

        Possible values are: "Bluetooth + Speakers", "Bluetooth Only"
        """
        return self._bt_output_mode

    @property
    def delay_time(self) -> Optional[int]:
        """
        Return the delay time for the device in ms.

        Only available if using Telnet.
        """
        return self._delay_time

    @property
    def audio_restorer(self) -> Optional[str]:
        """
        Return the audio restorer for the device.

        Only available if using Telnet.

        Possible values are: "Off", "Low", "Medium", "High"
        """
        return self._audio_restorer

    @property
    def graphic_eq(self) -> Optional[bool]:
        """
        Return the Graphic EQ status for the device.

        Only available if using Telnet.
        """
        return self._graphic_eq

    @property
    def headphone_eq(self) -> Optional[bool]:
        """
        Return the Headphone EQ status for the device.

        Only available if using Telnet.
        """
        return self._headphone_eq

    @property
    def illumination(self) -> Optional[str]:
        """
        Return the illumination status for the device.

        Only available on Marantz devices and when using Telnet.

        Possible values are: "Auto", "Bright", "Dim", "Dark", "Off"
        """
        return self._illumination

    @property
    def auto_lip_sync(self) -> Optional[bool]:
        """
        Return the auto lip sync status for the device.

        Only available on Marantz devices and when using Telnet.
        """
        return self._auto_lip_sync

    @property
    def telnet_available(self) -> bool:
        """Return true if telnet is connected and healthy."""
        return self.telnet_api.connected and self.telnet_api.healthy

    @property
    def is_denon(self) -> bool:
        """Return true if the receiver is a Denon device."""
        if not self.manufacturer:
            return True  # Fallback to Denon
        return "denon" in self.manufacturer.lower()

    ##########
    # Getter #
    ##########

    def get_trigger(self, trigger: int) -> Optional[str]:
        """
        Return the status of a specific trigger.

        Only available if using Telnet.

        Valid trigger values are 1-3.
        """
        if trigger < 1 or trigger > 3:
            raise AvrCommandError(f"Invalid trigger {trigger}, must be between 1 and 3")

        if self._triggers is None:
            return None
        return self._triggers.get(trigger)

    ##########
    # Setter #
    ##########

    async def async_power_on(self) -> None:
        """Turn on receiver via HTTP get command."""
        if self._power == "ON":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_power_on
            )
        else:
            await self.api.async_get_command(self.urls.command_power_on)

    async def async_power_off(self) -> None:
        """Turn off receiver via HTTP get command."""
        if self._power == "OFF":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_power_standby
            )
        else:
            await self.api.async_get_command(self.urls.command_power_standby)

    async def async_cursor_up(self) -> None:
        """Cursor Up on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_cusor_up, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_cusor_up)

    async def async_cursor_down(self) -> None:
        """Cursor Down on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_cusor_down, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_cusor_down)

    async def async_cursor_left(self) -> None:
        """Cursor Left on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_cusor_left, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_cusor_left)

    async def async_cursor_right(self) -> None:
        """Cursor Right on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_cusor_right, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_cusor_right)

    async def async_cursor_enter(self) -> None:
        """Cursor Enter on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_cusor_enter, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_cusor_enter)

    async def async_back(self) -> None:
        """Back command on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_back, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_back)

    async def async_info(self) -> None:
        """Info OSD on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_info, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_info)

    async def async_options(self) -> None:
        """Options menu on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_options, skip_confirmation=True
            )
        else:
            await self.api.async_get_command(self.urls.command_options)

    async def async_settings_menu(self) -> None:
        """
        Options menu on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self._settings_menu:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_setup_close
            )
        else:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_setup_open
            )

    async def async_channel_level_adjust(self) -> None:
        """Toggle the channel level adjust menu on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_channel_level_adjust
            )
        else:
            await self.api.async_get_command(self.urls.command_channel_level_adjust)

    async def async_dimmer_toggle(self) -> None:
        """Toggle dimmer on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_dimmer_toggle
            )
        else:
            await self.api.async_get_command(self.urls.command_dimmer_toggle)

    async def async_dimmer(self, mode: DimmerModes) -> None:
        """Set dimmer mode on receiver via HTTP get command."""
        if mode not in self._dimmer_modes:
            raise AvrCommandError("Invalid dimmer mode")

        mapped_mode = DIMMER_MODE_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_dimmer_set.format(mode=mapped_mode)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_dimmer_set.format(mode=mapped_mode)
            )

    async def async_auto_standby(self, auto_standby: AutoStandbys) -> None:
        """Set auto standby on receiver via HTTP get command."""
        if auto_standby not in self._auto_standbys:
            raise AvrCommandError("Invalid Auto Standby mode")
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_auto_standby.format(mode=auto_standby)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_auto_standby.format(mode=auto_standby)
            )

    async def async_sleep(self, sleep: Union[Literal["OFF"], int]) -> None:
        """
        Set auto standby on receiver via HTTP get command.

        Valid sleep values are "OFF" and 1-120 (in minutes)
        """
        if sleep != "OFF" and sleep not in range(1, 120):
            raise AvrCommandError("Invalid sleep value")

        if self._sleep == sleep:
            return

        local_sleep = f"{sleep:03}" if isinstance(sleep, int) else sleep
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_sleep.format(value=local_sleep)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_sleep.format(value=local_sleep)
            )

    async def async_tactile_transducer_on(self) -> None:
        """Turn on tactile transducer on receiver via HTTP get command."""
        if self._tactile_transducer == "ON":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_tactile_transducer.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_tactile_transducer.format(mode="ON")
            )

    async def async_tactile_transducer_off(self) -> None:
        """Turn on tactile transducer on receiver via HTTP get command."""
        if self._tactile_transducer == "OFF":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_tactile_transducer.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_tactile_transducer.format(mode="OFF")
            )

    async def async_tactile_transducer_toggle(self) -> None:
        """
        Turn on tactile transducer on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self._tactile_transducer != "OFF":
            await self.async_tactile_transducer_off()
        else:
            await self.async_tactile_transducer_on()

    async def async_tactile_transducer_level_up(self) -> None:
        """Increase the transducer level on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_tactile_transducer_level.format(mode="UP")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_tactile_transducer_level.format(mode="UP")
            )

    async def async_tactile_transducer_level_down(self) -> None:
        """Decrease the transducer level on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_tactile_transducer_level.format(
                    mode="DOWN"
                )
            )
        else:
            await self.api.async_get_command(
                self.urls.command_tactile_transducer_level.format(mode="DOWN")
            )

    async def async_transducer_lpf(self, lpf: TransducerLPFs):
        """Set transducer low pass filter on receiver via HTTP get command."""
        if lpf not in self._tactile_transducer_lpfs:
            raise AvrCommandError("Invalid tactile transducer low pass filter")

        frequency = lpf.split()[0]
        if len(frequency) == 2:
            frequency = f"0{frequency}"
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_tactile_transducer_lpf.format(
                    frequency=frequency
                )
            )
        else:
            await self.api.async_get_command(
                self.urls.command_tactile_transducer_lpf.format(frequency=frequency)
            )

    async def async_room_size(self, room_size: RoomSizes) -> None:
        """Set room size on receiver via HTTP get command."""
        if room_size not in self._room_sizes:
            raise AvrCommandError("Invalid room size")

        if self._room_size == room_size:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_room_size.format(size=room_size)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_room_size.format(size=room_size)
            )

    async def async_trigger_on(self, trigger: int) -> None:
        """
        Set trigger to ON on receiver via HTTP get command.

        :param trigger: Trigger number to set to ON. Valid values are 1-3.
        """
        if trigger < 1 or trigger > 3:
            raise AvrCommandError("Trigger number must be between 1 and 3")

        if self._triggers.get(trigger, None) == "ON":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_trigger.format(number=trigger, mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_trigger.format(number=trigger, mode="ON")
            )

    async def async_trigger_off(self, trigger: int) -> None:
        """
        Set trigger to OFF on receiver via HTTP get command.

        :param trigger: Trigger number to set to OFF. Valid values are 1-3.
        """
        if trigger < 1 or trigger > 3:
            raise AvrCommandError("Trigger number must be between 1 and 3")

        if self._triggers.get(trigger, None) == "OFF":
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_trigger.format(number=trigger, mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_trigger.format(number=trigger, mode="OFF")
            )

    async def async_trigger_toggle(self, trigger: int) -> None:
        """
        Toggle trigger on receiver via HTTP get command.

        Only available if using Telnet.

        :param trigger: Trigger number to toggle. Valid values are 1-3.
        """
        if trigger < 1 or trigger > 3:
            raise AvrCommandError("Trigger number must be between 1 and 3")

        trigger_status = self._triggers.get(trigger)
        if trigger_status == "ON":
            await self.async_trigger_off(trigger)
        else:
            await self.async_trigger_on(trigger)

    async def async_quick_select_mode(self, quick_select_number: int) -> None:
        """
        Set quick select mode on receiver via HTTP get command.

        :param quick_select_number: Quick select number to set. Valid values are 1-5.
        """
        if quick_select_number not in range(1, 5):
            raise AvrCommandError("Quick select number must be between 1 and 5")

        if self.telnet_available:
            if self.is_denon:
                command = self.telnet_commands.command_quick_select_mode
            else:
                command = self.telnet_commands.command_smart_select_mode
            await self.telnet_api.async_send_commands(
                command.format(number=quick_select_number)
            )
        else:
            if self.is_denon:
                command = self.urls.command_quick_select_mode
            else:
                command = self.urls.command_smart_select_mode
            await self.api.async_get_command(command.format(number=quick_select_number))

    async def async_quick_select_memory(self, quick_select_number: int) -> None:
        """
        Set quick select memory on receiver via HTTP get command.

        :param quick_select_number: Quick select number to set. Valid values are 1-5.
        """
        if quick_select_number not in range(1, 5):
            raise AvrCommandError("Quick select number must be between 1 and 5")

        if self.telnet_available:
            if self.is_denon:
                command = self.telnet_commands.command_quick_select_memory
            else:
                command = self.telnet_commands.command_smart_select_memory
            await self.telnet_api.async_send_commands(
                command.format(number=quick_select_number)
            )
        else:
            if self.is_denon:
                command = self.urls.command_quick_select_memory
            else:
                command = self.urls.command_smart_select_memory
            await self.api.async_get_command(command.format(number=quick_select_number))

    async def async_delay_up(self) -> None:
        """Delay up on receiver via HTTP get command."""
        if self._delay == 500:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay_up
            )
        else:
            await self.api.async_get_command(self.urls.command_delay_up)

    async def async_delay_down(self) -> None:
        """Delay down on receiver via HTTP get command."""
        if self._delay == 0:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay_down
            )
        else:
            await self.api.async_get_command(self.urls.command_delay_down)

    async def async_delay(self, delay: int) -> None:
        """
        Set delay on receiver via HTTP get command.

        :param delay: Delay time in ms. Valid values are 0-500.
        """
        if delay < 0 or delay > 500:
            raise AvrCommandError("Invalid delay value")

        if self._delay == delay:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay.format(delay=delay)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_delay.format(delay=delay)
            )

    async def async_eco_mode(self, mode: EcoModes) -> None:
        """Set Eco mode."""
        if mode not in self._eco_modes:
            raise AvrCommandError("Invalid Eco mode")

        if self._eco_mode == mode:
            return

        mapped_mode = ECO_MODE_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_eco_mode.format(mode=mapped_mode)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_eco_mode.format(mode=mapped_mode)
            )

    async def async_hdmi_output(self, output: HDMIOutputs) -> None:
        """Set HDMI output."""
        if output not in self._hdmi_outputs:
            raise AvrCommandError("Invalid HDMI output mode")

        if self._hdmi_output == output:
            return

        mapped_output = HDMI_OUTPUT_MAP[output]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_hdmi_output.format(output=mapped_output)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_hdmi_output.format(output=mapped_output)
            )

    async def async_hdmi_audio_decode(self, mode: HDMIAudioDecodes) -> None:
        """Set HDMI Audio Decode mode on receiver via HTTP get command."""
        if mode not in self._hdmi_audio_decodes:
            raise AvrCommandError("Invalid HDMI Audio Decode mode")

        if self._hdmi_audio_decode == mode:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_hdmi_audio_decode.format(mode=mode)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_hdmi_audio_decode.format(mode=mode)
            )

    async def async_video_processing_mode(self, mode: VideoProcessingModes) -> None:
        """Set video processing mode on receiver via HTTP get command."""
        if mode not in self._video_processing_modes:
            raise AvrCommandError("Invalid video processing mode")

        if self._video_processing_mode == mode:
            return

        processing_mode = VIDEO_PROCESSING_MODES_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_video_processing_mode.format(
                    mode=processing_mode
                )
            )
        else:
            await self.api.async_get_command(
                self.urls.command_video_processing_mode.format(mode=processing_mode)
            )

    async def async_status(self) -> None:
        """Get status of receiver via HTTP get command."""
        if not self.is_denon:
            raise AvrCommandError("Status command is only supported for Denon devices")

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_status
            )
        else:
            await self.api.async_get_command(self.urls.command_status)

    async def async_system_reset(self) -> None:
        """DANGER! Reset the receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_system_reset
            )
        else:
            await self.api.async_get_command(self.urls.command_system_reset)

    async def async_network_restart(self) -> None:
        """Restart the network on the receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_network_restart
            )
        else:
            await self.api.async_get_command(self.urls.command_network_restart)

    async def async_speaker_preset(self, preset: int) -> None:
        """
        Set speaker preset on receiver via HTTP get command.

        Valid preset values are 1-2.
        """
        if preset < 1 or preset > 2:
            raise AvrCommandError("Speaker preset number must be 1 or 2")

        if self._speaker_preset == preset:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_speaker_preset.format(number=preset)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_speaker_preset.format(number=preset)
            )

    async def async_speaker_preset_toggle(self) -> None:
        """
        Toggle speaker preset on receiver via HTTP get command.

        Only available if using Telnet.
        """
        speaker_preset = 1 if self._speaker_preset == 2 else 2
        await self.async_speaker_preset(speaker_preset)

    async def async_bt_transmitter_on(
        self,
    ) -> None:
        """Turn on Bluetooth transmitter on receiver via HTTP get command."""
        if self._bt_transmitter:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_bluetooth_transmitter.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_bluetooth_transmitter.format(mode="ON")
            )

    async def async_bt_transmitter_off(
        self,
    ) -> None:
        """Turn off Bluetooth transmitter on receiver via HTTP get command."""
        if self._bt_transmitter is False:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_bluetooth_transmitter.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_bluetooth_transmitter.format(mode="OFF")
            )

    async def async_bt_transmitter_toggle(self) -> None:
        """
        Toggle Bluetooth transmitter mode on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self.bt_transmitter:
            await self.async_bt_transmitter_off()
        else:
            await self.async_bt_transmitter_on()

    async def async_bt_output_mode(self, mode: BluetoothOutputModes) -> None:
        """Set Bluetooth transmitter mode on receiver via HTTP get command."""
        if mode not in self._bt_output_modes:
            raise AvrCommandError("Invalid Bluetooth output mode")

        if self._bt_output_mode == mode:
            return

        mapped_mode = BLUETOOTH_OUTPUT_MODES_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_bluetooth_transmitter.format(
                    mode=mapped_mode
                )
            )
        else:
            await self.api.async_get_command(
                self.urls.command_bluetooth_transmitter.format(mode=mapped_mode)
            )

    async def async_bt_output_mode_toggle(self) -> None:
        """
        Toggle Bluetooth output mode on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self.bt_output_mode == "Bluetooth + Speakers":
            await self.async_bt_output_mode("Bluetooth Only")
        else:
            await self.async_bt_output_mode("Bluetooth + Speakers")

    async def async_delay_time_up(self) -> None:
        """Delay time up on receiver via HTTP get command."""
        if self._delay_time == 300:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay_time.format(value="UP")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_delay_time.format(value="UP")
            )

    async def async_delay_time_down(self) -> None:
        """Delay time down on receiver via HTTP get command."""
        if self._delay_time == 0:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay_time.format(value="DOWN")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_delay_time.format(value="DOWN")
            )

    async def async_delay_time(self, delay_time: int) -> None:
        """
        Set delay time on receiver via HTTP get command.

        :param delay_time: Delay time in ms. Valid values are 0-300.
        """
        if delay_time < 0 or delay_time > 300:
            raise AvrCommandError("Invalid delay time value")

        if self._delay_time == delay_time:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_delay_time.format(value=delay_time)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_delay_time.format(value=delay_time)
            )

    async def async_audio_restorer(self, mode: AudioRestorers):
        """Set audio restorer on receiver via HTTP get command."""
        if mode not in self._audio_restorers:
            raise AvrCommandError("Invalid audio restorer mode")

        if self._audio_restorer == mode:
            return

        mapped_mode = AUDIO_RESTORER_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_audio_restorer.format(mode=mapped_mode)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_audio_restorer.format(mode=mapped_mode)
            )

    async def async_remote_control_lock(self):
        """Set remote control lock on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_remote_control_lock.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_remote_control_lock.format(mode="ON")
            )

    async def async_remote_control_unlock(self):
        """Set remote control unlock on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_remote_control_lock.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_remote_control_lock.format(mode="OFF")
            )

    async def async_panel_lock(self, panel_lock_mode: PanelLocks):
        """Set panel lock on receiver via HTTP get command."""
        if panel_lock_mode not in self._panel_locks:
            raise AvrCommandError("Invalid panel lock mode")

        if self.telnet_available:
            if panel_lock_mode == "Panel":
                await self.telnet_api.async_send_commands(
                    self.telnet_commands.command_panel_lock.format(mode="ON")
                )
            else:
                await self.telnet_api.async_send_commands(
                    self.telnet_commands.command_panel_and_volume_lock
                )
        else:
            if panel_lock_mode == "Panel":
                await self.api.async_get_command(
                    self.urls.command_panel_lock.format(mode="ON")
                )
            else:
                await self.api.async_get_command(
                    self.urls.command_panel_and_volume_lock
                )

    async def async_panel_unlock(self):
        """Set panel unlock on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_panel_lock.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_panel_lock.format(mode="OFF")
            )

    async def async_graphic_eq_on(self) -> None:
        """Turn on Graphic EQ on receiver via HTTP get command."""
        if self._graphic_eq:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_graphic_eq.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_graphic_eq.format(mode="ON")
            )

    async def async_graphic_eq_off(self) -> None:
        """Turn off Graphic EQ on receiver via HTTP get command."""
        if self._graphic_eq is False:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_graphic_eq.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_graphic_eq.format(mode="OFF")
            )

    async def async_graphic_eq_toggle(self) -> None:
        """
        Toggle Graphic EQ on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self._graphic_eq:
            await self.async_graphic_eq_off()
        else:
            await self.async_graphic_eq_on()

    async def async_headphone_eq_on(self) -> None:
        """Turn on Headphone EQ on receiver via HTTP get command."""
        if self._headphone_eq:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_headphone_eq.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_headphone_eq.format(mode="ON")
            )

    async def async_headphone_eq_off(self) -> None:
        """Turn off Headphone EQ on receiver via HTTP get command."""
        if self._headphone_eq is False:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_headphone_eq.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_headphone_eq.format(mode="OFF")
            )

    async def async_headphone_eq_toggle(self) -> None:
        """
        Toggle Headphone EQ on receiver via HTTP get command.

        Only available if using Telnet.
        """
        if self._headphone_eq:
            await self.async_headphone_eq_off()
        else:
            await self.async_headphone_eq_on()

    async def async_hdmi_cec_on(self) -> None:
        """Turn on HDMI CEC on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_denon_hdmi_cec_on
                if self.is_denon
                else self.urls.command_marantz_hdmi_cec_on
            )
        else:
            await self.api.async_get_command(
                self.urls.command_denon_hdmi_cec_on
                if self.is_denon
                else self.urls.command_marantz_hdmi_cec_on
            )

    async def async_hdmi_cec_off(self) -> None:
        """Turn off HDMI CEC on receiver via HTTP get command."""
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_denon_hdmi_cec_off
                if self.is_denon
                else self.urls.command_marantz_hdmi_cec_off
            )
        else:
            await self.api.async_get_command(
                self.urls.command_denon_hdmi_cec_off
                if self.is_denon
                else self.urls.command_marantz_hdmi_cec_off
            )

    async def async_illumination(self, mode: Illuminations):
        """
        Set illumination mode on receiver via HTTP get command.

        Only available on Marantz devices.
        """
        if self.is_denon:
            raise AvrCommandError("Illumination is only available for Marantz devices")

        if mode not in self._illuminations:
            raise AvrCommandError("Invalid illumination mode")

        if self._illumination == mode:
            return

        mapped_mode = ILLUMINATION_MAP[mode]
        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_illumination.format(mode=mapped_mode)
            )
        else:
            await self.api.async_get_command(
                self.urls.command_illumination.format(mode=mapped_mode)
            )

    async def async_auto_lip_sync_on(self) -> None:
        """
        Turn on auto lip sync on receiver via HTTP get command.

        Only available on Marantz devices.
        """
        if self.is_denon:
            raise AvrCommandError("Auto lip sync is only available for Marantz devices")

        if self._auto_lip_sync:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_auto_lip_sync.format(mode="ON")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_auto_lip_sync.format(mode="ON")
            )

    async def async_auto_lip_sync_off(self) -> None:
        """
        Turn off auto lip sync on receiver via HTTP get command.

        Only available on Marantz devices.
        """
        if self.is_denon:
            raise AvrCommandError("Auto lip sync is only available for Marantz devices")

        if self._auto_lip_sync is False:
            return

        if self.telnet_available:
            await self.telnet_api.async_send_commands(
                self.telnet_commands.command_auto_lip_sync.format(mode="OFF")
            )
        else:
            await self.api.async_get_command(
                self.urls.command_auto_lip_sync.format(mode="OFF")
            )

    async def async_auto_lip_sync_toggle(self) -> None:
        """
        Toggle auto lip sync on receiver via HTTP get command.

        Only available on Marantz devices and when using Telnet.
        """
        if self.is_denon:
            raise AvrCommandError("Auto lip sync is only available for Marantz devices")

        if self._auto_lip_sync:
            await self.async_auto_lip_sync_off()
        else:
            await self.async_auto_lip_sync_on()

    async def async_page_up(self) -> None:
        """Page Up on receiver via HTTP get command."""
        if self.telnet_available:
            command = (
                self.telnet_commands.command_page_up_denon
                if self.is_denon
                else self.telnet_commands.command_page_up_marantz
            )
            await self.telnet_api.async_send_commands(command)
        else:
            command = (
                self.urls.command_page_up_denon
                if self.is_denon
                else self.urls.command_page_up_marantz
            )
            await self.api.async_get_command(command)

    async def async_page_down(self) -> None:
        """Page Down on receiver via HTTP get command."""
        if self.telnet_available:
            command = (
                self.telnet_commands.command_page_down_denon
                if self.is_denon
                else self.telnet_commands.command_page_down_marantz
            )
            await self.telnet_api.async_send_commands(command)
        else:
            command = (
                self.urls.command_page_down_denon
                if self.is_denon
                else self.urls.command_page_down_marantz
            )
            await self.api.async_get_command(command)

    async def async_input_mode(self, mode: InputModes):
        """Set input mode on receiver via HTTP get command."""
        if mode not in self._input_modes:
            raise AvrCommandError("Invalid input mode")

        if mode == "Select":
            command = (
                self.telnet_commands.command_input_mode_select_denon
                if self.telnet_available
                else (
                    self.urls.command_input_mode_select_denon
                    if self.is_denon
                    else (
                        self.telnet_commands.command_input_mode_select_marantz
                        if self.telnet_available
                        else self.urls.command_input_mode_select_marantz
                    )
                )
            )
        elif mode == "Auto":
            command = (
                self.telnet_commands.command_input_mode_auto_denon
                if self.telnet_available
                else (
                    self.urls.command_input_mode_auto_denon
                    if self.is_denon
                    else (
                        self.telnet_commands.command_input_mode_auto_marantz
                        if self.telnet_available
                        else self.urls.command_input_mode_auto_marantz
                    )
                )
            )
        elif mode == "HDMI":
            command = (
                self.telnet_commands.command_input_mode_hdmi_denon
                if self.telnet_available
                else (
                    self.urls.command_input_mode_hdmi_denon
                    if self.is_denon
                    else (
                        self.telnet_commands.command_input_mode_hdmi_marantz
                        if self.telnet_available
                        else self.urls.command_input_mode_hdmi_marantz
                    )
                )
            )
        elif mode == "Digital":
            command = (
                self.telnet_commands.command_input_mode_digital_denon
                if self.telnet_available
                else (
                    self.urls.command_input_mode_digital_denon
                    if self.is_denon
                    else (
                        self.telnet_commands.command_input_mode_digital_marantz
                        if self.telnet_available
                        else self.urls.command_input_mode_digital_marantz
                    )
                )
            )
        else:
            command = (
                self.telnet_commands.command_input_mode_analog_denon
                if self.telnet_available
                else (
                    self.urls.command_input_mode_analog_denon
                    if self.is_denon
                    else (
                        self.telnet_commands.command_input_mode_analog_marantz
                        if self.telnet_available
                        else self.urls.command_input_mode_analog_marantz
                    )
                )
            )

        if self.telnet_available:
            await self.telnet_api.async_send_commands(command)
        else:
            await self.api.async_get_command(command)


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
        kw_only=True,
    )
    _is_setup: bool = attr.ib(converter=bool, default=False, init=False)

    async def async_update_attrs_appcommand(
        self,
        update_attrs: Dict[AppCommandCmd, None],
        appcommand0300: bool = False,
        global_update: bool = False,
        cache_id: Optional[Hashable] = None,
    ):
        """Update attributes from AppCommand.xml."""
        # Copy that we do not accidently change the wrong dict
        update_attrs = deepcopy(update_attrs)
        # Collect tags for AppCommand.xml call
        tags = tuple(i for i in update_attrs.keys())
        # Execute call
        try:
            if global_update:
                xml = await self._device.api.async_get_global_appcommand(
                    appcommand0300=appcommand0300, cache_id=cache_id
                )
            else:
                # Determine endpoint
                if appcommand0300:
                    url = self._device.urls.appcommand0300
                else:
                    url = self._device.urls.appcommand
                xml = await self._device.api.async_post_appcommand(
                    url, tags, cache_id=cache_id
                )
        except AvrRequestError as err:
            _LOGGER.debug("Error when getting status update: %s", err)
            raise

        # Extract relevant information
        zone = self._device.get_own_zone()

        attrs = deepcopy(update_attrs)
        for app_command in attrs.keys():
            search_strings = self.create_appcommand_search_strings(app_command, zone)
            start = 0
            success = 0
            for i, pattern in enumerate(app_command.response_pattern):
                try:
                    start += 1
                    # Check if attribute exists
                    getattr(self, pattern.update_attribute)
                    # Set new value either from XML attribute or text
                    if pattern.get_xml_attribute is not None:
                        set_value = xml.find(search_strings[i]).get(
                            pattern.get_xml_attribute
                        )
                    else:
                        set_value = xml.find(search_strings[i]).text

                    setattr(self, pattern.update_attribute, set_value)
                    success += 1

                    _LOGGER.debug(
                        "Changing variable %s to value %s",
                        pattern.update_attribute,
                        set_value,
                    )

                except (AttributeError, IndexError) as err:
                    _LOGGER.debug(
                        "Failed updating attribute %s for zone %s: %s",
                        pattern.update_attribute,
                        self._device.zone,
                        err,
                    )

            if start == success:
                # Done
                update_attrs.pop(app_command, None)

        # Check if each attribute was updated
        if update_attrs:
            raise AvrProcessingError(
                f"Some attributes of zone {self._device.zone} not found on update:"
                f" {update_attrs}"
            )

    async def async_update_attrs_status_xml(
        self,
        update_attrs: Dict[str, str],
        urls: List[str],
        cache_id: Optional[Hashable] = None,
    ):
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
                xml = await self._device.api.async_get_xml(url, cache_id=cache_id)
            except AvrRequestError as err:
                _LOGGER.debug(
                    "Error when getting status update from url %s: %s", url, err
                )
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
                        "Changing variable %s to value %s", name, xml.find(tag).text
                    )

                except (AttributeError, IndexError) as err:
                    _LOGGER.debug(
                        "Failed updating attribute %s for zone %s: %s",
                        name,
                        self._device.zone,
                        err,
                    )

            # All done, no need for continuing
            if not update_attrs:
                break

        # Check if each attribute was updated
        if update_attrs:
            raise AvrProcessingError(
                f"Some attributes of zone {self._device.zone} not found on update:"
                f" {update_attrs}"
            )

    @staticmethod
    def create_appcommand_search_strings(
        app_command_cmd: AppCommandCmd, zone: str
    ) -> List[str]:
        """Create search pattern for AppCommand(0300).xml response."""
        result = []

        for resp in app_command_cmd.response_pattern:
            string = "./cmd"
            # Text of cmd tag in query was added as attribute to response
            if app_command_cmd.cmd_text:
                string = (
                    string + f"[@{APPCOMMAND_CMD_TEXT}='{app_command_cmd.cmd_text}']"
                )
            # Text of name tag in query was added as attribute to response
            if app_command_cmd.name:
                string = string + f"[@{APPCOMMAND_NAME}='{app_command_cmd.name}']"
            # Some results include a zone tag
            if resp.add_zone:
                string = string + f"/{zone}"
            # Suffix like /status, /volume
            string = string + resp.suffix

            # A complete search string with all strributes set looks like
            # ./cmd[@cmd_text={cmd_text}][@name={name}]/zone1/volume
            result.append(string)

        return result


def set_api_host(
    instance: DenonAVRFoundation, attribute: attr.Attribute, value: str
) -> str:
    """Change API host on host changes too."""
    # First change _device.api.host then return value
    # pylint: disable=protected-access
    instance._device.api.host = value
    instance._device.telnet_api.host = value
    return value


def set_api_timeout(
    instance: DenonAVRFoundation, attribute: attr.Attribute, value: float
) -> float:
    """Change API timeout on timeout changes too."""
    # First change _device.api.host then return value
    # pylint: disable=protected-access
    instance._device.api.timeout = value
    instance._device.api.read_timeout = max(value, 15.0)
    instance._device.telnet_api.timeout = value
    instance._device.telnet_api._send_confirmation_timeout = value
    return value


def convert_string_int_bool(value: Union[str, bool]) -> Optional[bool]:
    """Convert an integer from string format to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return bool(int(value))
