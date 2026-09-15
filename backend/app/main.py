from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .converters import (
    SUPPORTED_TARGETS,
    analyze_pdf_layout,
    convert_file,
    libreoffice_available,
)

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

app = FastAPI(
    title="Doc2Any",
    description="Layout-aware document conversion API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    libreoffice: bool
    targets: list[str]


class FormatsResponse(BaseModel):
    targets: list[str]
    libreoffice: bool
    routes: dict[str, list[str]]


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


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        libreoffice=libreoffice_available(),
        targets=sorted(SUPPORTED_TARGETS),
    )


@app.get("/api/formats", response_model=FormatsResponse)
def formats() -> FormatsResponse:
    return FormatsResponse(
        targets=sorted(SUPPORTED_TARGETS),
        libreoffice=libreoffice_available(),
        routes=ROUTES,
    )


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)) -> dict:
    """Inspect PDF layout complexity / OCR need before converting."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="缺少檔案名稱")
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="空檔案")

    job_id = uuid.uuid4().hex
    work = OUTPUT_DIR / job_id
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
    file: UploadFile = File(...),
    target_format: str = Form(...),
    layout_mode: str = Form("auto"),
) -> FileResponse:
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
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="檔案超過 50MB 限制")

    job_id = uuid.uuid4().hex
    work = OUTPUT_DIR / job_id
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
