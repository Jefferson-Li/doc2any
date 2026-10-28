"""Expired job directory cleanup."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path

import pytest

import app.cleanup as cleanup


def _age(path: Path, seconds: float) -> None:
    stamp = time.time() - seconds
    os.utime(path, (stamp, stamp))


def test_cleanup_skips_invalid_targets(tmp_path):
    missing = tmp_path / "missing"
    assert cleanup.cleanup_expired_jobs(missing, ttl_seconds=10) == 0

    root = tmp_path / "out"
    root.mkdir()
    old = root / "old"
    old.mkdir()
    _age(old, 500)
    assert cleanup.cleanup_expired_jobs(root, ttl_seconds=0) == 0
    assert cleanup.cleanup_expired_jobs(root, ttl_seconds=-5) == 0
    assert old.is_dir()


def test_cleanup_removes_only_expired_job_dirs(tmp_path, caplog):
    root = tmp_path / "out"
    root.mkdir()
    expired = root / "job-old"
    fresh = root / "job-new"
    hidden = root / ".keep"
    leftover = root / "notes.txt"
    for directory in (expired, fresh, hidden):
        directory.mkdir()
    leftover.write_text("keep")
    _age(expired, 5_000)
    _age(hidden, 5_000)
    _age(leftover, 5_000)

    caplog.set_level(logging.INFO, logger="doc2any.cleanup")
    deleted = cleanup.cleanup_expired_jobs(root, ttl_seconds=100)

    assert deleted == 1
    assert not expired.exists()
    assert fresh.is_dir()
    assert hidden.is_dir()
    assert leftover.is_file()
    assert "job-old" in caplog.text


def test_cleanup_continues_when_stat_fails(tmp_path, monkeypatch):
    root = tmp_path / "out"
    root.mkdir()
    good = root / "good"
    bad = root / "bad"
    good.mkdir()
    bad.mkdir()
    _age(good, 5_000)
    _age(bad, 5_000)

    real_stat = Path.stat
    calls = {"bad": 0}

    def flaky(self, *args, **kwargs):
        if self.name == "bad":
            calls["bad"] += 1
            if calls["bad"] > 1:
                raise OSError("denied")
        return real_stat(self, *args, **kwargs)

    monkeypatch.setattr(Path, "stat", flaky)
    assert cleanup.cleanup_expired_jobs(root, ttl_seconds=10) == 1
    names = {path.name for path in root.iterdir()}
    assert "good" not in names
    assert "bad" in names


def test_cleanup_loop_stops_immediately(tmp_path, monkeypatch):
    called = {"n": 0}

    def boom(*args, **kwargs):
        called["n"] += 1
        return 0

    monkeypatch.setattr(cleanup, "cleanup_expired_jobs", boom)
    stop = asyncio.Event()
    stop.set()
    asyncio.run(
        cleanup.cleanup_loop(
            tmp_path, ttl_seconds=10, interval_seconds=10, stop_event=stop
        )
    )
    assert called["n"] == 0


def test_cleanup_loop_logs_sweeps_and_honors_interval(tmp_path, monkeypatch, caplog):
    root = tmp_path / "out"
    root.mkdir()
    results = iter([2, 0])

    def fake_cleanup(*args, **kwargs):
        return next(results)

    monkeypatch.setattr(cleanup, "cleanup_expired_jobs", fake_cleanup)
    timeouts: list[float] = []
    stop = asyncio.Event()

    async def fake_wait_for(awaitable, timeout):
        timeouts.append(timeout)
        stop.set()
        return await awaitable

    monkeypatch.setattr(cleanup.asyncio, "wait_for", fake_wait_for)
    caplog.set_level(logging.INFO, logger="doc2any.cleanup")
    asyncio.run(
        cleanup.cleanup_loop(
            root, ttl_seconds=10, interval_seconds=10, stop_event=stop
        )
    )
    assert timeouts == [30]
    assert "Cleanup sweep removed 2" in caplog.text

    timeouts.clear()
    stop = asyncio.Event()

    async def fake_wait_long(awaitable, timeout):
        timeouts.append(timeout)
        stop.set()
        return await awaitable

    monkeypatch.setattr(cleanup.asyncio, "wait_for", fake_wait_long)
    monkeypatch.setattr(cleanup, "cleanup_expired_jobs", lambda *a, **k: 0)
    asyncio.run(
        cleanup.cleanup_loop(
            root, ttl_seconds=10, interval_seconds=120, stop_event=stop
        )
    )
    assert timeouts == [120]


def test_cleanup_loop_retries_after_timeout_and_logs_errors(tmp_path, monkeypatch, caplog):
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("disk")
        return 0

    monkeypatch.setattr(cleanup, "cleanup_expired_jobs", flaky)
    stop = asyncio.Event()
    waits = {"n": 0}

    async def fake_wait_for(awaitable, timeout):
        waits["n"] += 1
        task = asyncio.ensure_future(awaitable)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        if waits["n"] == 1:
            raise asyncio.TimeoutError
        stop.set()
        return None

    monkeypatch.setattr(cleanup.asyncio, "wait_for", fake_wait_for)
    caplog.set_level(logging.ERROR, logger="doc2any.cleanup")
    asyncio.run(
        cleanup.cleanup_loop(
            tmp_path, ttl_seconds=5, interval_seconds=45, stop_event=stop
        )
    )
    assert calls["n"] == 2
    assert "Cleanup sweep failed" in caplog.text
