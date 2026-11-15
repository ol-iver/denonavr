#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the handling of duplicate telnet events."""

import pytest

from denonavr.api import DenonAVRTelnetApi, _should_propagate_event

# pylint: disable=protected-access


@pytest.fixture(name="events")
def events_fixture():
    """Return a telnet api and the list that collects the callback events."""
    api = DenonAVRTelnetApi()
    received = []
    api.register_callback(
        "SS", lambda zone, event, parameter: received.append(parameter)
    )
    api.register_callback(
        "PS", lambda zone, event, parameter: received.append(parameter)
    )
    return api, received


def test_duplicate_event_is_ignored(events):
    """Test that the same event twice in a row is propagated once."""
    api, received = events
    api._process_event("SSINFSIGRES I 4K60")
    api._process_event("SSINFSIGRES I 4K60")
    assert received == ["INFSIGRES I 4K60"]


def test_changed_event_is_propagated(events):
    """Test that an event with a new value is propagated."""
    api, received = events
    api._process_event("SSINFSIGRES I 4K60")
    api._process_event("SSINFSIGRES I 1080p")
    api._process_event("SSINFSIGRES I 4K60")
    assert received == ["INFSIGRES I 4K60", "INFSIGRES I 1080p", "INFSIGRES I 4K60"]


def test_input_and_output_are_tracked_separately(events):
    """Test that events with different keys do not hide each other."""
    api, received = events
    api._process_event("SSINFSIGRES I 4K60")
    api._process_event("SSINFSIGRES O 4K60")
    assert received == ["INFSIGRES I 4K60", "INFSIGRES O 4K60"]


def test_other_events_are_never_ignored(events):
    """Test that events which are not tracked are always propagated."""
    api, received = events
    api._process_event("PSBAS 50")
    api._process_event("PSBAS 50")
    assert received == ["BAS 50", "BAS 50"]


def test_end_markers_are_ignored(events):
    """Test that end marker events are not propagated."""
    api, received = events
    api._process_event("SSSDV END")
    api._process_event("SSHDMIDIAG END")
    assert not received


def test_clear_duplicate_event_cache(events):
    """Test that an event is propagated again after clearing the cache."""
    api, received = events
    api._process_event("SSINFSIGRES I 4K60")
    api.clear_duplicate_event_cache()
    api._process_event("SSINFSIGRES I 4K60")
    assert received == ["INFSIGRES I 4K60", "INFSIGRES I 4K60"]


def test_should_propagate_event():
    """Test the decision with a custom tracker map."""
    tracker = {"KEY": ""}
    assert _should_propagate_event("SS", "KEY 1", tracker)
    assert not _should_propagate_event("SS", "KEY 1", tracker)
    assert _should_propagate_event("SS", "KEY 2", tracker)
    assert _should_propagate_event("SS", "OTHER", tracker)
    assert _should_propagate_event("SS", "OTHER", tracker)
