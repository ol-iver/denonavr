#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the AppCommand(0300) command table.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import importlib
import inspect
import pkgutil

import attr
import pytest

import denonavr
from denonavr.appcommand import AppCommandCmd, AppCommands


def _known_commands():
    """Return every AppCommandCmd declared in the command table."""
    return {
        name: cmd
        for name, cmd in vars(AppCommands).items()
        if isinstance(cmd, AppCommandCmd)
    }


def _declared_attributes():
    """Return every attrs attribute in the package, mapped to its converters."""
    attributes = {}
    for module_info in pkgutil.iter_modules(denonavr.__path__):
        module = importlib.import_module(f"denonavr.{module_info.name}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if not attr.has(cls) or cls.__module__ != module.__name__:
                continue
            for field in attr.fields(cls):
                attributes.setdefault(field.name, []).append(
                    (cls.__name__, field.converter)
                )
    return attributes


def _response_patterns():
    """Return every (command name, response pattern) pair in the table."""
    return [
        pytest.param(cmd_name, pattern, id=f"{cmd_name}-{pattern.update_attribute}")
        for cmd_name, cmd in sorted(_known_commands().items())
        for pattern in cmd.response_pattern
    ]


class TestResponsePatternTargets:
    """
    Test case for the targets of AppCommand response patterns.

    update_attribute is a string applied with setattr, so a typo or a renamed
    attribute fails silently at runtime: the response is parsed, the value is
    written to an attribute nobody reads, and the real one stays None.
    """

    @pytest.mark.parametrize("cmd_name,pattern", _response_patterns())
    def test_target_attribute_exists(self, cmd_name, pattern):
        """Check that every response pattern targets a declared attribute."""
        assert pattern.update_attribute in _declared_attributes(), (
            f"{cmd_name} writes to {pattern.update_attribute}, which no attrs "
            f"class in denonavr declares"
        )

    @pytest.mark.parametrize("cmd_name,pattern", _response_patterns())
    def test_target_attribute_has_converter(self, cmd_name, pattern):
        """Check that every target converts the string the XML layer hands it."""
        owners = _declared_attributes().get(pattern.update_attribute, [])
        without = [name for name, converter in owners if converter is None]
        assert not without, (
            f"{cmd_name} writes the XML string for {pattern.update_attribute} to "
            f"{', '.join(without)}, which declares it without a converter"
        )
