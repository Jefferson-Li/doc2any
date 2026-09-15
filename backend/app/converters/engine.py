"""Doc2Any conversion service — layout-aware document converters."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
import img2pdf
import mammoth
from docx import Document
from pdf2docx import Converter
from PIL import Image

SUPPORTED_TARGETS = {
    "pdf",
    "docx",
    "doc",
    "html",
    "txt",
    "png",
    "jpg",
    "jpeg",
    "webp",
}

IMAGE_EXTS = {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif"}
OFFICE_EXTS = {"doc", "docx", "odt", "rtf", "ppt", "pptx", "xls", "xlsx", "odp", "ods"}


def _ext(path: Path) -> str:
    return path.suffix.lower().lstrip(".")


def _find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    # Common macOS / Linux install paths
    for candidate in (
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/lib/libreoffice/program/soffice",
    ):
        if Path(candidate).exists():
            return candidate
    return None


def libreoffice_available() -> bool:
    return _find_soffice() is not None


def convert_with_libreoffice(src: Path, target_ext: str, out_dir: Path) -> Path:
    soffice = _find_soffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice 未安裝。請安裝 LibreOffice 以支援此轉換路徑，"
            "或改用 PDF→DOCX / 圖片格式轉換。"
        )

    # LibreOffice filter aliases
    filter_map = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "doc",
        "odt": "odt",
        "html": "html",
        "txt": "txt",
        "png": "png",
        "jpg": "jpg",
        "rtf": "rtf",
    }
    if target_ext not in filter_map:
        raise ValueError(f"LibreOffice 不支援輸出格式: .{target_ext}")

    cmd = [
        soffice,
        "--headless",
        "--nologo",
        "--nofirststartwizard",
        "--convert-to",
        filter_map[target_ext],
        "--outdir",
        str(out_dir),
        str(src),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice 轉換失敗: {result.stderr or result.stdout}")

    produced = out_dir / f"{src.stem}.{target_ext}"
    if not produced.exists():
        # LibreOffice may normalize jpeg → jpg etc.
        matches = list(out_dir.glob(f"{src.stem}.*"))
        if not matches:
            raise RuntimeError("LibreOffice 未產生輸出檔案")
        produced = matches[0]
    return produced


def pdf_to_docx(src: Path, dst: Path) -> Path:
    """Layout-preserving PDF → DOCX via pdf2docx (paragraphs, tables, images)."""
    cv = Converter(str(src))
    try:
        cv.convert(str(dst))
    finally:
        cv.close()
    return dst


def pdf_to_images(src: Path, out_dir: Path, fmt: str = "png") -> list[Path]:
    doc = fitz.open(src)
    paths: list[Path] = []
    try:
        for i, page in enumerate(doc):
            # 2x zoom for sharper output
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            out = out_dir / f"{src.stem}_p{i + 1}.{fmt}"
            pix.save(str(out))
            paths.append(out)
    finally:
        doc.close()
    return paths


def pdf_to_text(src: Path, dst: Path) -> Path:
    doc = fitz.open(src)
    try:
        parts = [page.get_text("text") for page in doc]
    finally:
        doc.close()
    dst.write_text("\n\n".join(parts), encoding="utf-8")
    return dst


def pdf_to_html(src: Path, dst: Path) -> Path:
    doc = fitz.open(src)
    try:
        chunks = ['<!DOCTYPE html><html><head><meta charset="utf-8">',
                  "<title>converted</title>",
                  "<style>body{font-family:system-ui,sans-serif;max-width:800px;margin:2rem auto;line-height:1.6}"
                  "pre{white-space:pre-wrap}</style></head><body>"]
        for i, page in enumerate(doc):
            chunks.append(f"<section><h2>Page {i + 1}</h2>")
            chunks.append(f"<pre>{page.get_text('text')}</pre></section>")
        chunks.append("</body></html>")
    finally:
        doc.close()
    dst.write_text("\n".join(chunks), encoding="utf-8")
    return dst


def docx_to_html(src: Path, dst: Path) -> Path:
    with open(src, "rb") as f:
        result = mammoth.convert_to_html(f)
    html = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>converted</title>"
        "<style>body{font-family:Georgia,serif;max-width:800px;margin:2rem auto;line-height:1.7}"
        "img{max-width:100%}</style></head><body>"
        f"{result.value}</body></html>"
    )
    dst.write_text(html, encoding="utf-8")
    return dst


def docx_to_txt(src: Path, dst: Path) -> Path:
    document = Document(str(src))
    lines = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            lines.append("\t".join(cell.text for cell in row.cells))
    dst.write_text("\n".join(lines), encoding="utf-8")
    return dst


def images_to_pdf(images: list[Path], dst: Path) -> Path:
    # Normalize to RGB JPEG/PNG bytes for img2pdf
    prepared: list[bytes] = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        for i, img_path in enumerate(images):
            im = Image.open(img_path)
            if im.mode in ("RGBA", "P"):
                im = im.convert("RGB")
            buf = tmp_path / f"page_{i}.jpg"
            im.save(buf, "JPEG", quality=95)
            prepared.append(buf.read_bytes())
        dst.write_bytes(img2pdf.convert(prepared))
    return dst


def convert_image(src: Path, dst: Path) -> Path:
    im = Image.open(src)
    target = _ext(dst)
    if target in ("jpg", "jpeg"):
        if im.mode in ("RGBA", "P"):
            im = im.convert("RGB")
        im.save(dst, "JPEG", quality=95)
    elif target == "png":
        im.save(dst, "PNG")
    elif target == "webp":
        im.save(dst, "WEBP", quality=90)
    else:
        im.save(dst)
    return dst


def text_to_docx(src: Path, dst: Path) -> Path:
    document = Document()
    for line in src.read_text(encoding="utf-8", errors="ignore").splitlines():
        document.add_paragraph(line)
    document.save(str(dst))
    return dst


def text_to_pdf(src: Path, dst: Path) -> Path:
    """Simple text → PDF with preserved line breaks (monospace layout)."""
    text = src.read_text(encoding="utf-8", errors="ignore")
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    margin = 50
    rect = fitz.Rect(margin, margin, 595 - margin, 842 - margin)
    page.insert_textbox(rect, text, fontsize=11, fontname="helv", align=0)
    doc.save(str(dst))
    doc.close()
    return dst


def convert_file(src: Path, target_ext: str, work_dir: Path) -> Path:
    """Route conversion to the best available engine for the pair."""
    target_ext = target_ext.lower().lstrip(".")
    if target_ext == "jpeg":
        target_ext = "jpg"
    if target_ext not in SUPPORTED_TARGETS and target_ext not in {"odt", "rtf"}:
        raise ValueError(f"不支援的目標格式: .{target_ext}")

    src_ext = _ext(src)
    dst = work_dir / f"{src.stem}.{target_ext}"

    if src_ext == target_ext:
        shutil.copy2(src, dst)
        return dst

    # --- PDF source (layout-first) ---
    if src_ext == "pdf":
        if target_ext == "docx":
            return pdf_to_docx(src, dst)
        if target_ext in ("png", "jpg"):
            pages = pdf_to_images(src, work_dir, fmt=target_ext)
            if len(pages) == 1:
                pages[0].rename(dst)
                return dst
            # Multi-page: zip them
            import zipfile

            zip_path = work_dir / f"{src.stem}_pages.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                for p in pages:
                    zf.write(p, p.name)
            return zip_path
        if target_ext == "txt":
            return pdf_to_text(src, dst)
        if target_ext == "html":
            return pdf_to_html(src, dst)
        if target_ext == "doc":
            # via docx then LibreOffice if available
            interim = work_dir / f"{src.stem}.docx"
            pdf_to_docx(src, interim)
            if libreoffice_available():
                return convert_with_libreoffice(interim, "doc", work_dir)
            raise RuntimeError("PDF→DOC 需要 LibreOffice；請改選 DOCX。")

    # --- DOCX source ---
    if src_ext in ("docx", "doc"):
        if src_ext == "doc" or target_ext in ("pdf", "odt", "rtf", "doc"):
            if libreoffice_available():
                return convert_with_libreoffice(src, target_ext, work_dir)
            if src_ext == "docx" and target_ext == "html":
                return docx_to_html(src, dst)
            if src_ext == "docx" and target_ext == "txt":
                return docx_to_txt(src, dst)
            raise RuntimeError(
                f".{src_ext}→.{target_ext} 需要安裝 LibreOffice 才能保版轉換。"
            )
        if target_ext == "html":
            return docx_to_html(src, dst)
        if target_ext == "txt":
            return docx_to_txt(src, dst)
        if target_ext == "pdf":
            if libreoffice_available():
                return convert_with_libreoffice(src, "pdf", work_dir)
            raise RuntimeError("DOCX→PDF 需要安裝 LibreOffice。")

    # --- Images ---
    if src_ext in IMAGE_EXTS:
        if target_ext == "pdf":
            return images_to_pdf([src], dst)
        if target_ext in IMAGE_EXTS or target_ext in ("png", "jpg", "webp"):
            return convert_image(src, dst)
        if target_ext == "docx":
            document = Document()
            document.add_picture(str(src))
            document.save(str(dst))
            return dst

    # --- Plain text ---
    if src_ext in ("txt", "md", "csv", "log"):
        if target_ext == "docx":
            return text_to_docx(src, dst)
        if target_ext == "pdf":
            return text_to_pdf(src, dst)
        if target_ext == "txt":
            shutil.copy2(src, dst)
            return dst
        if target_ext == "html":
            body = src.read_text(encoding="utf-8", errors="ignore")
            dst.write_text(
                f"<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
                f"<body><pre>{body}</pre></body></html>",
                encoding="utf-8",
            )
            return dst

    # --- HTML ---
    if src_ext in ("html", "htm"):
        if libreoffice_available() and target_ext in ("pdf", "docx", "odt", "txt"):
            return convert_with_libreoffice(src, target_ext, work_dir)
        if target_ext == "txt":
            # strip tags lightly
            import re

            raw = src.read_text(encoding="utf-8", errors="ignore")
            text = re.sub(r"<[^>]+>", "", raw)
            dst.write_text(text, encoding="utf-8")
            return dst

    # Fallback: LibreOffice for office suites
    if libreoffice_available() and (
        src_ext in OFFICE_EXTS or target_ext in OFFICE_EXTS or target_ext == "pdf"
    ):
        return convert_with_libreoffice(src, target_ext, work_dir)

    raise ValueError(
        f"目前不支援 .{src_ext} → .{target_ext}。"
        + (
            " 安裝 LibreOffice 後可擴充更多格式。"
            if not libreoffice_available()
            else ""
        )
    )
