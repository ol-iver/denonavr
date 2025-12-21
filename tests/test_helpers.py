#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module contains helper functions for tests.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""
from typing import Any, Awaitable
from unittest.mock import AsyncMock, PropertyMock, patch

from denonavr.api import DenonAVRApi, DenonAVRTelnetApi
from denonavr.foundation import DenonAVRDeviceInfo


class DeviceTestFixture:
    """Test fixture for Denon AVR devices."""

    _mock_get: AsyncMock
    _mock_post: AsyncMock
    _mock_telnet: AsyncMock

    def __init__(self, is_denon: bool) -> None:
        """Initialize the test fixture."""
        self.api = DenonAVRApi()
        self.telnet_api = DenonAVRTelnetApi()
        self.device_info = DenonAVRDeviceInfo(
            api=self.api, telnet_api=self.telnet_api, zone="Main"
        )
        self.device_info.manufacturer = "Denon" if is_denon else "Marantz"

    async def async_execute(self, action: Awaitable[Any]):
        """Execute an async action within the patched context."""
        with patch.object(
            type(self.device_info),
            "telnet_available",
            new_callable=PropertyMock,
            return_value=True,
        ), patch.object(
            self.api, "async_get_command", new_callable=AsyncMock
        ) as mock_get, patch.object(
            self.api, "async_post_appcommand", new_callable=AsyncMock
        ) as mock_post, patch.object(
            self.telnet_api, "async_send_commands", new_callable=AsyncMock
        ) as mock_telnet:
            await action

        self._mock_get = mock_get
        self._mock_post = mock_post
        self._mock_telnet = mock_telnet

    def assert_called_once(self):
        """Assert that exactly one of the mocked methods was called once."""
        assert (
            self._mock_get.call_count
            + self._mock_post.call_count
            + self._mock_telnet.call_count
        ) == 1

    def assert_not_called(self):
        """Assert that none of the mocked methods were called."""
        assert (
            self._mock_get.call_count
            + self._mock_post.call_count
            + self._mock_telnet.call_count
        ) == 0

    def assert_called(self):
        """Assert that at least one of the mocked methods was called."""
        assert (
            self._mock_get.call_count
            + self._mock_post.call_count
            + self._mock_telnet.call_count
        ) > 0
