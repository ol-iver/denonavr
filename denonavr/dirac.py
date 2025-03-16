#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the Audyssey settings of Denon AVR receivers.

:copyright: (c) 2020 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import logging

import attr

from .const import (
    DENON_ATTR_SETATTR,
    DiracFilter,
)
from .foundation import DenonAVRFoundation

_LOGGER = logging.getLogger(__name__)


@attr.s(auto_attribs=True, on_setattr=DENON_ATTR_SETATTR)
class DenonAVRDirac(DenonAVRFoundation):
    """Dirac Settings."""

    ##########
    # Setter #
    ##########
    async def async_diract_filter(
        self, dirac_filter: DiracFilter
    ) -> None:
        """Set Dirac filter."""
        if self._device.telnet_available:
            await self._device.telnet_api.async_send_commands(
                self._device.telnet_commands.command_dirac_filter.format(
                    filter=dirac_filter
                )
            )
            return
        await self._device.api.async_get_command(
            self._device.urls.command_dirac_filter.format(filter=dirac_filter)
        )


def dirac_factory(instance: DenonAVRFoundation) -> DenonAVRDirac:
    """Create DenonAVRDirac at receiver instances."""
    # pylint: disable=protected-access
    new = DenonAVRDirac(device=instance._device)
    return new
