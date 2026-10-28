"""Isolate settings before the application is imported."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_DATA = Path(tempfile.mkdtemp(prefix="doc2any-tests-"))
os.environ["DOC2ANY_ENV"] = "development"
os.environ["DOC2ANY_DATA_DIR"] = str(_DATA)
os.environ["DOC2ANY_DEBUG"] = "false"
os.environ["DOC2ANY_CLEANUP_ENABLED"] = "false"
os.environ["DOC2ANY_CLEANUP_INTERVAL_SECONDS"] = "30"
os.environ["DOC2ANY_FILE_TTL_SECONDS"] = "3600"
os.environ["DOC2ANY_RATE_LIMIT_ENABLED"] = "true"
os.environ["DOC2ANY_RATE_LIMIT_PER_MINUTE"] = "1000"
os.environ["DOC2ANY_RATE_LIMIT_ANALYZE_PER_MINUTE"] = "1000"
os.environ["DOC2ANY_MAX_UPLOAD_MB"] = "50"
os.environ["DOC2ANY_CORS_ORIGINS"] = "*"
os.environ["DOC2ANY_PUBLIC_LABEL"] = ""
os.environ["DOC2ANY_HOST"] = "127.0.0.1"
os.environ["DOC2ANY_PORT"] = "8000"


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    from app.rate_limit import limiter

    limiter._hits.clear()
    yield
    limiter._hits.clear()


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    yield
    from app.config import get_settings

    get_settings.cache_clear()
