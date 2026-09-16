#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the API helpers of Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import pytest
from defusedxml.ElementTree import fromstring

from denonavr.api import appcommand_status


class TestAppCommandStatus:
    """Test case for the AppCommand(0300) setter response parser."""

    @pytest.mark.parametrize(
        "response,expected",
        [
            # ver-2 setters answer with the status as text of <cmd>
            ("<rx><cmd>OK</cmd></rx>", "OK"),
            ("<rx><cmd>Error</cmd></rx>", "Error"),
            # ver-1 setters nest it one level deeper
            ("<rx><cmd><value>OK</value></cmd></rx>", "OK"),
            ("<rx><cmd>\n<value>OK</value>\n</cmd></rx>", "OK"),
            # nothing usable
            ("<rx><cmd></cmd></rx>", None),
            ("<rx><cmd><value></value></cmd></rx>", None),
            ("<rx><error>2</error></rx>", None),
        ],
    )
    def test_both_response_shapes(self, response, expected):
        """Check that both command versions report their status."""
        assert appcommand_status(fromstring(response)) == expected
