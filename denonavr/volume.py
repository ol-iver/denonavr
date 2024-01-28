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
    return bool(value.lower() == STATE_ON)


def convert_volume(value: Union[float, str]) -> float:
    """Convert volume to float."""
    if value == "--":
        return -80.0
    return float(value)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRVolume(DenonAVRFoundation):
    """This class implements volume functions of Denon AVR receiver."""

    _volume: Optional[float] = attr.ib(
        converter=attr.converters.optional(convert_volume), default=None
    )
    _muted: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_muted), default=None
    )

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {
        AppCommands.GetAllZoneVolume: None,
        AppCommands.GetAllZoneMuteStatus: None,
    }
    # Status.xml interface
    status_xml_attrs = {"_volume": "./MasterVolume/value", "_muted": "./Mute/value"}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        for tag in self.appcommand_attrs:
            self._device.api.add_appcommand_update_tag(tag)

        self._device.telnet_api.register_callback("MV", self._async_volume_callback)
        self._device.telnet_api.register_callback("MU", self._async_mute_callback)

        self._is_setup = True

    async def _async_volume_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a volume change event."""
        if self._device.zone != zone:
            return

        if len(parameter) < 3:
            self._volume = -80.0 + float(parameter)
        else:
            whole_number = float(parameter[0:2])
            fraction = 0.1 * float(parameter[2])
            self._volume = -80.0 + whole_number + fraction

    async def _async_mute_callback(self, zone: str, event: str, parameter: str) -> None:
        """Handle a muting change event."""
        if self._device.zone != zone:
            return

        self._muted = parameter

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update volume asynchronously."""
        # Ensure instance is setup before updating
        if not self._is_setup:
            self.setup()

        # Update state
        await self.async_update_volume(global_update=global_update, cache_id=cache_id)

    async def async_update_volume(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ):
        """Update volume status of device."""
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
        success = self._device.telnet_api.send_commands(
            self._device.telnet_commands.command_volume_up
        )
        if not success:
            await self._device.api.async_get_command(
                self._device.urls.command_volume_up
            )

    async def async_volume_down(self) -> None:
        """Volume down receiver via HTTP get command."""
        success = self._device.telnet_api.send_commands(
            self._device.telnet_commands.command_volume_down
        )
        if not success:
            await self._device.api.async_get_command(
                self._device.urls.command_volume_down
            )

    async def async_set_volume(self, volume: float) -> None:
        """
        Set receiver volume via HTTP get command.

        Volume is send in a format like -50.0.
        Minimum is -80.0, maximum at 18.0
        """
        if volume < -80 or volume > 18:
            raise AvrCommandError(f"Invalid volume: {volume}")

        # Round volume because only values which are a multi of 0.5 are working
        volume = round(volume * 2) / 2.0
        success = self._device.telnet_api.send_commands(
            self._device.telnet_commands.command_set_volume.format(
                volume=int(volume + 80)
            )
        )
        if not success:
            await self._device.api.async_get_command(
                self._device.urls.command_set_volume.format(volume=volume)
            )

    async def async_mute(self, mute: bool) -> None:
        """Mute receiver via HTTP get command."""
        if mute:
            success = self._device.telnet_api.send_commands(
                self._device.telnet_commands.command_mute_on
            )
            if not success:
                await self._device.api.async_get_command(
                    self._device.urls.command_mute_on
                )
        else:
            success = self._device.telnet_api.send_commands(
                self._device.telnet_commands.command_mute_off
            )
            if not success:
                await self._device.api.async_get_command(
                    self._device.urls.command_mute_off
                )


def volume_factory(instance: DenonAVRFoundation) -> DenonAVRVolume:
    """Create DenonAVRVolume at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRVolume(device=instance._device)
    return new
