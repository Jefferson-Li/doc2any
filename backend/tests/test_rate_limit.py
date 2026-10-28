"""Sliding-window rate limiter."""

from __future__ import annotations

import app.rate_limit as rate_limit
from app.rate_limit import RateLimiter


def test_limit_zero_does_not_record(monkeypatch):
    clock = {"now": 1_000.0}
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: clock["now"])
    limiter = RateLimiter()

    assert limiter.allow("ip", limit=0) is True
    assert limiter.allow("ip", limit=-5) is True
    assert len(limiter._hits["ip"]) == 0
    assert limiter.remaining("ip", limit=0) == 0


def test_allow_remaining_and_expiry(monkeypatch):
    clock = {"now": 1_000.0}
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: clock["now"])
    limiter = RateLimiter()

    assert limiter.allow("a", limit=2) is True
    assert limiter.allow("a", limit=2) is True
    assert limiter.remaining("a", limit=2) == 0
    assert limiter.allow("a", limit=2) is False
    assert limiter.allow("b", limit=1) is True
    assert limiter.remaining("b", limit=1) == 0

    clock["now"] = 1_061.0
    assert limiter.remaining("a", limit=2) == 2
    assert limiter.allow("a", limit=2) is True
    assert limiter.remaining("a", limit=2) == 1

    limiter._hits["crowded"].extend([clock["now"], clock["now"], clock["now"]])
    assert limiter.remaining("crowded", limit=1) == 0


def test_expired_hits_are_pruned_before_fresh_ones(monkeypatch):
    clock = {"now": 500.0}
    monkeypatch.setattr(rate_limit.time, "monotonic", lambda: clock["now"])
    limiter = RateLimiter()
    limiter._hits["mix"].extend([400.0, 430.0, 490.0])

    clock["now"] = 500.0
    assert limiter.allow("mix", limit=3, window_seconds=60) is True
    assert list(limiter._hits["mix"]) == [490.0, 500.0]
    assert limiter.remaining("mix", limit=3, window_seconds=60) == 1


def test_module_limiter_is_shared_instance():
    assert isinstance(rate_limit.limiter, RateLimiter)
