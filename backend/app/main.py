from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .cleanup import cleanup_loop
from .config import Settings, get_settings
from .converters import (
    SUPPORTED_TARGETS,
    analyze_pdf_layout,
    convert_file,
    libreoffice_available,
)
from .rate_limit import limiter

logger = logging.getLogger("doc2any")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

_cleanup_stop: asyncio.Event | None = None
_cleanup_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _cleanup_stop, _cleanup_task
    settings = get_settings()
    settings.ensure_dirs()
    logger.info(
        "Doc2Any starting env=%s data_dir=%s output_dir=%s ttl=%ss rate=%s/min",
        settings.env,
        settings.data_dir,
        settings.resolved_output_dir,
        settings.file_ttl_seconds,
        settings.rate_limit_per_minute,
    )

    if settings.cleanup_enabled:
        _cleanup_stop = asyncio.Event()
        _cleanup_task = asyncio.create_task(
            cleanup_loop(
                settings.resolved_output_dir,
                ttl_seconds=settings.file_ttl_seconds,
                interval_seconds=settings.cleanup_interval_seconds,
                stop_event=_cleanup_stop,
            )
        )

    yield

    if _cleanup_stop is not None:
        _cleanup_stop.set()
    if _cleanup_task is not None:
        try:
            await asyncio.wait_for(_cleanup_task, timeout=5)
        except (asyncio.TimeoutError, asyncio.CancelledError):
            _cleanup_task.cancel()


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Layout-aware document conversion API",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url=None if settings.is_production and not settings.debug else "/docs",
    redoc_url=None if settings.is_production and not settings.debug else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    environment: str
    label: str
    libreoffice: bool
    targets: list[str]
    max_upload_mb: int
    file_ttl_seconds: int
    rate_limit_per_minute: int


class FormatsResponse(BaseModel):
    targets: list[str]
    libreoffice: bool
    routes: dict[str, list[str]]
    environment: str


ROUTES: dict[str, list[str]] = {
    "pdf": ["docx", "doc", "png", "jpg", "txt", "html"],
    "docx": ["pdf", "html", "txt", "doc", "odt", "rtf"],
    "doc": ["pdf", "docx", "html", "txt"],
    "png": ["jpg", "webp", "pdf", "docx"],
    "jpg": ["png", "webp", "pdf", "docx"],
    "jpeg": ["png", "webp", "pdf", "docx"],
    "webp": ["png", "jpg", "pdf"],
    "txt": ["docx", "pdf", "html"],
    "md": ["docx", "pdf", "html", "txt"],
    "html": ["pdf", "docx", "txt"],
    "pptx": ["pdf", "odp"],
    "xlsx": ["pdf", "ods", "csv"],
}


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _enforce_rate_limit(request: Request, *, kind: str) -> Settings:
    cfg = get_settings()
    if not cfg.rate_limit_enabled:
        return cfg
    ip = _client_ip(request)
    limit = (
        cfg.rate_limit_analyze_per_minute
        if kind == "analyze"
        else cfg.rate_limit_per_minute
    )
    key = f"{kind}:{ip}"
    if not limiter.allow(key, limit=limit, window_seconds=60.0):
        raise HTTPException(
            status_code=429,
            detail="請求過於頻繁，請稍後再試 / Too many requests, please retry later",
            headers={"Retry-After": "60"},
        )
    return cfg


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    cfg = get_settings()
    return HealthResponse(
        status="ok",
        environment=cfg.env,
        label=cfg.display_label,
        libreoffice=libreoffice_available(),
        targets=sorted(SUPPORTED_TARGETS),
        max_upload_mb=cfg.max_upload_mb,
        file_ttl_seconds=cfg.file_ttl_seconds,
        rate_limit_per_minute=cfg.rate_limit_per_minute,
    )


@app.get("/api/formats", response_model=FormatsResponse)
def formats() -> FormatsResponse:
    cfg = get_settings()
    return FormatsResponse(
        targets=sorted(SUPPORTED_TARGETS),
        libreoffice=libreoffice_available(),
        routes=ROUTES,
        environment=cfg.env,
    )


@app.post("/api/analyze")
async def analyze(request: Request, file: UploadFile = File(...)) -> dict:
    """Inspect PDF layout complexity / OCR need before converting."""
    cfg = _enforce_rate_limit(request, kind="analyze")

    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少檔案名稱")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空檔案")
    if len(raw) > cfg.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"檔案超過 {cfg.max_upload_mb}MB 限制",
        )

    job_id = uuid.uuid4().hex
    work = cfg.resolved_output_dir / job_id
    work.mkdir(parents=True, exist_ok=True)
    src_path = work / Path(file.filename).name
    src_path.write_bytes(raw)
    try:
        if src_path.suffix.lower() != ".pdf":
            return {
                "recommended_mode": "editable",
                "reason": "非 PDF，無需版面模式",
                "is_scanned": False,
                "complex_layout": False,
            }
        return analyze_pdf_layout(src_path)
    finally:
        shutil.rmtree(work, ignore_errors=True)


@app.post("/api/convert")
async def convert(
    request: Request,
    file: UploadFile = File(...),
    target_format: str = Form(...),
    layout_mode: str = Form("auto"),
) -> FileResponse:
    cfg = _enforce_rate_limit(request, kind="convert")

    target = target_format.lower().lstrip(".")
    if target == "jpeg":
        target = "jpg"

    mode = (layout_mode or "auto").lower().strip()
    if mode not in {"auto", "visual", "editable"}:
        raise HTTPException(
            status_code=400,
            detail="layout_mode 僅支援 auto / visual / editable",
        )

    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少檔案名稱")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空檔案")
    if len(raw) > cfg.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"檔案超過 {cfg.max_upload_mb}MB 限制",
        )

    job_id = uuid.uuid4().hex
    work = cfg.resolved_output_dir / job_id
    work.mkdir(parents=True, exist_ok=True)

    src_name = Path(file.filename).name
    src_path = work / src_name
    src_path.write_bytes(raw)

    try:
        result = convert_file(src_path, target, work, layout_mode=mode)
    except ValueError as exc:
        shutil.rmtree(work, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        shutil.rmtree(work, ignore_errors=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(work, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"轉換失敗: {exc}") from exc

    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "html": "text/html",
        "txt": "text/plain",
        "png": "image/png",
        "jpg": "image/jpeg",
        "webp": "image/webp",
        "zip": "application/zip",
        "odt": "application/vnd.oasis.opendocument.text",
        "rtf": "application/rtf",
    }
    suffix = result.suffix.lstrip(".").lower()
    download_name = f"{Path(src_name).stem}.{suffix}"

    return FileResponse(
        path=result,
        media_type=media_types.get(suffix, "application/octet-stream"),
        filename=download_name,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
