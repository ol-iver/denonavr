#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for input source events of zone 2 and zone 3."""

import pytest

from denonavr.api import DenonAVRTelnetApi

# pylint: disable=protected-access


@pytest.fixture(name="events")
def events_fixture():
    """Return a telnet api and the list that collects the SI events."""
    api = DenonAVRTelnetApi()
    received = []
    api.register_callback(
        "SI", lambda zone, event, parameter: received.append((zone, event, parameter))
    )
    return api, received


@pytest.mark.parametrize(
    "message, zone, source",
    [
        ("Z2GAME", "Zone2", "GAME"),
        ("Z2GAME1", "Zone2", "GAME1"),
        ("Z2GAME2", "Zone2", "GAME2"),
        ("Z28K", "Zone2", "8K"),
        ("Z3GAME1", "Zone3", "GAME1"),
        ("Z3GAME2", "Zone3", "GAME2"),
        ("Z38K", "Zone3", "8K"),
    ],
)
def test_source_change_in_zone_2_and_3_is_an_input_event(events, message, zone, source):
    """Test that a source change in zone 2 or 3 reaches the input callbacks."""
    api, received = events
    api._process_event(message)
    assert received == [(zone, "SI", source)]


@pytest.mark.parametrize("message", ["SIGAME1", "SIGAME2", "SI8K"])
def test_source_change_in_main_zone(events, message):
    """Test that a source change in the main zone reaches the input callbacks."""
    api, received = events
    api._process_event(message)
    assert received == [("Main", "SI", message[2:])]
