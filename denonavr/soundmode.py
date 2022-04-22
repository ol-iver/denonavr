#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the handler for sound mode of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
from copy import deepcopy
import logging

from typing import Dict, Hashable, List, Optional

import attr

from .appcommand import AppCommands
from .const import (
    AVR_X, AVR_X_2016, ALL_ZONE_STEREO, DENON_ATTR_SETATTR, SOUND_MODE_MAPPING)
from .exceptions import AvrProcessingError
from .foundation import DenonAVRFoundation


_LOGGER = logging.getLogger(__name__)


def convert_sound_mode(value: Optional[str]) -> Optional[str]:
    """Convert to upper case and remove multiple spaces on value."""
    if value is None:
        return value
    return " ".join(str(value).upper().split())


def sound_mode_map_factory() -> Dict[str, List]:
    """Construct sound_mode map."""
    sound_mode_map = {}
    for matched_mode, sublist in SOUND_MODE_MAPPING.items():
        sound_mode_map[matched_mode] = [convert_sound_mode(i) for i in sublist]
    return sound_mode_map


def sound_mode_rev_map_factory(instance: DenonAVRFoundation) -> Dict[str, str]:
    """
    Construct the sound_mode_rev_map.

    Reverse the key value structure. The sound_mode_rev_map is bigger,
    but allows for direct matching using a dictionary key access.
    The sound_mode_map is uses externally to set this dictionary
    because that has a nicer syntax.
    """
    mode_map = list(
        instance._sound_mode_map.items())  # pylint: disable=protected-access
    mode_map_rev = {}
    for matched_mode, sublist in mode_map:
        for raw_mode in sublist:
            mode_map_rev[convert_sound_mode(raw_mode)] = matched_mode
    return mode_map_rev


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRSoundMode(DenonAVRFoundation):
    """This class implements sound mode functions of Denon AVR receiver."""

    _support_sound_mode: Optional[bool] = attr.ib(
        converter=attr.converters.optional(bool),
        default=None)
    _sound_mode_raw: Optional[str] = attr.ib(
        converter=attr.converters.optional(convert_sound_mode),
        default=None)
    _sound_mode_map: Dict[str, list] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str),
            attr.validators.deep_iterable(
                attr.validators.instance_of(str),
                attr.validators.instance_of(list)),
            attr.validators.instance_of(dict)),
        default=attr.Factory(sound_mode_map_factory), init=False)
    _sound_mode_map_rev: Dict[str, str] = attr.ib(
        validator=attr.validators.deep_mapping(
            attr.validators.instance_of(str),
            attr.validators.instance_of(str),
            attr.validators.instance_of(dict)),
        default=attr.Factory(sound_mode_rev_map_factory, takes_self=True),
        init=False)
    _setup_lock: asyncio.Lock = attr.ib(default=attr.Factory(asyncio.Lock))

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {
        AppCommands.GetSurroundModeStatus: None}
    # Status.xml interface
    status_xml_attrs_01 = {
        "_sound_mode_raw": "./selectSurround/value"}
    status_xml_attrs_02 = {
        "_sound_mode_raw": "./SurrMode/value"}

    async def async_setup(self) -> None:
        """Ensure that the instance is initialized."""
        async with self._setup_lock:
            # Add tags for a potential AppCommand.xml update
            for tag in self.appcommand_attrs:
                self._device.api.add_appcommand_update_tag(tag)

            # Soundmode is always available for AVR-X and AVR-X-2016 receivers
            # For AVR receiver it will be tested druing the first update
            if self._device.receiver in [AVR_X, AVR_X_2016]:
                self._support_sound_mode = True
            else:
                await self.async_update_sound_mode()

            self._is_setup = True

    async def async_update(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None) -> None:
        """Update sound mode asynchronously."""
        # Ensure instance is setup before updating
        if self._is_setup is False:
            await self.async_setup()

        # Update state
        await self.async_update_sound_mode(
            global_update=global_update, cache_id=cache_id)

    async def async_update_sound_mode(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update sound mode status of device."""
        if self._device.use_avr_2016_update is True:
            await self.async_update_attrs_appcommand(
                self.appcommand_attrs, global_update=global_update,
                cache_id=cache_id)
        elif self._device.use_avr_2016_update is False:
            urls = [self._device.urls.status, self._device.urls.mainzone]
            if self._support_sound_mode is False:
                return
            # There are two different options of sound mode tags
            try:
                await self.async_update_attrs_status_xml(
                    self.status_xml_attrs_01, urls, cache_id=cache_id)
            except AvrProcessingError:
                try:
                    await self.async_update_attrs_status_xml(
                        self.status_xml_attrs_02, urls, cache_id=cache_id)
                except AvrProcessingError:
                    _LOGGER.info("Sound mode not supported")
                    self._support_sound_mode = False
                    return
            self._support_sound_mode = True
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set")

    def match_sound_mode(self, sound_mode_raw: str) -> Optional[str]:
        """Match the raw_sound_mode to its corresponding sound_mode."""
        if self._sound_mode_raw is None:
            return None
        smr_cv = convert_sound_mode(sound_mode_raw)
        try:
            sound_mode = self._sound_mode_map_rev[smr_cv]
        except KeyError:
            # Estimate sound mode for unclassified input
            if smr_cv.find("DTS") != -1:
                self._sound_mode_map["DTS SURROUND"].append(smr_cv)
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "assuming 'DTS SURROUND'.", smr_cv)
            elif smr_cv.find("DOLBY") != -1:
                self._sound_mode_map["DOLBY DIGITAL"].append(smr_cv)
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "assuming 'DOLBY DIGITAL'.", smr_cv)
            elif smr_cv.find("MUSIC") != -1:
                self._sound_mode_map["MUSIC"].append(smr_cv)
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "assuming 'MUSIC'.", smr_cv)
            elif smr_cv.find("AURO") != -1:
                self._sound_mode_map["AURO3D"].append(smr_cv)
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "assuming 'AURO3D'.", smr_cv)
            elif (smr_cv.find("MOVIE") != -1 or smr_cv.find("CINEMA") != -1):
                self._sound_mode_map["MOVIE"].append(smr_cv)
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "assuming 'MOVIE'.", smr_cv)
            else:
                self._sound_mode_map[smr_cv] = [smr_cv]
                _LOGGER.warning("Not able to match sound mode: '%s', "
                                "returning raw sound mode.", smr_cv)
            self._sound_mode_map_rev = sound_mode_rev_map_factory(self)
            sound_mode = self._sound_mode_map_rev[smr_cv]

        return sound_mode

    async def _async_set_all_zone_stereo(self, zst_on: bool) -> None:
        """
        Set All Zone Stereo option on the device.

        Calls command to activate/deactivate the mode
        """
        command_url = self._device.urls.command_set_all_zone_stereo
        if zst_on:
            command_url += "ZST ON"
        else:
            command_url += "ZST OFF"

        await self._device.api.async_get_command(command_url)

    ##############
    # Properties #
    ##############
    @property
    def support_sound_mode(self) -> Optional[bool]:
        """Return True if sound mode supported."""
        return self._support_sound_mode

    @property
    def sound_mode(self) -> Optional[str]:
        """Return the matched current sound mode as a string."""
        sound_mode_matched = self.match_sound_mode(self._sound_mode_raw)
        return sound_mode_matched

    @property
    def sound_mode_list(self) -> None:
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

    ##########
    # Setter #
    ##########
    async def async_set_sound_mode(self, sound_mode: str) -> None:
        """
        Set sound_mode of device.

        Valid values depend on the device and should be taken from
        "sound_mode_list".
        """
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
        # sent command
        await self._device.api.async_get_command(command_url)


def sound_mode_factory(instance: DenonAVRFoundation) -> DenonAVRSoundMode:
    """Create DenonAVRSoundMode at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRSoundMode(device=instance._device)
    return new
