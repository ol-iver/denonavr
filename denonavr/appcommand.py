#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements foundation for AppCommand(0300) of Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from typing import Optional, Tuple

import attr


@attr.s(auto_attribs=True, frozen=True)
class AppCommandCmdParam:
    """AppCommand param data type."""

    name: str = attr.ib(converter=str)
    text: str = attr.ib(converter=str, default="")


@attr.s(auto_attribs=True, frozen=True)
class AppCommandResponsePattern:
    """
    AppCommand response pattern data type.

    Use it to configure the search pattern in AppCommand response.
    """

    update_attribute: str = attr.ib(converter=str)
    add_zone: bool = attr.ib(converter=bool, default=True)
    suffix: str = attr.ib(converter=str, default="")
    get_xml_attribute: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)


@attr.s(auto_attribs=True, frozen=True)
class AppCommandCmd:
    """AppCommand data type."""

    cmd_id: str = attr.ib(converter=str)
    cmd_text: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    name: Optional[str] = attr.ib(
        converter=attr.converters.optional(str), default=None)
    param_list: Optional[Tuple[AppCommandCmdParam]] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.deep_iterable(
                attr.validators.instance_of(AppCommandCmdParam),
                attr.validators.instance_of(tuple))),
        default=None)
    set_command: Optional[AppCommandCmdParam] = attr.ib(
        validator=attr.validators.optional(
            attr.validators.instance_of(AppCommandCmdParam)),
        default=None)
    response_pattern: Tuple[AppCommandResponsePattern] = attr.ib(
        validator=attr.validators.deep_iterable(
                attr.validators.instance_of(AppCommandResponsePattern),
                attr.validators.instance_of(tuple)),
        default=attr.Factory(tuple))


class AppCommands:
    """Collect known AppCommand.xml tags."""

    GetAllZoneMuteStatus = AppCommandCmd(
        cmd_id=1, cmd_text="GetAllZoneMuteStatus",
        response_pattern=(AppCommandResponsePattern(
            update_attribute="_muted", add_zone=True, suffix=""),))
    GetAllZonePowerStatus = AppCommandCmd(
        cmd_id=1, cmd_text="GetAllZonePowerStatus",
        response_pattern=(AppCommandResponsePattern(
            update_attribute="_power", add_zone=True, suffix=""),))
    GetAllZoneSource = AppCommandCmd(
        cmd_id=1, cmd_text="GetAllZoneSource",
        response_pattern=(AppCommandResponsePattern(
            update_attribute="_input_func", add_zone=True, suffix="/source"),))
    GetAllZoneVolume = AppCommandCmd(
        cmd_id=1, cmd_text="GetAllZoneVolume",
        response_pattern=(AppCommandResponsePattern(
            update_attribute="_volume", add_zone=True, suffix="/volume"),))

    GetSurroundModeStatus = AppCommandCmd(
        cmd_id=1, cmd_text="GetSurroundModeStatus",
        response_pattern=(AppCommandResponsePattern(
            update_attribute="_sound_mode_raw", add_zone=False,
            suffix="/surround"),))

    GetToneControl = AppCommandCmd(
        cmd_id=1, cmd_text="GetToneControl",
        response_pattern=(
            AppCommandResponsePattern(
                update_attribute="_tone_control_status", add_zone=False,
                suffix="/status"),
            AppCommandResponsePattern(
                update_attribute="_tone_control_adjust", add_zone=False,
                suffix="/adjust"),
            AppCommandResponsePattern(
                update_attribute="_bass_level", add_zone=False,
                suffix="/basslevel"),
            AppCommandResponsePattern(
                update_attribute="_bass", add_zone=False,
                suffix="/bassvalue"),
            AppCommandResponsePattern(
                update_attribute="_treble_level", add_zone=False,
                suffix="/treblelevel"),
            AppCommandResponsePattern(
                update_attribute="_treble", add_zone=False,
                suffix="/treblevalue")))
    # Replace set command with a real command using attr.evolve
    SetToneControl = AppCommandCmd(
        cmd_id=1, cmd_text="SetToneControl",
        set_command=AppCommandCmdParam(name="REPLACE", text="REPLACE"))

    GetRenameSource = AppCommandCmd(cmd_id=1, cmd_text="GetRenameSource")
    GetDeletedSource = AppCommandCmd(cmd_id=1, cmd_text="GetDeletedSource")

    GetFriendlyName = AppCommandCmd(cmd_id=1, cmd_text="GetFriendlyName")

    GetAudyssey = AppCommandCmd(
        cmd_id=3,
        name="GetAudyssey",
        param_list=(
            AppCommandCmdParam(name="dynamiceq"),
            AppCommandCmdParam(name="reflevoffset"),
            AppCommandCmdParam(name="dynamicvol"),
            AppCommandCmdParam(name="multeq")),
        response_pattern=(
            AppCommandResponsePattern(
                update_attribute="_multeq", add_zone=False,
                suffix="/list/param[@name='multeq']"),
            AppCommandResponsePattern(
                update_attribute="_multeq_control", add_zone=False,
                suffix="/list/param[@name='multeq']",
                get_xml_attribute="control"),
            AppCommandResponsePattern(
                update_attribute="_dynamiceq", add_zone=False,
                suffix="/list/param[@name='dynamiceq']"),
            AppCommandResponsePattern(
                update_attribute="_dynamiceq_control", add_zone=False,
                suffix="/list/param[@name='dynamiceq']",
                get_xml_attribute="control"),
            AppCommandResponsePattern(
                update_attribute="_reflevoffset", add_zone=False,
                suffix="/list/param[@name='reflevoffset']"),
            AppCommandResponsePattern(
                update_attribute="_reflevoffset_control", add_zone=False,
                suffix="/list/param[@name='reflevoffset']",
                get_xml_attribute="control"),
            AppCommandResponsePattern(
                update_attribute="_dynamicvol", add_zone=False,
                suffix="/list/param[@name='dynamicvol']"),
            AppCommandResponsePattern(
                update_attribute="_dynamicvol_control", add_zone=False,
                suffix="/list/param[@name='dynamicvol']",
                get_xml_attribute="control")))
    SetAudysseyDynamicEQ = AppCommandCmd(
        cmd_id=3,
        name="SetAudyssey",
        param_list=(AppCommandCmdParam(name="dynamiceq", text="REPLACE"),))
    SetAudysseyMultiEQ = AppCommandCmd(
        cmd_id=3,
        name="SetAudyssey",
        param_list=(AppCommandCmdParam(name="multieq", text="REPLACE"),))
    SetAudysseyReflevoffset = AppCommandCmd(
        cmd_id=3,
        name="SetAudyssey",
        param_list=(AppCommandCmdParam(name="reflevoffset", text="REPLACE"),))
    SetAudysseyDynamicvol = AppCommandCmd(
        cmd_id=3,
        name="SetAudyssey",
        param_list=(AppCommandCmdParam(name="dynamicvol", text="REPLACE"),))
