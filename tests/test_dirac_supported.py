#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the detection of Dirac support."""

from unittest.mock import AsyncMock, patch
from xml.etree import ElementTree as ET

import pytest

from denonavr.dirac import DenonAVRDirac
from tests.test_helpers import DeviceTestFixture

# pylint: disable=protected-access


def _deviceinfo(filename: str) -> ET.Element:
    with open(f"tests/xml/{filename}", encoding="utf-8") as file:
        return ET.fromstring(file.read())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename, expected",
    [
        ("AVC-A10H-Deviceinfo-8080.xml", True),
        ("AVC-X3700H-Deviceinfo-8080.xml", False),
        ("AVR-X4100W-Deviceinfo.xml", False),
    ],
)
async def test_dirac_support_is_read_from_deviceinfo(filename, expected):
    """Test that Dirac support is detected from Deviceinfo.xml."""
    fixture = DeviceTestFixture(True)
    device = fixture.device_info
    assert device.is_dirac_supported is False
    with patch.object(
        fixture.api,
        "async_get_xml",
        new_callable=AsyncMock,
        return_value=_deviceinfo(filename),
    ):
        await device.async_identify_receiver()

    assert device.is_dirac_supported is expected
    assert DenonAVRDirac(device=device).is_dirac_supported is expected
