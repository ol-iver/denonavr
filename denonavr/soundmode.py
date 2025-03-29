#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the handler for sound mode of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import logging
from collections.abc import Hashable
from copy import deepcopy
from typing import Dict, List, Literal, Optional, get_args

import attr

from .appcommand import AppCommands
from .const import (
    ALL_ZONE_STEREO,
    DENON_ATTR_SETATTR,
    SOUND_MODE_MAPPING,
    IMAXHPFs,
    IMAXLPFs,
)
from .exceptions import AvrCommandError, AvrIncompleteResponseError, AvrProcessingError
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)


def convert_sound_mode(value: Optional[str]) -> Optional[str]:
    """Remove multiple spaces from value."""
    if value is None:
        return value
    return " ".join(str(value).split())


def sound_mode_map_factory() -> Dict[str, List]:
    """Construct sound_mode map."""
    sound_mode_map = {}
    for matched_mode, sublist in SOUND_MODE_MAPPING.items():
        sound_mode_map[matched_mode] = [convert_sound_mode(i) for i in sublist]
    return sound_mode_map


def sound_mode_rev_map_factory(instance: "DenonAVRSoundMode") -> Dict[str, str]:
    """
    Construct the sound_mode_rev_map.

    Reverse the key value structure. The sound_mode_rev_map is bigger,
    but allows for direct matching using a dictionary key access.
    The sound_mode_map is uses externally to set this dictionary
    because that has a nicer syntax.
    """
    mode_map = list(
        instance._sound_mode_map.items()  # pylint: disable=protected-access
    )
    mode_map_rev = {}
    for matched_mode, sublist in mode_map:
        for raw_mode in sublist:
            mode_map_rev[convert_sound_mode(raw_mode)] = matched_mode
    return mode_map_rev


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRSoundMode(DenonAVRFoundation):
    """This class implements sound mode functions of Denon AVR receiver."""

    _support_sound_mode: Optional[bool] = attr.ib(
        converter=attr.converters.optional(bool), default=None
    )
    _sound_mode_raw: Optional[str] = attr.ib(
        converter=attr.converters.optional(convert_sound_mode), default=None
    )
    _neural_x_on_off: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _imax_auto_off: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _imax_audio_settings: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _imax_hpf: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )
    _imax_hpfs = get_args(IMAXHPFs)
    _imax_lpf: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )
    _imax_lpfs = get_args(IMAXLPFs)
    _imax_subwoofer_mode: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _imax_subwoofer_output: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _center_spread: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _loudness_management: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )
    _sound_mode_map: Dict[str, list] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str),
            attr.validators.deep_iterable(
                attr.validators.instance_of(str), attr.validators.instance_of(list)
            ),
            attr.validators.instance_of(dict),
        ),
        default=attr.Factory(sound_mode_map_factory),
        init=False,
    )
    _sound_mode_map_rev: Dict[str, str] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str),
            attr.validators.instance_of(str),
            attr.validators.instance_of(dict),
        ),
        default=attr.Factory(sound_mode_rev_map_factory, takes_self=True),
        init=False,
    )
    _setup_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))
    _appcommand_active: bool = attr.ib(converter=bool, default=True, init=False)

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {AppCommands.GetSurroundModeStatus: None}
    # Status.xml interface
    status_xml_attrs_01 = {"_sound_mode_raw": "./selectSurround/value"}
    status_xml_attrs_02 = {"_sound_mode_raw": "./SurrMode/value"}

    async def async_setup(self) -> None:
        """Ensure that the instance is initialized."""
        async with self._setup_lock:
            _LOGGER.debug("Starting sound mode setup")

            # The first update determines if sound mode is supported
            await self.async_update_sound_mode()

            if self._support_sound_mode and self._appcommand_active:
                # Add tags for a potential AppCommand.xml update
                for tag in self.appcommand_attrs:
                    self._device.api.add_appcommand_update_tag(tag)

            self._device.telnet_api.register_callback(
                "MS", self._async_soundmode_callback
            )
            self._device.telnet_api.register_callback(
                "PS", self._async_neural_x_callback
            )
            self._device.telnet_api.register_callback("PS", self._async_imax_callback)
            self._device.telnet_api.register_callback(
                "PS", self._async_center_spread_callback
            )
            self._device.telnet_api.register_callback(
                "PS", self._async_loudness_management_callback
            )

            self._is_setup = True
            _LOGGER.debug("Finished sound mode setup")

    async def _async_soundmode_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a sound mode change event."""
        if self._device.zone != zone:
            return

        self._sound_mode_raw = parameter

    async def _async_neural_x_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a Neural X change event."""
        parameter_name_length = len("NEURAL")
        if parameter[:parameter_name_length] == "NEURAL":
            self._neural_x_on_off = parameter[parameter_name_length + 1 :]

    async def _async_imax_callback(self, zone: str, event: str, parameter: str) -> None:
        """Handle an IMAX change event."""
        key_value = parameter.split()
        if len(key_value) != 2 or key_value[0][:4] != "IMAX":
            return

        if key_value[0] == "IMAX":
            self._imax_auto_off = parameter[5:]
        elif key_value[0] == "IMAXAUD":
            self._imax_audio_settings = parameter[8:]
        elif key_value[0] == "IMAXHPF":
            self._imax_hpf = int(parameter[8:])
        elif key_value[0] == "IMAXLPF":
            self._imax_lpf = int(parameter[8:])
        elif key_value[0] == "IMAXSWM":
            self._imax_subwoofer_mode = parameter[8:]
        elif key_value[0] == "IMAXSWO":
            self._imax_subwoofer_output = parameter[8:]

    async def _async_center_spread_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a Center Spread change event."""
        if parameter[:3] == "CES":
            self._center_spread = parameter[4:]

    async def _async_loudness_management_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a Loudness Management change event."""
        if parameter[:3] == "LOM":
            self._loudness_management = parameter[4:]

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update sound mode asynchronously."""
        _LOGGER.debug("Starting sound mode update")
        # Ensure instance is setup before updating
        if not self._is_setup:
            await self.async_setup()

        # Update state
        await self.async_update_sound_mode(
            global_update=global_update, cache_id=cache_id
        )
        _LOGGER.debug("Finished sound mode update")

    async def async_update_sound_mode(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ):
        """Update sound mode status of device."""
        if self._device.use_avr_2016_update is None:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set"
            )

        if self._is_setup and not self._support_sound_mode:
            return

        if self._device.use_avr_2016_update and self._appcommand_active:
            try:
                await self.async_update_attrs_appcommand(
                    self.appcommand_attrs,
                    global_update=global_update,
                    cache_id=cache_id,
                )
            except (AvrProcessingError, AvrIncompleteResponseError):
                self._appcommand_active = False
                _LOGGER.debug(
                    "Appcommand.xml does not support Sound mode. "
                    "Testing status.xml interface next"
                )
            else:
                if not self._is_setup:
                    self._support_sound_mode = True
                    _LOGGER.info("Sound mode supported")
                return

        urls = [self._device.urls.status, self._device.urls.mainzone]
        # There are two different options of sound mode tags
        try:
            await self.async_update_attrs_status_xml(
                self.status_xml_attrs_01, urls, cache_id=cache_id
            )
        except AvrProcessingError:
            try:
                await self.async_update_attrs_status_xml(
                    self.status_xml_attrs_02, urls, cache_id=cache_id
                )
            except AvrProcessingError:
                self._support_sound_mode = False
                _LOGGER.info("Sound mode not supported")
                return

        if not self._is_setup:
            self._support_sound_mode = True
            _LOGGER.info("Sound mode supported")

    def match_sound_mode(self) -> Optional[str]:
        """Match the raw_sound_mode to its corresponding sound_mode."""
        if self._sound_mode_raw is None:
            return None
        smr_up = self._sound_mode_raw.upper()
        try:
            sound_mode = self._sound_mode_map_rev[smr_up]
        except KeyError:
            # Estimate sound mode for unclassified input
            if smr_up.find("DTS") != -1:
                self._sound_mode_map["DTS SURROUND"].append(smr_up)
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', assuming 'DTS SURROUND'.",
                    smr_up,
                )
            elif smr_up.find("DOLBY") != -1:
                self._sound_mode_map["DOLBY DIGITAL"].append(smr_up)
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', assuming 'DOLBY DIGITAL'.",
                    smr_up,
                )
            elif smr_up.find("MUSIC") != -1:
                self._sound_mode_map["MUSIC"].append(smr_up)
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', assuming 'MUSIC'.", smr_up
                )
            elif smr_up.find("AURO") != -1:
                self._sound_mode_map["AURO3D"].append(smr_up)
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', assuming 'AURO3D'.", smr_up
                )
            elif smr_up.find("MOVIE") != -1 or smr_up.find("CINEMA") != -1:
                self._sound_mode_map["MOVIE"].append(smr_up)
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', assuming 'MOVIE'.", smr_up
                )
            else:
                self._sound_mode_map[smr_up] = [smr_up]
                _LOGGER.warning(
                    "Not able to match sound mode: '%s', returning raw sound mode.",
                    smr_up,
                )
            self._sound_mode_map_rev = sound_mode_rev_map_factory(self)
            sound_mode = self._sound_mode_map_rev[smr_up]

        return sound_mode

    async def _async_set_all_zone_stereo(self, zst_on: bool) -> None:
        """
        Set All Zone Stereo option on the device.

        Calls command to activate/deactivate the mode
        """
        command_url = self._device.urls.command_set_all_zone_stereo
        telnet_command = self._device.telnet_commands.command_set_all_zone_stereo
        if zst_on:
            command_url += "ZST ON"
            telnet_command += "ZST ON"
        else:
            command_url += "ZST OFF"
            telnet_command += "ZST OFF"
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(telnet_command)
        else:
            await self._device.api.async_get_command(command_url)

    ##############
    # Properties #
    ##############
    @property
    def support_sound_mode(self) -> Optional[bool]:
        """Return True if sound mode is supported."""
        return self._support_sound_mode

    @property
    def sound_mode(self) -> Optional[str]:
        """Return the matched current sound mode as a string."""
        sound_mode_matched = self.match_sound_mode()
        return sound_mode_matched

    @property
    def sound_mode_list(self) -> List[str]:
        """Return a list of available sound modes as string."""
        return list(self._sound_mode_map.keys())

    @property
    def sound_mode_map(self) -> Dict[str, str]:
        """Return a dict of available sound modes with their mapping values."""
        return deepcopy(self._sound_mode_map)

    @property
    def sound_mode_map_rev(self) -> Dict[str, str]:
        """Return a dict to map each sound_mode_raw to matching sound_mode."""
        return deepcopy(self._sound_mode_map_rev)

    @property
    def sound_mode_raw(self) -> Optional[str]:
        """Return the current sound mode as string as received from the AVR."""
        return self._sound_mode_raw

    @property
    def neural_x(self) -> Optional[str]:
        """
        Return the current Neural:X status.

        Only available if using Telnet.

        Possible values are: "ON", "OFF"
        """
        return self._neural_x_on_off

    @property
    def imax(self) -> Optional[str]:
        """
        Return the current IMAX status.

        Only available if using Telnet.

        Possible values are: "AUTO", "OFF"
        """
        return self._imax_auto_off

    @property
    def imax_audio_settings(self) -> Optional[str]:
        """
        Return the current IMAX Audio Settings.

        Only available if using Telnet.

        Possible values are: "AUTO", "MANUAL"
        """
        return self._imax_audio_settings

    @property
    def imax_hpf(self) -> Optional[int]:
        """
        Return the current IMAX High Pass Filter.

        Only available if using Telnet.
        """
        return self._imax_hpf

    @property
    def imax_lpf(self) -> Optional[int]:
        """
        Return the current IMAX Low Pass Filter.

        Only available if using Telnet.
        """
        return self._imax_lpf

    @property
    def imax_subwoofer_mode(self) -> Optional[str]:
        """
        Return the current IMAX Subwoofer Mode.

        Only available if using Telnet.
        """
        return self._imax_subwoofer_mode

    @property
    def imax_subwoofer_output(self) -> Optional[str]:
        """
        Return the current IMAX Subwoofer Output Mode.

        Only available if using Telnet.
        """
        return self._imax_subwoofer_output

    @property
    def center_spread(self) -> Optional[str]:
        """
        Return the current Center Spread status.

        Only available if using Telnet.

        Possible values are: "ON", "OFF"
        """
        return self._center_spread

    @property
    def loudness_management(self) -> Optional[str]:
        """
        Return the current Loudness Management status.

        Only available if using Telnet.

        Possible values are: "ON", "OFF"
        """
        return self._loudness_management

    ##########
    # Setter #
    ##########
    async def async_set_sound_mode(self, sound_mode: str) -> None:
        """
        Set sound_mode of device.

        Valid values depend on the device and should be taken from
        "sound_mode_list".
        """
        if sound_mode not in self.sound_mode_list:
            raise AvrCommandError(f"{sound_mode} is not a valid sound mode")

        if sound_mode == ALL_ZONE_STEREO:
            await self._async_set_all_zone_stereo(True)
            return

        if self.sound_mode == ALL_ZONE_STEREO:
            await self._async_set_all_zone_stereo(False)
        # For selection of sound mode other names then at receiving sound modes
        # have to be used
        # Therefore source mapping is needed to get sound_mode
        # Create command URL and send command via HTTP GET
        command_url = self._device.urls.command_sel_sound_mode + sound_mode
        telnet_command = (
            self._device.telnet_commands.command_sel_sound_mode + sound_mode
        )
        # sent command
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(telnet_command)
        else:
            await self._device.api.async_get_command(command_url)

    async def async_sound_mode_next(self):
        """Select next sound mode."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_sel_sound_mode + "RIGHT"
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_sel_sound_mode + "RIGHT"
            )

    async def async_sound_mode_previous(self):
        """Select previous sound mode."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_sel_sound_mode + "LEFT"
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_sel_sound_mode + "LEFT"
            )

    async def async_neural_x_on(self):
        """Turn on Neural:X sound mode."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_neural_x_on_off.format(mode="ON")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_neural_x_on_off.format(mode="ON")
            )

    async def async_neural_x_off(self):
        """Turn off Neural:X sound mode."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_neural_x_on_off.format(mode="OFF")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_neural_x_on_off.format(mode="OFF")
            )

    async def async_neural_x_toggle(self):
        """
        Toggle Neural:X sound mode.

        Only available if using Telnet.
        """
        if self._neural_x_on_off == "ON":
            await self.async_neural_x_off()
        else:
            await self.async_neural_x_on()

    async def async_imax_auto(self):
        """Set IMAX sound mode to Auto."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_auto_off.format(mode="AUTO")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_auto_off.format(mode="AUTO")
            )

    async def async_imax_off(self):
        """Turn off IMAX sound mode."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_auto_off.format(mode="OFF")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_auto_off.format(mode="OFF")
            )

    async def async_imax_toggle(self):
        """
        Toggle IMAX sound mode between auto and off.

        Only available if using Telnet.
        """
        if self._imax_auto_off != "OFF":
            await self.async_imax_off()
        else:
            await self.async_imax_auto()

    async def async_imax_audio_settings(self, mode: Literal["AUTO", "MANUAL"]):
        """Set IMAX audio settings."""
        if mode not in ["AUTO", "MANUAL"]:
            raise AvrCommandError(f"{mode} is not a valid IMAX audio setting")

        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_audio_settings.format(
                    mode=mode
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_audio_settings.format(mode=mode)
            )

    async def async_imax_audio_settings_toggle(self) -> None:
        """
        Toggle IMAX audio settings between auto and manual.

        Only available if using Telnet.
        """
        if self._imax_audio_settings == "AUTO":
            await self.async_imax_audio_settings("MANUAL")
        else:
            await self.async_imax_audio_settings("AUTO")

    async def async_imax_hpf(self, hpf: IMAXHPFs) -> None:
        """Set IMAX High Pass Filter."""
        if hpf not in self._imax_hpfs:
            raise AvrCommandError(f"{hpf} is not a valid IMAX high pass filter")

        local_hpf = self._padded_pass_filter(hpf)
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_hpf.format(
                    frequency=local_hpf
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_hpf.format(frequency=local_hpf)
            )

    async def async_imax_lpf(self, lpf: IMAXLPFs) -> None:
        """Set IMAX Low Pass Filter."""
        if lpf not in self._imax_lpfs:
            raise AvrCommandError(f"{lpf} is not a valid IMAX low pass filter")
        # pad lpf with 0 if it is a only two digits digit
        local_lpf = self._padded_pass_filter(lpf)
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_lpf.format(
                    frequency=local_lpf
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_lpf.format(frequency=local_lpf)
            )

    @staticmethod
    def _padded_pass_filter(pass_filter: str) -> str:
        return f"0{pass_filter}" if len(str(pass_filter)) == 2 else str(pass_filter)

    async def async_imax_subwoofer_mode(self, mode: Literal["ON", "OFF"]) -> None:
        """Set IMAX Subwoofer Mode."""
        if mode not in ["ON", "OFF"]:
            raise AvrCommandError(f"{mode} is not a valid IMAX subwoofer mode")

        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_subwoofer_mode.format(
                    mode=mode
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_subwoofer_mode.format(mode=mode)
            )

    async def async_imax_subwoofer_output(self, mode: Literal["L+M", "LFE"]) -> None:
        """Set IMAX Subwoofer Output Mode."""
        if mode not in ["L+M", "LFE"]:
            raise AvrCommandError(f"{mode} is not a valid IMAX subwoofer output mode")

        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_imax_subwoofer_output.format(
                    mode=mode
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_imax_subwoofer_output.format(mode=mode)
            )

    async def async_center_spread_on(self):
        """Set Center Spread to ON."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_center_spread.format(mode="ON")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_center_spread.format(mode="ON")
            )

    async def async_center_spread_off(self):
        """Set Center Spread to ON."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_center_spread.format(mode="OFF")
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_center_spread.format(mode="OFF")
            )

    async def async_center_spread_toggle(self):
        """
        Toggle Center Spread.

        Only available if using Telnet.
        """
        if self._center_spread == "ON":
            await self.async_center_spread_off()
        else:
            await self.async_center_spread_on()

    async def async_loudness_management_on(self):
        """Set Loudness Management to ON."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_loudness_management.format(
                    mode="ON"
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_loudness_management.format(mode="ON")
            )

    async def async_loudness_management_off(self):
        """Set Loudness Management to OFF."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_loudness_management.format(
                    mode="OFF"
                )
            )
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_loudness_management.format(mode="OFF")
            )

    async def async_loudness_management_toggle(self):
        """
        Toggle Loudness Management.

        Only available if using Telnet.
        """
        if self._loudness_management == "ON":
            await self.async_loudness_management_off()
        else:
            await self.async_loudness_management_on()


def sound_mode_factory(instance: DenonAVRFoundation) -> DenonAVRSoundMode:
    """Create DenonAVRSoundMode at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRSoundMode(device=instance._device)
    return new
