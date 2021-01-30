#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for ssdp."""

import pytest
from denonavr.ssdp import evaluate_scpd_xml


def get_sample_content(filename):
    """Return sample content form file."""
    with open(
            "tests/xml/{filename}".format(
                filename=filename), encoding="utf-8") as file:
        return file.read()


@pytest.mark.parametrize(
    "model,expected_device",
    [
        (
            "AVR-X1600H",
            {
                "friendlyName": "Denon AVR-X1600H",
                "host": "10.0.0.0",
                "manufacturer": "Denon",
                "modelName": "Denon AVR-X1600H",
                "serialNumber": "XXX",
            },
        )
    ],
)
def test_evaluate(model, expected_device):
    """Test that the discovered device looks like expected."""
    url = "https://10.0.0.0/denon"
    body = get_sample_content("{model}_upnp.xml".format(model=model))
    device = evaluate_scpd_xml(url, body)
    assert device == expected_device
