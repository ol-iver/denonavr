#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module implements the REST API to Denon AVR receivers.

:copyright: (c) 2021 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

import inspect
import logging
from functools import wraps
from typing import Any, Callable, Optional, Sequence, TypeVar

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
                raise AvrForbiddenError(
                    f"HTTPStatusError for {err.request.url}: {err}", err.request
                ) from err
            raise AvrRequestError(
                f"HTTPStatusError for {err.request.url}: {err}", err.request
            ) from err
        except httpx.TimeoutException as err:
            _LOGGER.debug("HTTP timeout exception on request %s: %s", err.request, err)
            raise AvrTimoutError(
                f"TimeoutException for {err.request.url}: {err}", err.request
            ) from err
        except httpx.NetworkError as err:
            _LOGGER.debug("Network error exception on request %s: %s", err.request, err)
            raise AvrNetworkError(
                f"NetworkError for {err.request.url}: {err}", err.request
            ) from err
        except httpx.RemoteProtocolError as err:
            _LOGGER.debug(
                "Remote protocol error exception on request %s",
                err.request,
            )
            raise AvrInvalidResponseError(
                f"RemoteProtocolError for {err.request.url}: {err}", err.request
            ) from err

    return wrapper


class _UnkeyedArg:
    """An argument that is left out of the cache key.

    Every instance hashes and compares alike whatever it holds, so the
    entry one value made answers a call carrying another.
    """

    __slots__ = ("value",)

    def __init__(self, value: Any) -> None:
        """Wrap a value so it takes no part in a cache key."""
        self.value = value

    def __hash__(self) -> int:
        """Hash alike whatever is wrapped."""
        return hash(_UnkeyedArg)

    def __eq__(self, other: Any) -> bool:
        """Compare equal to any other unkeyed argument."""
        return isinstance(other, _UnkeyedArg)


def _unwrap(value: Any) -> Any:
    """Return what an unkeyed argument holds, or the value itself."""
    return value.value if isinstance(value, _UnkeyedArg) else value


def cache_result(
    func: Optional[Callable[..., AnyT]] = None,
    *,
    unkeyed: Sequence[str] = (),
) -> Callable[..., Any]:
    """
    Decorate a function to cache its results with an lru_cache of maxsize 32.

    The cache is only used if the "cache_id" keyword argument is set.

    Parameters named in "unkeyed" are left out of the cache key: calls that
    differ only in them share one entry, made by whichever ran first. Name
    only a parameter that describes the call rather than the answer, such
    as a timeout; anything that changes what comes back has to stay in the
    key.
    """

    def decorator(func: Callable[..., AnyT]) -> Callable[..., AnyT]:
        signature = inspect.signature(func)
        if signature.parameters.get("cache_id") is None:
            raise AttributeError(
                f"Function {func} does not have a 'cache_id' keyword parameter"
            )
        for name in unkeyed:
            if signature.parameters.get(name) is None:
                raise AttributeError(
                    f"Function {func} does not have a '{name}' parameter"
                )

        @wraps(func)
        async def unkeyed_func(*args, **kwargs):
            return await func(
                *(_unwrap(arg) for arg in args),
                **{name: _unwrap(value) for name, value in kwargs.items()},
            )

        lru_decorator = lru_cache(maxsize=32)
        cached_func = lru_decorator(unkeyed_func)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if kwargs.get("cache_id") is None:
                return await func(*args, **kwargs)

            bound = signature.bind(*args, **kwargs)
            for name in unkeyed:
                if name in bound.arguments:
                    bound.arguments[name] = _UnkeyedArg(bound.arguments[name])

            return await cached_func(*bound.args, **bound.kwargs)

        return wrapper

    if func is None:
        return decorator

    return decorator(func)
