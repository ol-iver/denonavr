#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This module covers tests of the caching decorator.

:copyright: (c) 2016 by Oliver Goetz.
:license: MIT, see LICENSE for more details.
"""

from typing import Any, Callable, Hashable, List, Optional, Tuple

import pytest
from pytest_httpx import HTTPXMock

from denonavr.api import DenonAVRApi
from denonavr.decorators import cache_result

APPCOMMAND_URL = "/goform/AppCommand.xml"
FAKE_IP = "10.1.0.0"


def counting_reader(
    unkeyed: Tuple[str, ...] = (),
) -> Tuple[Callable[..., Any], List[Tuple[str, float]]]:
    """Return a cached reader and the list of calls that reached it."""
    calls: List[Tuple[str, float]] = []

    @cache_result(unkeyed=unkeyed)
    async def read(url: str, timeout: float, *, cache_id: Hashable = None) -> int:
        calls.append((url, timeout))
        return len(calls)

    return read, calls


class TestUnkeyedArguments:
    """Test case for parameters that are left out of the cache key."""

    @pytest.mark.asyncio
    async def test_an_unkeyed_argument_does_not_split_the_cache(self):
        """Check that two timeouts share one entry, the first one's."""
        read, calls = counting_reader(unkeyed=("timeout",))

        assert await read("/a", 2.0, cache_id=1) == 1
        assert await read("/a", 15.0, cache_id=1) == 1

        assert calls == [("/a", 2.0)]

    @pytest.mark.asyncio
    async def test_a_keyed_argument_still_splits_it(self):
        """Check that only the named parameter is left out of the key."""
        read, calls = counting_reader(unkeyed=("timeout",))

        await read("/a", 2.0, cache_id=1)
        await read("/b", 2.0, cache_id=1)
        await read("/a", 2.0, cache_id=2)

        assert calls == [("/a", 2.0), ("/b", 2.0), ("/a", 2.0)]

    @pytest.mark.asyncio
    async def test_naming_nothing_keeps_every_argument_in_the_key(self):
        """Check that the plain decorator is what it always was."""
        read, calls = counting_reader()

        await read("/a", 2.0, cache_id=1)
        await read("/a", 15.0, cache_id=1)

        assert calls == [("/a", 2.0), ("/a", 15.0)]

    @pytest.mark.asyncio
    async def test_without_a_cache_id_nothing_is_cached(self):
        """Check that leaving the cache id out still bypasses the cache."""
        read, calls = counting_reader(unkeyed=("timeout",))

        await read("/a", 2.0)
        await read("/a", 2.0)

        assert calls == [("/a", 2.0), ("/a", 2.0)]

    def test_naming_a_parameter_that_is_not_there_is_refused(self):
        """Check that a typo in the name is reported where it is made."""
        with pytest.raises(AttributeError):

            @cache_result(unkeyed=("read_timeout",))
            async def read(url: str, *, cache_id: Hashable = None) -> str:
                return url


class TestPostKeepsItsBody:
    """Test case for the request body of a cached POST."""

    @pytest.mark.asyncio
    @pytest.mark.httpx_mock(can_send_already_matched_responses=True)
    async def test_two_bodies_are_two_requests(self, httpx_mock: HTTPXMock):
        """Check that what is posted still tells one call from another.

        One AppCommand.xml request differs from another in its body alone,
        so that stays in the cache key whatever else leaves it.
        """
        httpx_mock.add_response(content="DATA")
        api = DenonAVRApi(host=FAKE_IP)
        cache_id: Optional[Hashable] = 1

        await api.async_post(APPCOMMAND_URL, content=b"first", cache_id=cache_id)
        await api.async_post(APPCOMMAND_URL, content=b"second", cache_id=cache_id)
        await api.async_post(APPCOMMAND_URL, content=b"first", cache_id=cache_id)

        bodies = [request.content for request in httpx_mock.get_requests()]
        assert bodies == [b"first", b"second"]
