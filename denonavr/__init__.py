#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Automation Library for Denon AVR receivers.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

# Set default logging handler to avoid "No handler found" warnings.
import logging

# Import denonavr module
from .denonavr import DenonAVR

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        """Null Handler."""

        def emit(self, record):
            """Emit."""
            pass

logging.getLogger(__name__).addHandler(NullHandler())

__title__ = "denonavr"
__version__ = "0.1.6"
