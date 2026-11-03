#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the update_running property of the telnet api."""

import asyncio

import pytest

from denonavr.api import DenonAVRTelnetApi

# pylint: disable=protected-access


def test_update_running_is_false_without_update():
    """Test that no update is running by default."""
    assert DenonAVRTelnetApi().update_running is False


@pytest.mark.asyncio
async def test_update_running_while_update_task_runs():
    """Test that the property is true until the update task has finished."""
    api = DenonAVRTelnetApi()
    release = asyncio.Event()
    task = asyncio.create_task(release.wait())
    api._update_callback_tasks.add(task)
    task.add_done_callback(api._update_callback_tasks.discard)

    assert api.update_running is True

    release.set()
    await task
    await asyncio.sleep(0)
    assert api.update_running is False


@pytest.mark.asyncio
async def test_update_running_is_false_after_cancel():
    """Test that a cancelled update task does not count as running."""
    api = DenonAVRTelnetApi()
    task = asyncio.create_task(asyncio.Event().wait())
    api._update_callback_tasks.add(task)
    task.add_done_callback(api._update_callback_tasks.discard)

    task.cancel()
    await asyncio.gather(task, return_exceptions=True)
    assert api.update_running is False
