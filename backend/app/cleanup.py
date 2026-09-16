"""Background cleanup for expired conversion job directories."""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from pathlib import Path

logger = logging.getLogger("doc2any.cleanup")


def cleanup_expired_jobs(output_dir: Path, *, ttl_seconds: int) -> int:
    """Remove job folders older than ttl_seconds. Returns deleted count."""
    if ttl_seconds <= 0 or not output_dir.exists():
        return 0

    now = time.time()
    deleted = 0
    for child in output_dir.iterdir():
        if not child.is_dir():
            continue
        # Skip reserved names
        if child.name.startswith("."):
            continue
        try:
            age = now - child.stat().st_mtime
        except OSError:
            continue
        if age >= ttl_seconds:
            shutil.rmtree(child, ignore_errors=True)
            deleted += 1
            logger.info("Removed expired job dir %s (age=%.0fs)", child.name, age)
    return deleted


async def cleanup_loop(
    output_dir: Path,
    *,
    ttl_seconds: int,
    interval_seconds: int,
    stop_event: asyncio.Event,
) -> None:
    """Periodically sweep expired jobs until stop_event is set."""
    interval = max(30, interval_seconds)
    while not stop_event.is_set():
        try:
            deleted = await asyncio.to_thread(
                cleanup_expired_jobs, output_dir, ttl_seconds=ttl_seconds
            )
            if deleted:
                logger.info("Cleanup sweep removed %d job folder(s)", deleted)
        except Exception:  # noqa: BLE001
            logger.exception("Cleanup sweep failed")
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            continue
