#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Output settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
from collections.abc import Hashable
from typing import Optional

import attr

from .appcommand import AppCommandCmd, AppCommandCmdParam, AppCommands
from .const import (
    DENON_ATTR_SETATTR,
    HDMI_OUTPUT_MAP,
    HDMI_OUTPUT_MAP_APPCOMMAND_REVERSE,
    HDMI_OUTPUT_MAP_TELNET_REVERSE,
    HDMIOutputs,
)
from .exceptions import AvrCommandError, AvrProcessingError
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVROutputSettings(DenonAVRFoundation):
    """Output Settings."""

    _videoout: Optional[str] = attr.ib(
        converter=attr.converters.optional(HDMI_OUTPUT_MAP.get), default=None
    )

    # Update tags for attributes
    # AppCommand0300.xml interface
    appcommand0300_attrs = {AppCommands.GetOutputSettings: None}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        for tag in self.appcommand0300_attrs:
            self._device.api.add_appcommand0300_update_tag(tag)

        self._device.telnet_api.register_callback("VS", self._videoout_callback)

        self._is_setup = True

    def _videoout_callback(self, zone: str, event: str, parameter: str) -> None:
        """Handle a HDMI Output change event."""
        if self._device.zone != zone:
            return

        if parameter[0:4] == "MONI":
            self._videoout = parameter

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update OutputSettings asynchronously."""
        _LOGGER.debug("Starting OutputSettings update")
        # Ensure instance is setup before updating
        if not self._is_setup:
            self.setup()

        # Update state
        await self.async_update_outputsettings(
            global_update=global_update, cache_id=cache_id
        )
        _LOGGER.debug("Finished OutputSettings update")

    async def async_update_outputsettings(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ):
        """Update OutputSettings status of device."""
        if self._device.use_avr_2016_update is None:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set"
            )

        # OutputSettings is only available for avr 2016 update
        if self._device.use_avr_2016_update:
            try:
                await self.async_update_attrs_appcommand(
                    self.appcommand0300_attrs,
                    appcommand0300=True,
                    global_update=global_update,
                    cache_id=cache_id,
                )
            except AvrProcessingError as err:
                # Don't raise an error here, because not all devices support it
                _LOGGER.debug("Updating OutputSettings failed: %s", err)

    async def _async_set_outputsettings(self, cmd: AppCommandCmd) -> None:
        """Set OutputSettings parameter."""
        res = await self._device.api.async_post_appcommand(
            self._device.urls.appcommand0300, (cmd,)
        )

        try:
            if res.find("cmd").text != "OK":
                raise AvrProcessingError(f"SetOutputSettings command {cmd.name} failed")
        except AttributeError as err:
            raise AvrProcessingError(
                f"SetOutputSettings command {cmd.name} failed"
            ) from err

    ##############
    # Properties #
    ##############

    @property
    def videoout(self) -> Optional[str]:
        """Return value of Video Out."""
        return self._videoout

    ##########
    # Setter #
    ##########

    async def async_set_videoout(self, value: HDMIOutputs) -> None:
        """Set Video Out mode."""
        if self._device.telnet_available:
            setting = HDMI_OUTPUT_MAP_TELNET_REVERSE.get(value)
            if setting is None:
                raise AvrCommandError(f"Value {value} not known for Video Out")
            telnet_command = self._device.telnet_commands.command_hdmi_output.format(
                output=setting
            )
            await self._device.telnet_api.async_send_commands(telnet_command)
            return

        setting = HDMI_OUTPUT_MAP_APPCOMMAND_REVERSE.get(value)
        if setting is None:
            raise AvrCommandError(f"Value {value} not known for Video Out")
        cmd = attr.evolve(
            AppCommands.SetOutputSettingsVideoOut,
            param_list=(AppCommandCmdParam(name="videoout", text=setting),),
        )
        await self._async_set_outputsettings(cmd)


def outputsettings_factory(instance: DenonAVRFoundation) -> DenonAVROutputSettings:
    """Create DenonAVROutputSettings at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVROutputSettings(device=instance._device)
    return new
