#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adaptive, protocol-agnostic per-destination rate limiter built on aiolimiter.

Single-process only. Excludes fire-and-forget calls (skip_confirmation) from RTT stats.
"""

from __future__ import annotations

import asyncio
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
    - initial_rate: initial wait time between requests in milliseconds (> 0)
    - min_rate: minimum wait time between requests in milliseconds (> 0)
    - max_rate: maximum wait time between requests in milliseconds (>= min_rate)
    - k: scaling constant used in target_rate = k / avg_rtt (> 0)
    - min_adjust_interval: minimum seconds between rate adjustments per key (> 0)
    - adjust_threshold: relative delta required to trigger an adjustment (> 0)
    - alpha: EWMA smoothing factor in (0,1]

    Behavior:
    - Rate adjustments are triggered from record_latency() when the target rate
      diverges from the current rate by more than adjust_threshold and at most
      once per min_adjust_interval per key.
    - Burst protection is inherent in the token bucket model.
    """

    def __init__(
        self,
        *,
        initial_rate: float = 100.0,
        min_rate: float = 100.0,
        max_rate: float = 200.0,
        k: float = 2.0,
        min_adjust_interval: float = 10.0,
        adjust_threshold: float = 0.2,
        alpha: float = 0.2,
    ) -> None:
        """Initialize AdaptiveLimiter with given parameters."""
        # Validate wait params
        if initial_rate <= 0 or min_rate <= 0 or max_rate <= 0:
            raise ValueError("wait values must be > 0")
        if min_rate > max_rate:
            raise ValueError("min_rate must be <= max_rate")

        # Validate EWMA and adjust params
        if k <= 0:
            raise ValueError("k must be > 0")
        if min_adjust_interval <= 0:
            raise ValueError("min_adjust_interval must be > 0")
        if adjust_threshold <= 0:
            raise ValueError("adjust_threshold must be > 0")
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1]")

        # Convert waits to rates (req/s): rate = 1000 / wait_ms
        initial_rate = 1000.0 / initial_rate
        self._min_rate = 1000.0 / max_rate  # max wait -> min rate
        self._max_rate = 1000.0 / min_rate  # min wait -> max rate
        self._initial_rate = float(initial_rate)

        self._k = float(k)
        self._min_adjust_interval = float(min_adjust_interval)
        self._adjust_threshold = float(adjust_threshold)
        self._alpha = float(alpha)
        self._limiters: Dict[str, AsyncLimiter] = {}
        self._rates: Dict[str, float] = {}
        self._latencies: Dict[str, EWMALatency] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._last_adjust: Dict[str, float] = {}
        self._init_lock = asyncio.Lock()

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
                self._rates[key] = self._initial_rate
                self._latencies[key] = EWMALatency(self._alpha)
                self._locks[key] = asyncio.Lock()
                self._last_adjust[key] = time.monotonic()

    async def _adjust_rate(self, key: str, new_rate: float) -> None:
        # AsyncLimiter does not expose direct rate mutation;
        # recreate it atomically under a lock to avoid races.
        async with self._locks[key]:
            self._limiters[key] = AsyncLimiter(new_rate, time_period=1)
            self._rates[key] = new_rate

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

        May schedule a one-shot task to adjust the limiter rate when the target
        rate diverges from the current rate by more than adjust_threshold and
        at least min_adjust_interval has elapsed since the last adjustment.
        """
        seconds = time.monotonic() - start
        # Avoid skewing the rate limiter when calling endpoints that are
        # known to be slow
        if seconds >= 2:
            return

        latency_tracker = self._latencies.get(destination)
        if latency_tracker is None:
            return
        latency_tracker.update(seconds)

        now = time.monotonic()
        if now - self._last_adjust[destination] < self._min_adjust_interval:
            return
        current_rate = self._rates[destination]
        new_rate = self._target_rate(latency_tracker.value)
        if abs(new_rate - current_rate) / current_rate <= self._adjust_threshold:
            return
        # Stamp before scheduling so concurrent callers don't pile on.
        self._last_adjust[destination] = now
        asyncio.create_task(self._adjust_rate(destination, new_rate))
