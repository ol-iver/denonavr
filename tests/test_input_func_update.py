#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the update of the input function list after telnet events."""

import asyncio
import logging
from unittest.mock import AsyncMock, patch

import pytest

from denonavr.exceptions import AvrProcessingError
from denonavr.input import DenonAVRInput
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.fixture(name="input_device")
def input_device_fixture():
    """Return an input instance."""
    return DenonAVRInput(device=DeviceTestFixture(True).device_info)


async def _wait_for_tasks(device: DenonAVRInput) -> None:
    while device._callback_tasks:
        await asyncio.gather(*device._callback_tasks, return_exceptions=True)
        await asyncio.sleep(0)


@pytest.mark.asyncio
@pytest.mark.parametrize("parameter", ["FUN", "FUNTV TV Audio", "SODBD ON"])
async def test_rename_and_hide_events_update_inputs(input_device, parameter):
    """Test that renaming or hiding a source updates the input list."""
    with patch.object(
        input_device, "_async_update_inputfuncs", new_callable=AsyncMock
    ) as update:
        input_device._input_func_update_callback("Main", "SS", parameter)
        await _wait_for_tasks(input_device)

    update.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("parameter", ["PST 1", "TTR ON", "HOS ON", "INFSIGRES I 4K"])
async def test_other_setup_events_are_ignored(input_device, parameter):
    """Test that other SS events do not update the input list."""
    with patch.object(
        input_device, "_async_update_inputfuncs", new_callable=AsyncMock
    ) as update:
        input_device._input_func_update_callback("Main", "SS", parameter)
        await _wait_for_tasks(input_device)

    update.assert_not_awaited()
    assert not input_device._callback_tasks


@pytest.mark.asyncio
async def test_events_in_one_read_share_one_update(input_device):
    """Test that events that arrive together cause one update."""

    async def yielding_update(**_kwargs):
        await asyncio.sleep(0)

    update = AsyncMock(side_effect=yielding_update)
    with patch.object(input_device, "_async_update_inputfuncs", update):
        for parameter in ("FUNTV TV", "FUNGAME Game", "SODBD ON"):
            input_device._input_func_update_callback("Main", "SS", parameter)
        await _wait_for_tasks(input_device)

    update.assert_awaited_once()


@pytest.mark.asyncio
async def test_event_during_update_runs_one_more_update(input_device):
    """Test that a change during an update is read with a second update."""
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def slow_update(**_kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()

    with patch.object(
        input_device, "_async_update_inputfuncs", side_effect=slow_update
    ):
        input_device._input_func_update_callback("Main", "SS", "FUNTV TV")
        await started.wait()
        input_device._input_func_update_callback("Main", "SS", "SODBD ON")
        input_device._input_func_update_callback("Main", "SS", "SODSAT ON")
        release.set()
        await _wait_for_tasks(input_device)

    assert calls == 2


@pytest.mark.asyncio
async def test_manual_update_waits_for_running_update(input_device):
    """Test that a second caller waits instead of fetching the sources again."""
    release = asyncio.Event()
    calls = 0

    async def slow_update(**_kwargs):
        nonlocal calls
        calls += 1
        await release.wait()

    with patch.object(
        input_device, "_async_update_inputfuncs", side_effect=slow_update
    ):
        first = asyncio.create_task(input_device.async_update_inputfuncs())
        await asyncio.sleep(0)
        second = asyncio.create_task(input_device.async_update_inputfuncs())
        await asyncio.sleep(0)
        assert not second.done()
        release.set()
        await asyncio.gather(first, second)

    assert calls == 1


@pytest.mark.asyncio
async def test_receiver_errors_are_logged(input_device, caplog):
    """Test that an error in the update task is logged and not raised."""
    with (
        caplog.at_level(logging.WARNING),
        patch.object(
            input_device,
            "_async_update_inputfuncs",
            side_effect=AvrProcessingError("failed"),
        ),
    ):
        input_device._input_func_update_callback("Main", "SS", "FUNTV TV")
        await _wait_for_tasks(input_device)

    assert "AVR error during input functions update" in caplog.text


@pytest.mark.asyncio
async def test_unexpected_errors_are_logged(input_device, caplog):
    """Test that an unexpected error in the update task is logged."""
    with (
        caplog.at_level(logging.ERROR),
        patch.object(
            input_device, "_async_update_inputfuncs", side_effect=RuntimeError("bug")
        ),
    ):
        input_device._input_func_update_callback("Main", "SS", "FUNTV TV")
        await _wait_for_tasks(input_device)

    assert "Unexpected error during input functions update" in caplog.text
