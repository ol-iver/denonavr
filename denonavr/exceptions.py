#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST API to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""


class DenonAvrError(Exception):
    """Define an error for Denon AVR."""


class AvrCommandError(DenonAvrError):
    """Define an error command errors."""

    # pylint: disable=useless-super-delegation
    def __init__(self, message: str, *args, **kwargs) -> None:
        """Create a new instance."""
        super().__init__(message, *args, **kwargs)


class AvrProcessingError(DenonAvrError):
    """Define an error for process errors."""

    # pylint: disable=useless-super-delegation
    def __init__(self, message: str, *args, **kwargs) -> None:
        """Create a new instance."""
        super().__init__(message, *args, **kwargs)


class AvrRequestError(DenonAvrError):
    """Define an error related to a HTTP request for Denon AVR."""

    def __init__(self, message: str, request: str, *args, **kwargs) -> None:
        """Create a new instance."""
        self.request = request
        super().__init__(message, *args, **kwargs)


class AvrNetworkError(AvrRequestError):
    """Define a network error during a HTTP request for Denon AVR."""


class AvrTimoutError(AvrRequestError):
    """Define an error for timeouts during a HTTP request for Denon AVR."""


class AvrIncompleteResponseError(AvrRequestError):
    """Define an error for incomplete responses of Denon AVR."""


class AvrInvalidResponseError(AvrRequestError):
    """Define an error for invalid responses of Denon AVR."""


class AvrForbiddenError(AvrRequestError):
    """Define an error for forbidden endpoints (HTTP 403) of Denon AVR."""
