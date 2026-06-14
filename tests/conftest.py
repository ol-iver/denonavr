#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared pytest fixtures for denonavr tests."""

import pytest

from denonavr.rate_limiter import AdaptiveLimiter


@pytest.fixture(autouse=True)
def fast_rate_limiter(monkeypatch):
    """Make AdaptiveLimiter effectively unlimited under mocked HTTP."""
    original_init = AdaptiveLimiter.__init__

    def fast_init(self, **kwargs):
        kwargs.setdefault("initial_rate", 1.0)
        kwargs.setdefault("min_rate", 1.0)
        kwargs.setdefault("max_rate", 1.0)
        original_init(self, **kwargs)

    monkeypatch.setattr(AdaptiveLimiter, "__init__", fast_init)
