#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST API to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import inspect
import logging
import time
from functools import wraps
from typing import Callable, TypeVar

import httpx
from asyncstdlib import lru_cache

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
    """Handle exceptions raised when calling a Denon AVR endpoint asynchronously."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as err:
            _LOGGER.debug("HTTP status error on request %s: %s", err.request, err)
            # Separate handling of 403 errors
            if err.response.status_code == 403:
                raise AvrForbiddenError(f"HTTPStatusError: {err}", err.request) from err
            raise AvrRequestError(f"HTTPStatusError: {err}", err.request) from err
        except httpx.TimeoutException as err:
            _LOGGER.debug("HTTP timeout exception on request %s: %s", err.request, err)
            raise AvrTimoutError(f"TimeoutException: {err}", err.request) from err
        except httpx.NetworkError as err:
            _LOGGER.debug("Network error exception on request %s: %s", err.request, err)
            raise AvrNetworkError(f"NetworkError: {err}", err.request) from err
        except httpx.RemoteProtocolError as err:
            _LOGGER.debug(
                "Remote protocol error exception on request %s",
                err.request,
            )
            raise AvrInvalidResponseError(
                f"RemoteProtocolError: {err}", err.request
            ) from err

    return wrapper


def cache_result(func: Callable[..., AnyT]) -> Callable[..., AnyT]:
    """
    Decorate a function to cache its results with an lru_cache of maxsize 32.

    This decorator also sets an "cache_id" keyword argument if it is not set yet.
    """
    if inspect.signature(func).parameters.get("cache_id") is None:
        raise AttributeError(
            f"Function {func} does not have a 'cache_id' keyword parameter"
        )

    lru_decorator = lru_cache(maxsize=32)
    cached_func = lru_decorator(func)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if kwargs.get("cache_id") is None:
            kwargs["cache_id"] = time.time()

        return await cached_func(*args, **kwargs)

    return wrapper
