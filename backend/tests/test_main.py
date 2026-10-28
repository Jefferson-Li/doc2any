"""HTTP API, rate limit, and process lifespan."""

from __future__ import annotations

import asyncio
import importlib
import io
import json
import logging
from pathlib import Path

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from starlette.requests import Request

import app.config as config
import app.converters as converters
import app.main as main
from app.converters.pipeline import ConversionReport
from tests.support import add_page, solid_image, write_pdf


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


def _request(headers=None, client=("127.0.0.1", 5000)):
    raw = []
    for key, value in (headers or {}).items():
        raw.append((key.lower().encode(), value.encode()))
    scope = {
        "type": "http",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": raw,
        "client": client,
        "server": ("test", 80),
    }
    return Request(scope)


class _UUID:
    def __init__(self, hex_value):
        self.hex = hex_value


def test_package_exports():
    assert converters.__all__
    for name in converters.__all__:
        assert hasattr(converters, name)
    import app

    assert app is not None


def test_client_ip_headers():
    forwarded = _request({"X-Forwarded-For": " 203.0.113.9, 10.0.0.8 "})
    assert main._client_ip(forwarded) == "203.0.113.9"
    assert main._client_ip(_request()) == "127.0.0.1"
    assert main._client_ip(_request(client=None)) == "unknown"


def test_health_formats_and_static(client, monkeypatch):
    monkeypatch.setattr(main, "libreoffice_available", lambda: False)
    health = client.get("/api/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["environment"] == "development"
    assert body["label"] == "Dev"
    assert body["libreoffice"] is False
    assert "docx" in body["targets"]
    assert body["max_upload_mb"] == 50

    monkeypatch.setenv("DOC2ANY_ENV", "staging")
    monkeypatch.setenv("DOC2ANY_PUBLIC_LABEL", "")
    config.get_settings.cache_clear()
    staged = client.get("/api/health").json()
    assert staged["environment"] == "staging"
    assert staged["label"] == "Staging"

    monkeypatch.setenv("DOC2ANY_ENV", "production")
    monkeypatch.setenv("DOC2ANY_DEBUG", "true")
    config.get_settings.cache_clear()
    assert client.get("/api/health").json()["label"] == ""

    monkeypatch.setattr(main, "libreoffice_available", lambda: True)
    formats = client.get("/api/formats").json()
    assert formats["libreoffice"] is True
    assert "docx" in formats["routes"]["pdf"]
    assert formats["environment"] == "production"

    assert "Doc2Any" in client.get("/").text
    assert client.get("/assets/styles.css").status_code == 200
    assert client.get("/assets/app.js").status_code == 200
    assert main.app.docs_url == "/docs"
    assert main.app.redoc_url == "/redoc"


def test_analyze_validation_layout_and_cleanup(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("analyzejob01"))

    async def missing_name():
        upload = UploadFile(filename="", file=io.BytesIO(b"abc"))
        with pytest.raises(HTTPException) as exc:
            await main.analyze(_request(), upload)
        assert exc.value.status_code == 400
        assert exc.value.detail == "缺少檔案名稱"

    asyncio.run(missing_name())

    empty = client.post("/api/analyze", files={"file": ("a.pdf", b"", "application/pdf")})
    assert empty.status_code == 400
    assert empty.json()["detail"] == "空檔案"

    cfg = config.get_settings()
    monkeypatch.setattr(cfg, "max_upload_mb", 1)
    too_big = client.post(
        "/api/analyze",
        files={"file": ("a.pdf", b"x" * (1024 * 1024 + 1), "application/pdf")},
    )
    assert too_big.status_code == 413
    assert "1MB" in too_big.json()["detail"]

    seen = {}

    def fake_layout(path: Path):
        seen["name"] = path.name
        seen["bytes"] = path.read_bytes()
        return {"recommended_mode": "visual", "is_scanned": True, "complex_layout": False}

    original_layout = main.analyze_pdf_layout
    monkeypatch.setattr(main, "analyze_pdf_layout", fake_layout)
    analyzed = client.post(
        "/api/analyze",
        files={"file": ("../../secret.PDF", b"%PDF-1.4", "application/pdf")},
    )
    assert analyzed.status_code == 200
    assert analyzed.json()["recommended_mode"] == "visual"
    assert seen["name"] == "secret.PDF"
    assert seen["bytes"].startswith(b"%PDF")
    job = cfg.resolved_output_dir / "analyzejob01"
    assert not job.exists()

    def explode(path):
        raise RuntimeError("inspect failed")

    monkeypatch.setattr(main, "analyze_pdf_layout", explode)
    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("analyzejob02"))
    with pytest.raises(RuntimeError, match="inspect failed"):
        client.post("/api/analyze", files={"file": ("a.pdf", b"%PDF", "application/pdf")})
    assert not (cfg.resolved_output_dir / "analyzejob02").exists()
    monkeypatch.setattr(main, "analyze_pdf_layout", original_layout)

    other = client.post("/api/analyze", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert other.status_code == 200
    assert other.json()["recommended_mode"] == "editable"
    assert other.json()["reason"] == "非 PDF，無需版面模式"

    sample = write_pdf(tmp_path / "sample.pdf", lambda doc: add_page(doc, "Hello layout"))
    real = client.post(
        "/api/analyze",
        files={"file": ("sample.pdf", sample.read_bytes(), "application/pdf")},
    )
    assert real.status_code == 200
    assert real.json()["layout_type"] == "simple"
    assert real.json()["pipeline_step"] == "layout_detection"


def test_convert_success_errors_and_headers(client, monkeypatch, tmp_path):
    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("convertjob01"))
    cfg = config.get_settings()
    single = write_pdf(tmp_path / "single.pdf", lambda doc: add_page(doc, "Solo text"))

    rejected = client.post(
        "/api/convert",
        data={"target_format": "txt", "layout_mode": "sideways"},
        files={"file": ("single.pdf", single.read_bytes(), "application/pdf")},
    )
    assert rejected.status_code == 400
    assert "layout_mode" in rejected.json()["detail"]

    async def missing_name():
        upload = UploadFile(filename=None, file=io.BytesIO(b"abc"))
        with pytest.raises(HTTPException) as exc:
            await main.convert(_request(), upload, "txt", "auto")
        assert exc.value.status_code == 400
        assert exc.value.detail == "缺少檔案名稱"

    asyncio.run(missing_name())

    empty = client.post(
        "/api/convert",
        data={"target_format": "txt"},
        files={"file": ("a.txt", b"", "text/plain")},
    )
    assert empty.status_code == 400
    assert empty.json()["detail"] == "空檔案"

    monkeypatch.setattr(cfg, "max_upload_mb", 1)
    huge = client.post(
        "/api/convert",
        data={"target_format": "txt"},
        files={"file": ("a.txt", b"y" * (1024 * 1024 + 1), "text/plain")},
    )
    assert huge.status_code == 413

    text = client.post(
        "/api/convert",
        data={"target_format": "txt", "layout_mode": ""},
        files={"file": ("../../note.PDF", single.read_bytes(), "application/pdf")},
    )
    assert text.status_code == 200
    assert "Solo text" in text.text
    assert text.headers["content-type"].startswith("text/plain")
    assert "note.txt" in text.headers["content-disposition"]
    assert "x-doc2any-score" not in text.headers
    job = cfg.resolved_output_dir / "convertjob01"
    assert (job / "note.PDF").is_file()
    assert (job / "note.txt").is_file()

    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("convertjob02"))
    image = solid_image(tmp_path / "pic.png", color=(20, 30, 40))
    jpeg = client.post(
        "/api/convert",
        data={"target_format": ".JPEG"},
        files={"file": ("pic.png", image.read_bytes(), "image/png")},
    )
    assert jpeg.status_code == 200
    assert jpeg.headers["content-type"] == "image/jpeg"
    assert jpeg.content[:3] == b"\xff\xd8\xff"

    captured = {}

    def fake_pipeline(src, dst, work, mode="auto"):
        captured["mode"] = mode
        captured["src_name"] = src.name
        dst.write_bytes(b"PK-docx-bytes")
        return ConversionReport(
            path=dst,
            mode_used="positioned",
            layout={"layout_type": "simple"},
            quality={
                "overall": 91.2,
                "grade": "A",
                "layout_similarity": 90,
                "text_preservation": 95,
                "image_preservation": 100,
                "element_alignment": 88,
                "page_structure": 94,
                "editability": 88,
                "weights": {},
                "explain": {},
                "thresholds": {},
                "mode_used": "positioned",
            },
        )

    monkeypatch.setattr(main, "convert_pdf_to_docx_pipeline", fake_pipeline)
    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("convertjob03"))
    docx = client.post(
        "/api/convert",
        data={"target_format": ".DOCX", "layout_mode": " Hybrid "},
        files={"file": ("resume.pdf", b"%PDF-resume", "application/pdf")},
    )
    assert docx.status_code == 200
    assert docx.content == b"PK-docx-bytes"
    assert docx.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert captured["mode"] == "hybrid"
    assert captured["src_name"] == "resume.pdf"
    assert docx.headers["x-doc2any-score"] == "91.2"
    assert docx.headers["x-doc2any-grade"] == "A"
    assert docx.headers["x-doc2any-layout-type"] == "simple"
    assert docx.headers["x-doc2any-mode-used"] == "positioned"
    # to_dict() does not forward editability, so the legacy header is blank.
    assert docx.headers["x-doc2any-score-edit"] == ""
    assert "/api/jobs/convertjob03/report" in docx.headers["x-doc2any-report"]
    assert "X-Doc2Any-Score" in docx.headers["access-control-expose-headers"]
    report_path = cfg.resolved_output_dir / "convertjob03" / "conversion_report.json"
    assert json.loads(report_path.read_text(encoding="utf-8"))["mode_used"] == "positioned"

    class Bare:
        def __init__(self, path):
            self.path = path

        def to_dict(self):
            return {"mode_used": "visual", "quality": None, "layout": None}

        def write_json(self, dest):
            dest.write_text("{}", encoding="utf-8")
            return dest

    def bare_pipeline(src, dst, work, mode="auto"):
        dst.write_bytes(b"bare")
        return Bare(dst)

    monkeypatch.setattr(main, "convert_pdf_to_docx_pipeline", bare_pipeline)
    bare = client.post(
        "/api/convert",
        data={"target_format": "docx"},
        files={"file": ("bare.pdf", b"%PDF", "application/pdf")},
    )
    assert bare.status_code == 200
    assert bare.headers["x-doc2any-score"] == ""
    assert bare.headers["x-doc2any-layout-type"] == ""
    assert bare.headers["x-doc2any-grade"] == ""

    def as_zip(src, target, work, layout_mode="auto"):
        path = work / f"{src.stem}.zip"
        path.write_bytes(b"PKZIP")
        return path

    monkeypatch.setattr(main, "convert_file", as_zip)
    zipped = client.post(
        "/api/convert",
        data={"target_format": "png"},
        files={"file": ("pages.pdf", b"%PDF", "application/pdf")},
    )
    assert zipped.status_code == 200
    assert zipped.headers["content-type"] == "application/zip"

    def as_bin(src, target, work, layout_mode="auto"):
        path = work / f"{src.stem}.bin"
        path.write_bytes(b"bin")
        return path

    monkeypatch.setattr(main, "convert_file", as_bin)
    binary = client.post(
        "/api/convert",
        data={"target_format": "txt"},
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert binary.headers["content-type"] == "application/octet-stream"

    for suffix, media in {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "html": "text/html",
        "webp": "image/webp",
        "odt": "application/vnd.oasis.opendocument.text",
        "rtf": "application/rtf",
    }.items():

        def make(src, target, work, layout_mode="auto", suffix=suffix):
            path = work / f"{src.stem}.{suffix}"
            path.write_bytes(b"x")
            return path

        monkeypatch.setattr(main, "convert_file", make)
        response = client.post(
            "/api/convert",
            data={"target_format": "txt"},
            files={"file": ("a.txt", b"hello", "text/plain")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"].split(";")[0] == media

    monkeypatch.setattr(main.uuid, "uuid4", lambda: _UUID("convertjoberr"))

    def raise_value(*args, **kwargs):
        raise ValueError("bad pair")

    monkeypatch.setattr(main, "convert_file", raise_value)
    failed = client.post(
        "/api/convert",
        data={"target_format": "txt"},
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert failed.status_code == 400
    assert failed.json()["detail"] == "bad pair"
    assert not (cfg.resolved_output_dir / "convertjoberr").exists()

    def raise_runtime(*args, **kwargs):
        raise RuntimeError("need office")

    monkeypatch.setattr(main, "convert_file", raise_runtime)
    runtime = client.post(
        "/api/convert",
        data={"target_format": "pdf"},
        files={"file": ("a.docx", b"PK", "application/octet-stream")},
    )
    assert runtime.status_code == 422
    assert runtime.json()["detail"] == "need office"

    def raise_os(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(main, "convert_file", raise_os)
    blown = client.post(
        "/api/convert",
        data={"target_format": "txt"},
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert blown.status_code == 500
    assert blown.json()["detail"] == "轉換失敗: disk full"


def test_job_report(client):
    missing = client.get("/api/jobs/missingjob/report")
    assert missing.status_code == 404
    bad = client.get("/api/jobs/bad-id/report")
    assert bad.status_code == 400
    assert bad.json()["detail"] == "無效的 job id"
    long_id = "a" * 65
    assert client.get(f"/api/jobs/{long_id}/report").status_code == 400

    cfg = config.get_settings()
    job = cfg.resolved_output_dir / ("ab" * 32)
    job.mkdir(parents=True)
    payload = {"mode_used": "visual", "quality": {"overall": 80}}
    (job / "conversion_report.json").write_text(json.dumps(payload), encoding="utf-8")
    found = client.get(f"/api/jobs/{job.name}/report")
    assert found.status_code == 200
    assert found.json() == payload


def test_rate_limit_buckets(client, monkeypatch):
    cfg = config.get_settings()
    monkeypatch.setattr(cfg, "rate_limit_enabled", False)
    monkeypatch.setattr(cfg, "rate_limit_per_minute", 1)
    from app.rate_limit import limiter

    limiter._hits["convert:198.51.100.10"].extend([0, 0, 0])
    for _ in range(3):
        response = client.post(
            "/api/convert",
            data={"target_format": "html"},
            files={"file": ("a.txt", b"hello", "text/plain")},
            headers={"X-Forwarded-For": "198.51.100.10"},
        )
        assert response.status_code == 200

    monkeypatch.setattr(cfg, "rate_limit_enabled", True)
    monkeypatch.setattr(cfg, "rate_limit_analyze_per_minute", 1)
    monkeypatch.setattr(cfg, "rate_limit_per_minute", 2)
    limiter._hits.clear()
    headers = {"X-Forwarded-For": "198.51.100.20"}
    first = client.post("/api/analyze", files={"file": ("a.txt", b"hello", "text/plain")}, headers=headers)
    second = client.post("/api/analyze", files={"file": ("a.txt", b"hello", "text/plain")}, headers=headers)
    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"] == "60"
    assert "Too many requests" in second.json()["detail"]
    converted = client.post(
        "/api/convert",
        data={"target_format": "html"},
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers=headers,
    )
    assert converted.status_code == 200
    other = client.post(
        "/api/analyze",
        files={"file": ("a.txt", b"hello", "text/plain")},
        headers={"X-Forwarded-For": "198.51.100.30, 10.0.0.1"},
    )
    assert other.status_code == 200


def _settings(tmp_path, **overrides):
    values = dict(
        env="development",
        data_dir=tmp_path,
        cleanup_enabled=False,
        debug=False,
        rate_limit_enabled=False,
        cleanup_interval_seconds=30,
        file_ttl_seconds=3600,
        public_label="",
    )
    values.update(overrides)
    return config.Settings(**values)


def test_lifespan_cleanup_paths(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO, logger="doc2any")

    async def disabled():
        main._cleanup_stop = None
        main._cleanup_task = None
        monkeypatch.setattr(main, "get_settings", lambda: _settings(tmp_path, cleanup_enabled=False))
        async with main.lifespan(main.app):
            assert main._cleanup_task is None
        assert main._cleanup_stop is None

    asyncio.run(disabled())
    assert "Doc2Any starting" in caplog.text

    async def preexisting_stop():
        event = asyncio.Event()
        main._cleanup_stop = event
        main._cleanup_task = None
        monkeypatch.setattr(main, "get_settings", lambda: _settings(tmp_path, cleanup_enabled=False))
        async with main.lifespan(main.app):
            assert main._cleanup_task is None
        assert event.is_set()

    asyncio.run(preexisting_stop())

    async def enabled():
        main._cleanup_stop = None
        main._cleanup_task = None
        monkeypatch.setattr(
            main,
            "get_settings",
            lambda: _settings(tmp_path, cleanup_enabled=True, cleanup_interval_seconds=30),
        )
        async with main.lifespan(main.app):
            assert main._cleanup_task is not None
            assert main._cleanup_stop is not None
            assert not main._cleanup_stop.is_set()
        assert main._cleanup_stop.is_set()
        assert main._cleanup_task.done()
        assert main._cleanup_task.cancelled() is False

    asyncio.run(enabled())

    async def timed_out():
        main._cleanup_stop = None
        main._cleanup_task = None

        async def hang(*args, **kwargs):
            await asyncio.Event().wait()

        real_wait = asyncio.wait_for

        async def fail_fast(awaitable, timeout):
            if timeout == 5:
                raise asyncio.TimeoutError
            return await real_wait(awaitable, timeout)

        monkeypatch.setattr(main, "cleanup_loop", hang)
        monkeypatch.setattr(main.asyncio, "wait_for", fail_fast)
        monkeypatch.setattr(main, "get_settings", lambda: _settings(tmp_path, cleanup_enabled=True))
        async with main.lifespan(main.app):
            task = main._cleanup_task
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled()

    asyncio.run(timed_out())

    async def cancelled():
        main._cleanup_stop = None
        main._cleanup_task = None
        flags = {"cancel": False}
        holder = {}

        async def hang(*args, **kwargs):
            await asyncio.Event().wait()

        async def raise_cancelled(awaitable, timeout):
            raise asyncio.CancelledError()

        original_create = asyncio.create_task

        def tracking(coro):
            task = original_create(coro)
            original_cancel = task.cancel

            def cancel(*args, **kwargs):
                flags["cancel"] = True
                return original_cancel(*args, **kwargs)

            task.cancel = cancel
            holder["task"] = task
            return task

        monkeypatch.setattr(main, "cleanup_loop", hang)
        monkeypatch.setattr(main.asyncio, "wait_for", raise_cancelled)
        monkeypatch.setattr(main.asyncio, "create_task", tracking)
        monkeypatch.setattr(main, "get_settings", lambda: _settings(tmp_path, cleanup_enabled=True))
        async with main.lifespan(main.app):
            pass
        assert flags["cancel"] is True
        with pytest.raises(asyncio.CancelledError):
            await holder["task"]

    asyncio.run(cancelled())


def test_docs_routes_follow_imported_settings(monkeypatch, tmp_path):
    real_get_settings = config.get_settings
    data_dir = __import__("os").environ["DOC2ANY_DATA_DIR"]

    def load(factory):
        monkeypatch.setattr(config, "get_settings", factory)
        importlib.reload(main)
        return main.app

    try:
        def production_debug_off():
            return config.Settings(
                env="production",
                debug=False,
                data_dir=tmp_path,
                cleanup_enabled=False,
            )

        production = load(production_debug_off)
        assert production.docs_url is None
        assert production.redoc_url is None

        def production_debug_on():
            return config.Settings(
                env="production",
                debug=True,
                data_dir=tmp_path,
                cleanup_enabled=False,
            )

        forced = load(production_debug_on)
        assert forced.docs_url == "/docs"
        assert forced.redoc_url == "/redoc"
    finally:
        monkeypatch.setattr(config, "get_settings", real_get_settings)
        monkeypatch.setenv("DOC2ANY_ENV", "development")
        monkeypatch.setenv("DOC2ANY_DEBUG", "false")
        monkeypatch.setenv("DOC2ANY_CLEANUP_ENABLED", "false")
        monkeypatch.setenv("DOC2ANY_DATA_DIR", data_dir)
        real_get_settings.cache_clear()
        importlib.reload(main)
        assert main.app.docs_url == "/docs"
