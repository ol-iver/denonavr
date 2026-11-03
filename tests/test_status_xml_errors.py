#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the error handling when updating the status XML."""

from unittest.mock import patch
from xml.etree import ElementTree as ET

import pytest

from denonavr.exceptions import AvrNetworkError, AvrRequestError, AvrTimoutError
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [AvrNetworkError("down", "req"), AvrTimoutError("timeout", "req")],
)
async def test_connection_errors_are_raised(error):
    """Test that connection errors are not skipped."""
    device = DeviceTestFixture(True).device_info
    with patch.object(device.api, "async_get_xml", side_effect=error):
        with pytest.raises(type(error)):
            await device.async_update_status_xml()


@pytest.mark.asyncio
async def test_connection_error_stops_after_first_url():
    """Test that no more URLs are tried after a connection error."""
    device = DeviceTestFixture(True).device_info
    with patch.object(
        device.api, "async_get_xml", side_effect=AvrTimoutError("timeout", "req")
    ) as mock_get:
        with pytest.raises(AvrTimoutError):
            await device.async_update_status_xml()

    assert mock_get.await_count == 1


@pytest.mark.asyncio
async def test_other_request_errors_skip_the_url():
    """Test that other request errors skip the URL."""
    device = DeviceTestFixture(True).device_info
    with patch.object(
        device.api, "async_get_xml", side_effect=AvrRequestError("error", "req")
    ) as mock_get:
        await device.async_update_status_xml()

    assert mock_get.await_count == 2


@pytest.mark.asyncio
async def test_power_is_read_from_status_xml():
    """Test that the status is still read when no error happens."""
    device = DeviceTestFixture(True).device_info
    xml = ET.fromstring("<item><Power><value>ON</value></Power></item>")
    with patch.object(device.api, "async_get_xml", return_value=xml):
        await device.async_update_status_xml()

    assert device.power == "ON"
