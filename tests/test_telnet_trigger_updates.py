"""Tests for the state queries sent after a telnet connection."""

import logging

import pytest

from denonavr.api import DenonAVRTelnetApi

# pylint: disable=protected-access


@pytest.mark.asyncio
async def test_trigger_updates_logs_lost_connection_instead_of_raising(caplog):
    """Test that a connection lost during the state queries does not raise.

    The queries run in a task that nothing awaits, so an error raised there
    reaches the event loop as "Task exception was never retrieved".
    """
    api = DenonAVRTelnetApi()
    # Enabled but without a protocol: the connection dropped after connecting.
    api._connection_enabled = True

    with caplog.at_level(logging.DEBUG, logger="denonavr.api"):
        await api._async_trigger_updates()

    assert "Failed updating state after telnet connect" in caplog.text
