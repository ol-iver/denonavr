#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Audyssey settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging
from typing import Optional

import attr

from .const import (
    DENON_ATTR_SETATTR,
    DIRAC_FILTER_MAP,
    DIRAC_FILTER_MAP_LABELS,
    DiracFilters,
)
from .exceptions import AvrCommandError
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRDirac(DenonAVRFoundation):
    """Dirac Settings."""

    _dirac_filter: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None
    )

    def setup(self) -> None:
        """Ensure that the instance is initialized."""
        self._device.telnet_api.register_callback(
            "PS", self._async_dirac_filter_callback
        )
        self._is_setup = True

    async def _async_dirac_filter_callback(
        self, zone: str, event: str, parameter: str
    ) -> None:
        """Handle Dirac filter change event."""
        if event == "PS" and parameter[0:5] == "DIRAC":
            self._dirac_filter = DIRAC_FILTER_MAP_LABELS[parameter[6:]]

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
        if dirac_filter not in DiracFilters:
            raise AvrCommandError("Invalid Dirac filter")

        mapped_filter = DIRAC_FILTER_MAP[dirac_filter]
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
