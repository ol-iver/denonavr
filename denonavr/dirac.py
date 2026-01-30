#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Audyssey settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
from typing import Optional, get_args

import attr

from .const import (
    DENON_ATTR_SETATTR,
    DIRAC_FILTER_MAP,
    DIRAC_FILTER_MAP_REVERSE,
    DiracFilters,
)
from .exceptions import AvrCommandError
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRDirac(DenonAVRFoundation):
    """Dirac Settings."""

    _dirac_filter: Optional[str] = attr.ib(
        converter=attr.converters.optional(DIRAC_FILTER_MAP.get), default=None
    )
    _dirac_filters = get_args(DiracFilters)

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        self._device.telnet_api.register_callback("PS", self._ps_callback)

        self._is_setup = True

    def _ps_callback(self, _zone: str, _event: str, parameter: str) -> None:
        """Handle Dirac filter change event."""
        if parameter.startswith("DIRAC"):
            self._dirac_filter = parameter[6:]

    ##############
    # Properties #
    ##############

    @property
    def dirac_filter(self) -> Optional[str]:
        """
        Returns the current Dirac filter.

        Only available if using Telnet.

        Possible values are: "Off", "Slot 1", "Slot 2", "Slot 3"
        """
        return self._dirac_filter

    ##########
    # Setter #
    ##########
    async def async_dirac_filter(self, dirac_filter: DiracFilters) -> None:
        """Set Dirac filter."""
        if dirac_filter not in self._dirac_filters:
            raise AvrCommandError("Invalid Dirac filter")

        if self._dirac_filter == dirac_filter:
            return

        mapped_filter = DIRAC_FILTER_MAP_REVERSE[dirac_filter]
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_dirac_filter.format(
                    filter=mapped_filter
                )
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_dirac_filter.format(filter=mapped_filter)
        )


def dirac_factory(instance: DenonAVRFoundation) -> DenonAVRDirac:
    """Create DenonAVRDirac at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRDirac(device=instance._device)
    return new
