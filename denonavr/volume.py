#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the handler for volume of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging

from typing import Hashable, Optional, Union

import attr

from .appcommand import AppCommands
from .const import DENON_ATTR_SETATTR, MAIN_ZONE, STATE_ON
from .exceptions import AvrCommandError, AvrProcessingError
from .foundation import DenonAVRFoundation


_LOGGER = logging.getLogger(__name__)


def convert_muted(value: str) -> bool:
    """Convert muted to bool."""
    return bool(value == STATE_ON)


def convert_volume(value: Union[float, str]) -> float:
    """Convert volume to float."""
    if value == "--":
        return -80.0
    return float(value)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRVolume(DenonAVRFoundation):
    """This class implements volume functions of Denon AVR receiver."""

    _volume: Optional[float] = attr.ib(
        converter=attr.converters.optional(convert_volume),
        default=None)
    _muted: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_muted),
        default=None)

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {
        AppCommands.GetAllZoneVolume: None,
        AppCommands.GetAllZoneMuteStatus: None}
    # Status.xml interface
    status_xml_attrs = {
        "_volume": "./MasterVolume/value",
        "_muted": "./Mute/value"}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        for tag in self.appcommand_attrs:
            self._device.api.add_appcommand_update_tag(tag)

        self._is_setup = True

    async def async_update(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None) -> None:
        """Update volume asynchronously."""
        # Ensure instance is setup before updating
        if self._is_setup is False:
            self.setup()

        # Update state
        await self.async_update_volume(
            global_update=global_update, cache_id=cache_id)

    async def async_update_volume(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update volume status of device."""
        if self._device.use_avr_2016_update is True:
            await self.async_update_attrs_appcommand(
                self.appcommand_attrs, global_update=global_update,
                cache_id=cache_id)
        elif self._device.use_avr_2016_update is False:
            urls = [self._device.urls.status]
            if self._device.zone == MAIN_ZONE:
                urls.append(self._device.urls.mainzone)
            await self.async_update_attrs_status_xml(
                self.status_xml_attrs, urls, cache_id=cache_id)
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set")

    ##############
    # Properties #
    ##############
    @property
    def muted(self) -> Optional[bool]:
        """
        Boolean if volume is currently muted.

        Return "True" if muted and "False" if not muted.
        """
        return self._muted

    @property
    def volume(self) -> Optional[float]:
        """
        Return volume of Denon AVR as float.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        return self._volume

    ##########
    # Setter #
    ##########
    async def async_volume_up(self) -> None:
        """Volume up receiver via HTTP get command."""
        await self._device.api.async_get_command(
            self._device.urls.command_volume_up)

    async def async_volume_down(self) -> None:
        """Volume down receiver via HTTP get command."""
        await self._device.api.async_get_command(
            self._device.urls.command_volume_down)

    async def async_set_volume(self, volume: float) -> None:
        """
        Set receiver volume via HTTP get command.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        if volume < -80 or volume > 18:
            raise AvrCommandError("Invalid volume: {}".format(volume))

        # Round volume because only values which are a multi of 0.5 are working
        volume = round(volume * 2) / 2.0

        await self._device.api.async_get_command(
            self._device.urls.command_set_volume.format(volume=volume))

    async def async_mute(self, mute: bool) -> None:
        """Mute receiver via HTTP get command."""
        if mute:
            await self._device.api.async_get_command(
                self._device.urls.command_mute_on)
        else:
            await self._device.api.async_get_command(
                self._device.urls.command_mute_off)


def volume_factory(instance: DenonAVRFoundation) -> DenonAVRVolume:
    """Create DenonAVRVolume at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRVolume(device=instance._device)
    return new
