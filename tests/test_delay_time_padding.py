#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the value of the async_delay_time command."""

import pytest

from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "delay_time, expected",
    [(0, "PSDEL 000"), (5, "PSDEL 005"), (50, "PSDEL 050"), (100, "PSDEL 100")],
)
async def test_async_delay_time_pads_value_to_three_digits(delay_time, expected):
    """Test that the receiver gets the delay time with three digits."""
    fixture = DeviceTestFixture(True)
    await fixture.async_execute(fixture.device_info.async_delay_time(delay_time))
    fixture._mock_telnet.assert_called_once_with(expected)


def test_http_command_still_accepts_up_and_down():
    """Test that the command text works for numbers and for UP and DOWN."""
    url = DeviceTestFixture(True).device_info.urls.command_delay_time
    assert url.format(value="005").endswith("PSDEL%20005")
    assert url.format(value="UP").endswith("PSDEL%20UP")
