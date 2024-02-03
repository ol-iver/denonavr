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
from typing import Callable, Coroutine, TypeVar

import httpx
from asyncstdlib import lru_cache
from defusedxml import DefusedXmlException
from defusedxml.ElementTree import ParseError

from .exceptions import (
    AvrForbiddenError,
    AvrInvalidResponseError,
    AvrNetworkError,
    AvrRequestError,
    AvrTimoutError,
)

_LOGGER = logging.getLogger(__name__)

AnyT = TypeVar("AnyT")


def async_handle_receiver_exceptions(func: Callable[..., AnyT]) -> Callable[..., AnyT]:
    """
    Handle exceptions raised when calling a Denon AVR endpoint asynchronously.

    The decorated function must either have a string variable as second
    argument or as "request" keyword argument.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as err:
            _LOGGER.debug("HTTP status error on request %s", err.request, exc_info=True)
            # Separate handling of 403 errors
            if err.response.status_code == 403:
                raise AvrForbiddenError(f"HTTPStatusError: {err}", err.request) from err
            raise AvrRequestError(f"HTTPStatusError: {err}", err.request) from err
        except httpx.TimeoutException as err:
            _LOGGER.debug(
                "HTTP timeout exception on request %s", err.request, exc_info=True
            )
            raise AvrTimoutError(f"TimeoutException: {err}", err.request) from err
        except httpx.NetworkError as err:
            _LOGGER.debug(
                "Network error exception on request %s", err.request, exc_info=True
            )
            raise AvrNetworkError(f"NetworkError: {err}", err.request) from err
        except httpx.RemoteProtocolError as err:
            _LOGGER.debug(
                "Remote protocol error exception on request %s",
                err.request,
                exc_info=True,
            )
            raise AvrInvalidResponseError(
                f"RemoteProtocolError: {err}", err.request
            ) from err
        except (
            ET.ParseError,
            DefusedXmlException,
            ParseError,
            UnicodeDecodeError,
        ) as err:
            _LOGGER.debug(
                "Defusedxml parse error on request %s", (args, kwargs), exc_info=True
            )
            raise AvrInvalidResponseError(
                f"XMLParseError: {err}", (args, kwargs)
            ) from err

    return wrapper


def cache_result(func: Callable[..., AnyT]) -> Callable[..., AnyT]:
    """
    Decorate a function to cache its results with an lru_cache of maxsize 16.

    This decorator also sets an "cache_id" keyword argument if it is not set yet.
    When an exception occurs it clears lru_cache to prevent memory leaks in
    home-assistant when receiver instances are created and deleted right
    away in case the device is offline on setup.
    """
    if inspect.signature(func).parameters.get("cache_id") is None:
        raise AttributeError(
            f"Function {func} does not have a 'cache_id' keyword parameter"
        )

    lru_decorator = lru_cache(maxsize=16)
    cached_func = lru_decorator(func)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if kwargs.get("cache_id") is None:
            kwargs["cache_id"] = time.time()
        try:
            return await cached_func(*args, **kwargs)
        except Exception as err:
            _LOGGER.debug("Exception %s raised, clearing cache", err)
            cached_func.cache_clear()
            raise

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
            raise AttributeError(f"Function {async_func} is not a coroutine function")
        # Check if the signature of both functions is equal
        if inspect.signature(func) != inspect.signature(async_func):
            raise AttributeError(
                f"Functions {func} and {async_func} have different signatures"
            )

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
