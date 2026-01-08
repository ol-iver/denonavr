#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive, protocol-agnostic per-destination rate limiter built on aiolimiter.

Single-process only. Excludes fire-and-forget calls (skip_confirmation) from RTT stats.

:copyright: (c) 2025 by Henrik Widlund.
:license: MIT, see LICENSE for more details.
"""
from __future__ import annotations

import asyncio
import contextlib
import time
from typing import Dict, Optional

from aiolimiter import AsyncLimiter


class EWMALatency:
    """Track EWMA of response times per destination."""

    def __init__(self, alpha: float = 0.2) -> None:
        """Initialize EWMA response times tracker."""
        self.alpha = alpha
        self._value: Optional[float] = None

    def update(self, sample: float) -> float:
        """Update EWMA with new sample and return current value."""
        if sample < 0:
            raise ValueError("Latency sample must be non-negative")
        if self._value is None:
            self._value = sample
        else:
            self._value = self.alpha * sample + (1 - self.alpha) * self._value
        return self._value

    @property
    def value(self) -> float:
        """Return current EWMA value, or 0.0 if uninitialized."""
        return self._value or 0.0


class AdaptiveLimiter:
    """
    Adaptive token-bucket rate limiter per key.

    Parameters:
    - initial_wait_ms: initial wait time between requests in milliseconds (> 0)
    - min_wait_ms: minimum wait time between requests in milliseconds (> 0)
    - max_wait_ms: maximum wait time between requests in milliseconds (>= min_wait_ms)
    - k: scaling constant used in target_rate = k / avg_rtt (> 0)
    - adjust_interval: seconds between rate recalculations (> 0)
    - alpha: EWMA smoothing factor in (0,1]

    Behavior:
    - The limiter updates each destination's rate every adjust_interval seconds
      based on the EWMA of observed latencies (excluding skip_confirmation calls).
    - Burst protection is inherent in the token bucket model.
    """

    def __init__(
        self,
        *,
        initial_wait_ms: float = 100.0,
        min_wait_ms: float = 100.0,
        max_wait_ms: float = 200.0,
        k: float = 2.0,
        adjust_interval: float = 2.0,
        alpha: float = 0.2,
    ) -> None:
        """Initialize AdaptiveLimiter with given parameters."""
        # Validate wait params
        if initial_wait_ms <= 0 or min_wait_ms <= 0 or max_wait_ms <= 0:
            raise ValueError("wait values must be > 0")
        if min_wait_ms > max_wait_ms:
            raise ValueError("min_wait_ms must be <= max_wait_ms")

        # Validate EWMA and adjust params
        if k <= 0:
            raise ValueError("k must be > 0")
        if adjust_interval <= 0:
            raise ValueError("adjust_interval must be > 0")
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")

        # Convert waits to rates (req/s): rate = 1000 / wait_ms
        initial_rate = 1000.0 / initial_wait_ms
        self._min_rate = 1000.0 / max_wait_ms  # max wait -> min rate
        self._max_rate = 1000.0 / min_wait_ms  # min wait -> max rate
        self._initial_rate = float(initial_rate)

        self._k = float(k)
        self._adjust_interval = float(adjust_interval)
        self._alpha = float(alpha)
        self._limiters: Dict[str, AsyncLimiter] = {}
        self._latencies: Dict[str, EWMALatency] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._tasks: Dict[str, asyncio.Task] = {}
        self._init_lock = asyncio.Lock()
        self._shutdown_event = asyncio.Event()

    def _target_rate(self, avg_rtt: float) -> float:
        if avg_rtt <= 0:
            return self._initial_rate
        target = self._k / avg_rtt
        return max(self._min_rate, min(self._max_rate, target))

    async def _ensure_key(self, key: str) -> None:
        # Fast path: key already exists
        if key in self._limiters:
            return

        # Slow path: need to initialize, use lock to prevent duplicate initialization
        async with self._init_lock:
            # Double-check after acquiring lock (another coroutine may have initialized)
            if key not in self._limiters:
                # Start limiter at configured initial rate
                self._limiters[key] = AsyncLimiter(self._initial_rate, time_period=1)
                self._latencies[key] = EWMALatency(self._alpha)
                self._locks[key] = asyncio.Lock()
                # Background adjuster
                self._tasks[key] = asyncio.create_task(self._adjust_loop(key))

    async def _adjust_loop(self, key: str) -> None:
        try:
            while not self._shutdown_event.is_set():
                await asyncio.sleep(self._adjust_interval)
                if self._shutdown_event.is_set():
                    break
                avg = self._latencies[key].value
                new_rate = self._target_rate(avg)
                # AsyncLimiter does not expose direct rate mutation;
                # recreate it atomically under a lock to avoid races.
                async with self._locks[key]:
                    self._limiters[key] = AsyncLimiter(new_rate, time_period=1)
        except asyncio.CancelledError:
            pass

    async def acquire(self, destination: str) -> None:
        """Acquire a token for the given destination."""
        await self._ensure_key(destination)
        # Acquire with current limiter. Use lock to avoid swap race.
        async with self._locks[destination]:
            limiter = self._limiters[destination]
        await limiter.acquire()

    def record_latency(self, destination: str, start: float) -> None:
        """
        Record RTT after a call.

        Safe to call even if key doesn't exist yet; if the key is not present,
        the call is silently ignored and no action is taken.
        """
        seconds = time.monotonic() - start
        # Only record if destination already initialized
        if latency_tracker := self._latencies.get(destination):
            latency_tracker.update(seconds)

    async def aclose(self) -> None:
        """Clean up background tasks."""
        # Cancel background tasks
        self._shutdown_event.set()
        for task in list(self._tasks.values()):
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()
