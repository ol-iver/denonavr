#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Audyssey settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
from collections.abc import Hashable
from typing import List, Optional

import attr

from .appcommand import AppCommandCmd, AppCommandCmdParam, AppCommands
from .const import (
    DENON_ATTR_SETATTR,
    DYNAMIC_VOLUME_MAP,
    DYNAMIC_VOLUME_MAP_LABELS_APPCOMMAND,
    DYNAMIC_VOLUME_MAP_LABELS_TELNET,
    MULTI_EQ_MAP,
    MULTI_EQ_MAP_LABELS_APPCOMMAND,
    MULTI_EQ_MAP_LABELS_TELNET,
    REF_LVL_OFFSET_MAP,
    REF_LVL_OFFSET_MAP_LABELS_APPCOMMAND,
    REF_LVL_OFFSET_MAP_LABELS_TELNET,
)
from .exceptions import AvrCommandError, AvrProcessingError
from .foundation import DenonAVRFoundation, convert_string_int_bool

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRAudyssey(DenonAVRFoundation):
    """Audyssey Settings."""

    _dynamiceq: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _dynamiceq_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _reflevoffset: Optional[str] = attr.ib(
        converter=attr.converters.optional(REF_LVL_OFFSET_MAP.get), default=None
    )
    _reflevoffset_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _dynamicvol: Optional[str] = attr.ib(
        converter=attr.converters.optional(DYNAMIC_VOLUME_MAP.get), default=None
    )
    _dynamicvol_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _multeq: Optional[str] = attr.ib(
        converter=attr.converters.optional(MULTI_EQ_MAP.get), default=None
    )
    _multeq_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _lfc: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool), default=None
    )
    _containment_amount: Optional[int] = attr.ib(
        converter=attr.converters.optional(int), default=None
    )

    # Update tags for attributes
    # AppCommand0300.xml interface
    appcommand0300_attrs = {AppCommands.GetAudyssey: None}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        for tag in self.appcommand0300_attrs:
            self._device.api.add_appcommand0300_update_tag(tag)

        self._device.telnet_api.register_callback(
            "PS", self._async_sound_detail_callback
        )

        self._is_setup = True

    async def _async_sound_detail_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle a sound detail change event."""
        if self._device.zone != zone:
            return

        if parameter[0:6] == "REFLEV":
            self._reflevoffset = parameter[7:]
        elif parameter[0:6] == "DYNVOL":
            self._dynamicvol = parameter[7:]
        elif parameter[0:6] == "MULTEQ":
            self._multeq = parameter[7:]
        elif parameter == "DYNEQ ON":
            self._dynamiceq = "1"
        elif parameter == "DYNEQ OFF":
            self._dynamiceq = "0"
        elif parameter == "LFC ON":
            self._lfc = "1"
        elif parameter == "LFC OFF":
            self._lfc = "0"
        elif parameter[:6] == "CNTAMT":
            self._containment_amount = int(parameter[7:])

    async def async_update(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ) -> None:
        """Update Audyssey asynchronously."""
        _LOGGER.debug("Starting Audyssey update")
        # Ensure instance is setup before updating
        if not self._is_setup:
            self.setup()

        # Update state
        await self.async_update_audyssey(global_update=global_update, cache_id=cache_id)
        _LOGGER.debug("Finished Audyssey update")

    async def async_update_audyssey(
        self, global_update: bool = False, cache_id: Optional[Hashable] = None
    ):
        """Update Audyssey status of device."""
        if self._device.use_avr_2016_update is None:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set"
            )

        # Audyssey is only available for avr 2016 update
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
                _LOGGER.debug("Updating Audyssey failed: %s", err)

    async def _async_set_audyssey(self, cmd: AppCommandCmd) -> None:
        """Set Audyssey parameter."""
        res = await self._device.api.async_post_appcommand(
            self._device.urls.appcommand0300, (cmd,)
        )

        try:
            if res.find("cmd").text != "OK":
                raise AvrProcessingError(f"SetAudyssey command {cmd.name} failed")
        except AttributeError as err:
            raise AvrProcessingError(f"SetAudyssey command {cmd.name} failed") from err

    ##############
    # Properties #
    ##############
    @property
    def dynamic_eq(self) -> Optional[bool]:
        """Return value of Dynamic EQ."""
        return self._dynamiceq

    @property
    def reference_level_offset(self) -> Optional[str]:
        """Return value of Reference Level Offset."""
        return self._reflevoffset

    @property
    def reference_level_offset_setting_list(self) -> List[str]:
        """Return a list of available reference level offset settings."""
        if self._device.telnet_available:
            return list(REF_LVL_OFFSET_MAP_LABELS_TELNET.keys())
        return list(REF_LVL_OFFSET_MAP_LABELS_APPCOMMAND.keys())

    @property
    def dynamic_volume(self) -> Optional[str]:
        """Return value of Dynamic Volume."""
        return self._dynamicvol

    @property
    def dynamic_volume_setting_list(self) -> List[str]:
        """Return a list of available Dynamic Volume settings."""
        if self._device.telnet_available:
            return list(DYNAMIC_VOLUME_MAP_LABELS_TELNET.keys())
        return list(DYNAMIC_VOLUME_MAP_LABELS_APPCOMMAND.keys())

    @property
    def multi_eq(self) -> Optional[str]:
        """Return value of MultiEQ."""
        return self._multeq

    @property
    def multi_eq_setting_list(self) -> List[str]:
        """Return a list of available MultiEQ settings."""
        if self._device.telnet_available:
            return list(MULTI_EQ_MAP_LABELS_TELNET.keys())
        return list(MULTI_EQ_MAP_LABELS_APPCOMMAND.keys())

    @property
    def lfc(self) -> Optional[bool]:
        """
        Return value of LFC.

        Only available if using Telnet.
        """
        return self._lfc

    @property
    def containment_amount(self) -> Optional[int]:
        """
        Return value of Containment Amount.

        Only available if using Telnet.
        """
        return self._containment_amount

    ##########
    # Setter #
    ##########
    async def async_dynamiceq_off(self) -> None:
        """Turn DynamicEQ off."""
        if self._device.telnet_available:
            telnet_command = self._device.telnet_commands.command_dynamiceq + "OFF"
            await self._device.telnet_api.async_send_commands(telnet_command)
            return
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicEQ,
            param_list=(AppCommandCmdParam(name="dynamiceq", text=0),),
        )
        await self._async_set_audyssey(cmd)

    async def async_dynamiceq_on(self) -> None:
        """Turn DynamicEQ on."""
        if self._device.telnet_available:
            telnet_command = self._device.telnet_commands.command_dynamiceq + "ON"
            await self._device.telnet_api.async_send_commands(telnet_command)
            return
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicEQ,
            param_list=(AppCommandCmdParam(name="dynamiceq", text=1),),
        )
        await self._async_set_audyssey(cmd)

    async def async_set_multieq(self, value: str) -> None:
        """Set MultiEQ mode."""
        if self._device.telnet_available:
            setting = MULTI_EQ_MAP_LABELS_TELNET.get(value)
            if setting is None:
                raise AvrCommandError(f"Value {value} not known for MultiEQ")
            telnet_command = self._device.telnet_commands.command_multieq + setting
            await self._device.telnet_api.async_send_commands(telnet_command)
            return

        setting = MULTI_EQ_MAP_LABELS_APPCOMMAND.get(value)
        if setting is None:
            raise AvrCommandError(f"Value {value} not known for MultiEQ")
        cmd = attr.evolve(
            AppCommands.SetAudysseyMultiEQ,
            param_list=(AppCommandCmdParam(name="multeq", text=setting),),
        )
        await self._async_set_audyssey(cmd)

    async def async_set_reflevoffset(self, value: str) -> None:
        """Set Reference Level Offset."""
        # Reference level offset can only be used with DynamicEQ
        if not self._dynamiceq:
            raise AvrCommandError(
                "Reference level could only be set when DynamicEQ is active"
            )
        if self._device.telnet_available:
            setting = REF_LVL_OFFSET_MAP_LABELS_TELNET.get(value)
            if setting is None:
                raise AvrCommandError(
                    f"Value {value} not known for Reference level offset"
                )
            telnet_command = self._device.telnet_commands.command_reflevoffset + setting
            await self._device.telnet_api.async_send_commands(telnet_command)
            return

        setting = REF_LVL_OFFSET_MAP_LABELS_APPCOMMAND.get(value)
        if setting is None:
            raise AvrCommandError(f"Value {value} not known for Reference level offset")
        cmd = attr.evolve(
            AppCommands.SetAudysseyReflevoffset,
            param_list=(AppCommandCmdParam(name="reflevoffset", text=setting),),
        )
        await self._async_set_audyssey(cmd)

    async def async_set_dynamicvol(self, value: str) -> None:
        """Set Dynamic Volume."""
        if self._device.telnet_available:
            setting = DYNAMIC_VOLUME_MAP_LABELS_TELNET.get(value)
            if setting is None:
                raise AvrCommandError(f"Value {value} not known for Dynamic Volume")
            telnet_command = self._device.telnet_commands.command_dynamicvol + setting
            await self._device.telnet_api.async_send_commands(telnet_command)
            return

        setting = DYNAMIC_VOLUME_MAP_LABELS_APPCOMMAND.get(value)
        if setting is None:
            raise AvrCommandError(f"Value {value} not known for Dynamic Volume")
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicvol,
            param_list=(AppCommandCmdParam(name="dynamicvol", text=setting),),
        )
        await self._async_set_audyssey(cmd)

    async def async_toggle_dynamic_eq(self) -> None:
        """Toggle DynamicEQ."""
        if self._dynamiceq:
            await self.async_dynamiceq_off()
        else:
            await self.async_dynamiceq_on()

    async def async_lfc_on(self):
        """Turn LFC on."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_lfc.format(mode="ON")
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_lfc.format(mode="ON")
        )

    async def async_lfc_off(self):
        """Turn LFC off."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_lfc.format(mode="OFF")
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_lfc.format(mode="OFF")
        )

    async def async_toggle_lfc(self):
        """Toggle LFC."""
        if self._lfc:
            await self.async_lfc_off()
        else:
            await self.async_lfc_on()

    async def async_containment_amount(self, amount: int) -> None:
        """
        Set Containment Amount.

        Valid values are 1-7.
        """
        if amount < 1 or amount > 7:
            raise AvrCommandError("Containment amount must be between 1 and 7")
        local_amount = f"{amount:02}"
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_containment_amount.format(
                    value=local_amount
                )
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_containment_amount.format(value=local_amount)
        )

    async def async_containment_amount_up(self) -> None:
        """Increase Containment Amount."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_containment_amount.format(
                    value="UP"
                )
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_containment_amount.format(value="UP")
        )

    async def async_containment_amount_down(self) -> None:
        """Decrease Containment Amount."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_containment_amount.format(
                    value="DOWN"
                )
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_containment_amount.format(value="DOWN")
        )


def audyssey_factory(instance: DenonAVRFoundation) -> DenonAVRAudyssey:
    """Create  DenonAVRAudyssey at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRAudyssey(device=instance._device)
    return new
