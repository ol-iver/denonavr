#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Audyssey settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging

from typing import Hashable, List, Optional

import attr

from .appcommand import AppCommandCmd, AppCommandCmdParam, AppCommands
from .const import (
    DENON_ATTR_SETATTR, DYNAMIC_VOLUME_MAP, DYNAMIC_VOLUME_MAP_LABELS,
    MULTI_EQ_MAP, MULTI_EQ_MAP_LABELS, REF_LVL_OFFSET_MAP,
    REF_LVL_OFFSET_MAP_LABELS)
from .foundation import DenonAVRFoundation, convert_string_int_bool
from .exceptions import AvrCommandError, AvrProcessingError

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRAudyssey(DenonAVRFoundation):
    """Audyssey Settings."""

    _dynamiceq: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _dynamiceq_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _reflevoffset: Optional[str] = attr.ib(
        converter=attr.converters.optional(REF_LVL_OFFSET_MAP.get),
        default=None)
    _reflevoffset_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _dynamicvol: Optional[str] = attr.ib(
        converter=attr.converters.optional(DYNAMIC_VOLUME_MAP.get),
        default=None)
    _dynamicvol_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)
    _multeq: Optional[str] = attr.ib(
        converter=attr.converters.optional(MULTI_EQ_MAP.get),
        default=None)
    _multeq_control: Optional[bool] = attr.ib(
        converter=attr.converters.optional(convert_string_int_bool),
        default=None)

    # Update tags for attributes
    # AppCommand0300.xml interface
    appcommand0300_attrs = {
        AppCommands.GetAudyssey: None}

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        # Add tags for a potential AppCommand.xml update
        for tag in self.appcommand0300_attrs:
            self._device.api.add_appcommand0300_update_tag(tag)

        self._is_setup = True

    async def async_update(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None) -> None:
        """Update Audyssey asynchronously."""
        # Ensure instance is setup before updating
        if self._is_setup is False:
            self.setup()

        # Update state
        await self.async_update_audyssey(
            global_update=global_update, cache_id=cache_id)

    async def async_update_audyssey(
            self,
            global_update: bool = False,
            cache_id: Optional[Hashable] = None):
        """Update Audyssey status of device."""
        if self._device.use_avr_2016_update is True:
            await self.async_update_attrs_appcommand(
                self.appcommand0300_attrs,
                appcommand0300=True,
                global_update=global_update,
                cache_id=cache_id,
                ignore_missing_response=True)
        elif self._device.use_avr_2016_update is False:
            # Not available
            pass
        else:
            raise AvrProcessingError(
                "Device is not setup correctly, update method not set")

    async def _async_set_audyssey(self, cmd: AppCommandCmd) -> None:
        """Set Audyssey parameter."""
        res = await self._device.api.async_post_appcommand(
            self._device.urls.appcommand0300, (cmd,))

        try:
            if res.find("cmd").text != "OK":
                raise AvrProcessingError(
                    "SetAudyssey command {} failed".format(cmd.name))
        except AttributeError as err:
            raise AvrProcessingError(
                "SetAudyssey command {} failed".format(cmd.name)) from err

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
        return list(REF_LVL_OFFSET_MAP_LABELS.keys())

    @property
    def dynamic_volume(self) -> Optional[str]:
        """Return value of Dynamic Volume."""
        return self._dynamicvol

    @property
    def dynamic_volume_setting_list(self) -> List[str]:
        """Return a list of available Dynamic Volume settings."""
        return list(DYNAMIC_VOLUME_MAP_LABELS.keys())

    @property
    def multi_eq(self) -> Optional[str]:
        """Return value of MultiEQ."""
        return self._multeq

    @property
    def multi_eq_setting_list(self) -> List[str]:
        """Return a list of available MultiEQ settings."""
        return list(MULTI_EQ_MAP_LABELS.keys())

    ##########
    # Setter #
    ##########
    async def async_dynamiceq_off(self) -> None:
        """Turn DynamicEQ off."""
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicEQ, param_list=(
                AppCommandCmdParam(name="dynamiceq", text=0),))
        await self._async_set_audyssey(cmd)

    async def async_dynamiceq_on(self) -> None:
        """Turn DynamicEQ on."""
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicEQ, param_list=(
                AppCommandCmdParam(name="dynamiceq", text=1),))
        await self._async_set_audyssey(cmd)

    async def async_set_multieq(self, value: str) -> None:
        """Set MultiEQ mode."""
        setting = MULTI_EQ_MAP_LABELS.get(value)
        if setting is None:
            raise AvrCommandError(
                "Value {} not known for MultiEQ".format(value))
        cmd = attr.evolve(
            AppCommands.SetAudysseyMultiEQ, param_list=(
                AppCommandCmdParam(name="multeq", text=setting),))
        await self._async_set_audyssey(cmd)

    async def async_set_reflevoffset(self, value: str) -> None:
        """Set Reference Level Offset."""
        # Reference level offset can only be used with DynamicEQ
        if self._dynamiceq is False:
            raise AvrCommandError(
                "Reference level could only be set when DynamicEQ is active")
        setting = REF_LVL_OFFSET_MAP_LABELS.get(value)
        if setting is None:
            raise AvrCommandError(
                "Value {} not known for Reference level offset".format(value))
        cmd = attr.evolve(
            AppCommands.SetAudysseyReflevoffset, param_list=(
                AppCommandCmdParam(name="reflevoffset", text=setting),))
        await self._async_set_audyssey(cmd)

    async def async_set_dynamicvol(self, value: str) -> None:
        """Set Dynamic Volume."""
        setting = DYNAMIC_VOLUME_MAP_LABELS.get(value)
        if setting is None:
            raise AvrCommandError(
                "Value {} not known for Dynamic Volume".format(value))
        cmd = attr.evolve(
            AppCommands.SetAudysseyDynamicvol, param_list=(
                AppCommandCmdParam(name="dynamicvol", text=setting),))
        await self._async_set_audyssey(cmd)

    async def async_toggle_dynamic_eq(self) -> None:
        """Toggle DynamicEQ."""
        if self._dynamiceq is True:
            await self.async_dynamiceq_off()
        else:
            await self.async_dynamiceq_on()


def audyssey_factory(instance: DenonAVRFoundation) -> DenonAVRAudyssey:
    """Create  DenonAVRAudyssey at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRAudyssey(device=instance._device)
    return new
