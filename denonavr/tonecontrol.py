#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the handler for state of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
import time

from typing import Hashable, Optional

import attr

from .appcommand import AppCommandCmdParam, AppCommands
from .const import DENON_ATTR_SETATTR
from .exceptions import AvrProcessingError, AvrCommandError
from .foundation import DenonAVRFoundation, convert_string_int_bool


_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRToneControl(DenonAVRFoundation):
    """This class implements tone control functions of Denon AVR receiver."""

    _tone_control_status: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _tone_control_adjust: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _bass: Optional[int] = attr.ib(
        converter=attr.converters.optional(int),
        default=None)
    _bass_level: Optional[str] = attr.ib(
        converter=attr.converters.optional(str),
        default=None)
    _treble: Optional[int] = attr.ib(
        converter=attr.converters.optional(int),
        default=None)
    _treble_level: Optional[str] = attr.ib(
        converter=attr.converters.optional(str),
        default=None)

    # Update tags for attributes
    # AppCommand.xml interface
    appcommand_attrs = {
        AppCommands.GetToneControl: None}

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
        await self.async_update_tone_control(
            global_update=global_update, cache_id=cache_id)

    async def async_update_tone_control(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update tone control status of device."""
        if self._device.use_avr_2016_update is True:
            await self.async_update_attrs_appcommand(
                self.appcommand_attrs, global_update=global_update,
                cache_id=cache_id, ignore_missing_response=True)
        elif self._device.use_avr_2016_update is False:
            # Not available
            pass
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set")

    async def async_set_tone_control_command(
            self, parameter_type: str, value: int) -> None:
        """Post request for tone control commands."""
        cmd = (attr.evolve(
            AppCommands.SetToneControl,
            set_command=AppCommandCmdParam(name=parameter_type, text=value)),)
        await self._device.api.async_post_appcommand(
            self._device.urls.appcommand, cmd, cache_id=time.time())

    ##############
    # Properties #
    ##############
    @property
    def bass(self) -> Optional[int]:
        """Return value of bass."""
        return self._bass

    @property
    def bass_level(self) -> Optional[str]:
        """Return level of bass."""
        return self._bass_level

    @property
    def treble(self) -> Optional[int]:
        """Return value of treble."""
        return self._treble

    @property
    def treble_level(self) -> Optional[str]:
        """Return level of treble."""
        return self._treble_level

    ##########
    # Setter #
    ##########
    async def async_enable_tone_control(self) -> None:
        """Enable tone control to change settings like bass or treble."""
        if self._tone_control_status is False:
            raise AvrCommandError(
                "Cannot enable tone control, Dynamic EQ must be deactivated")

        await self.async_set_tone_control_command("adjust", 1)

    async def async_disable_tone_control(self) -> None:
        """Disable tone control to change settings like bass or treble."""
        if self._tone_control_status is False:
            raise AvrCommandError(
                "Cannot disable tone control, Dynamic EQ must be deactivated")

        await self.async_set_tone_control_command("adjust", 0)

    async def async_set_bass(self, value: int) -> None:
        """
        Set receiver bass.

        Minimum is 0, maximum at 12

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if value < 0 or value > 12:
            raise AvrCommandError("Invalid value for bass")
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command("bassvalue", value)

    async def async_bass_up(self) -> None:
        """
        Increase level of Bass.

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if self.bass == 12:
            return
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command("bassvalue", self.bass + 1)
        await self.async_update()

    async def async_bass_down(self) -> None:
        """
        Decrease level of Bass.

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if self.bass == 0:
            return
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command("bassvalue", self.bass - 1)
        await self.async_update()

    async def async_set_treble(self, value: int) -> None:
        """
        Set receiver treble.

        Minimum is 0, maximum at 12

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if value < 0 or value > 12:
            raise AvrCommandError("Invalid value for treble")
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command("treblevalue", value)

    async def async_treble_up(self) -> None:
        """
        Increase level of Treble.

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if self.treble == 12:
            return
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command(
            "treblevalue", self.treble + 1
            )
        await self.async_update()

    async def async_treble_down(self) -> None:
        """
        Decrease level of Treble.

        Note:
        Doesn't work, if Dynamic Equalizer is active.
        """
        if self.treble == 0:
            return
        await self.async_enable_tone_control()
        await self.async_set_tone_control_command(
            "treblevalue", self.treble - 1
            )
        await self.async_update()


def tone_control_factory(instance: DenonAVRFoundation) -> DenonAVRToneControl:
    """Create DenonAVRToneControl at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRToneControl(device=instance._device)
    return new
