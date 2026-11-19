#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for background telnet commands."""

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from denonavr import api as api_module
from denonavr.api import DenonAVRTelnetApi

# pylint: disable=protected-access


@pytest.fixture(name="short_pause")
def short_pause_fixture(monkeypatch):
    """Use a short pause so tests run fast."""
    monkeypatch.setattr(api_module, "_BACKGROUND_PAUSE_AFTER_COMMAND", 0.05)
    return 0.05


@pytest.mark.asyncio
async def test_background_command_is_sent_when_idle():
    """Test that a background command is sent without delay if no user command ran."""
    api = DenonAVRTelnetApi()
    with patch.object(
        api, "_async_send_command_locked", new_callable=AsyncMock
    ) as sent:
        await api.async_send_commands("HD?", skip_confirmation=True, background=True)

    sent.assert_awaited_once()
    assert api._user_commands_pending == 0


@pytest.mark.asyncio
async def test_background_command_waits_for_user_command(short_pause):
    """Test that a background command is sent after a pending user command."""
    api = DenonAVRTelnetApi()
    order = []
    release = asyncio.Event()

    async def fake_send(command, **_kwargs):
        if command == "USER":
            await release.wait()
        order.append(command)

    with patch.object(api, "_async_send_command_locked", side_effect=fake_send):
        user_task = asyncio.create_task(api.async_send_commands("USER"))
        await asyncio.sleep(0)
        background_task = asyncio.create_task(
            api.async_send_commands("BACKGROUND", background=True)
        )
        await asyncio.sleep(short_pause * 2)
        assert not order

        release.set()
        await asyncio.gather(user_task, background_task)

    assert order == ["USER", "BACKGROUND"]


@pytest.mark.asyncio
async def test_background_command_pauses_after_user_command(short_pause):
    """Test that a background command waits shortly after the last user command."""
    api = DenonAVRTelnetApi()
    with patch.object(api, "_async_send_command_locked", new_callable=AsyncMock):
        await api.async_send_commands("USER")
        start = time.monotonic()
        await api.async_send_commands("BACKGROUND", background=True)

    assert time.monotonic() - start >= short_pause * 0.8


@pytest.mark.asyncio
async def test_user_command_does_not_wait_for_background_command():
    """Test that user commands are never delayed by the background logic."""
    api = DenonAVRTelnetApi()
    with patch.object(
        api, "_async_send_command_locked", new_callable=AsyncMock
    ) as sent:
        await api.async_send_commands("USER")
        await api.async_send_commands("USER")

    assert sent.await_count == 2


@pytest.mark.asyncio
async def test_pending_user_commands_are_reset_after_error():
    """Test that a failing user command does not block background commands."""
    api = DenonAVRTelnetApi()
    with patch.object(
        api, "_async_send_command_locked", side_effect=RuntimeError("failed")
    ):
        with pytest.raises(RuntimeError):
            await api.async_send_commands("USER")

    assert api._user_commands_pending == 0
    assert api._user_commands_idle.is_set()


@pytest.mark.asyncio
async def test_send_commands_passes_background_flag():
    """Test that send_commands forwards the background flag."""
    api = DenonAVRTelnetApi()
    with patch.object(api, "async_send_commands", new_callable=AsyncMock) as send:
        api.send_commands("HD?", skip_confirmation=True, background=True)
        await asyncio.gather(*api._send_tasks)

    send.assert_awaited_once_with(
        "HD?", skip_confirmation=True, confirmation_timeout=None, background=True
    )


def test_pause_after_user_command_is_in_the_range_of_the_protocol():
    """Test that the pause is 50 to 100 ms, the interval between commands."""
    assert 0.05 <= api_module._BACKGROUND_PAUSE_AFTER_COMMAND <= 0.1
