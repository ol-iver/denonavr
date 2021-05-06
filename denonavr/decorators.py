#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST API to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import asyncio
import inspect
import logging
import time
import xml.etree.ElementTree as ET

from functools import wraps
from typing import Callable, Coroutine

import httpx

from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError

from .exceptions import (
    AvrRequestError,
    AvrForbiddenError,
    AvrNetworkError,
    AvrTimoutError,
    AvrInvalidResponseError)

_LOGGER = logging.getLogger(__name__)


def async_handle_receiver_exceptions(func: Coroutine) -> Coroutine:
    """
    Handle exceptions raised when calling an Denon AVR endpoint asynchronously.

    The decorated function must either have a string variable as second
    argument or as "request" keyword argument.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as err:
            _LOGGER.debug(
                "HTTP status error on request %s", err.request, exc_info=True)
            # Separate handling of 403 errors
            if err.response.status_code == 403:
                raise AvrForbiddenError(
                    "HTTPStatusError: {}".format(err), err.request) from err
            raise AvrRequestError(
                "HTTPStatusError: {}".format(err), err.request) from err
        except httpx.TimeoutException as err:
            _LOGGER.debug(
                "HTTP timeout exception on request %s", err.request,
                exc_info=True)
            raise AvrTimoutError(
                "TimeoutException: {}".format(err), err.request) from err
        except httpx.NetworkError as err:
            _LOGGER.debug(
                "Network error exception on request %s", err.request,
                exc_info=True)
            raise AvrNetworkError(
                "NetworkError: {}".format(err), err.request) from err
        except httpx.RemoteProtocolError as err:
            _LOGGER.debug(
                "Remote protocol error exception on request %s", err.request,
                exc_info=True)
            raise AvrInvalidResponseError(
                "RemoteProtocolError: {}".format(err), err.request) from err
        except (
                ET.ParseError, DefusedXmlException, ParseError,
                UnicodeDecodeError) as err:
            _LOGGER.debug(
                "Defusedxml parse error on request %s", (args, kwargs),
                exc_info=True)
            raise AvrInvalidResponseError(
                "XMLParseError: {}".format(err), (args, kwargs)) from err

    return wrapper


def cache_clear_on_exception(func: Coroutine) -> Coroutine:
    """
    Decorate a function to clear lru_cache if an exception occurs.

    The decorator must be placed right before the @lru_cache decorator.
    It prevents memory leaks in home-assistant when receiver instances are
    created and deleted right away in case the device is offline on setup.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as err:
            _LOGGER.debug("Exception %s raised, clearing cache", err)
            func.cache_clear()
            raise

    return wrapper


def set_cache_id(func: Callable) -> Callable:
    """
    Decorate a function to add cache_id keyword argument if it is not present.

    The function must be called with a fix cache_id keyword argument to be able
    to get cached data. This prevents accidential caching of a function result.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get("cache_id") is None:
            kwargs["cache_id"] = time.time()
        return func(*args, **kwargs)

    return wrapper


def run_async_synchronously(async_func: Coroutine) -> Callable:
    """
    Decorate to run the configured asynchronous function synchronously instead.

    If available the corresponding function with async_ prefix is called in an
    own event loop. This is not efficient but it ensures backwards
    compatibility of this library.
    """
    def decorator(func: Callable):
        # Check if function is a coroutine
        if not inspect.iscoroutinefunction(async_func):
            raise AttributeError(
                "Function {} is not a coroutine function".format(async_func))
        # Check if the signature of both functions is equal
        if inspect.signature(func) != inspect.signature(async_func):
            raise AttributeError(
                "Functions {} and {} have different signatures".format(
                    func, async_func))

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Run async function in own event loop
            loop = asyncio.new_event_loop()

            try:
                return loop.run_until_complete(async_func(*args, **kwargs))
            finally:
                loop.close()

        return wrapper

    return decorator
