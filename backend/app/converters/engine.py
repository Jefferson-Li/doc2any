"""Doc2Any conversion service — layout-aware document converters."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

import fitz  # PyMuPDF
import img2pdf
import mammoth
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Emu, Pt
from pdf2docx import Converter
from PIL import Image

# 1 PDF point = 12700 EMU
_PT_TO_EMU = 12700

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


def _zero_paragraph_spacing(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    for child in list(p_pr):
        if child.tag in (qn("w:spacing"), qn("w:ind")):
            p_pr.remove(child)
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "0")
    spacing.set(qn("w:line"), "240")
    spacing.set(qn("w:lineRule"), "auto")
    p_pr.append(spacing)


def analyze_pdf_layout(src: Path) -> dict:
    """Detect whether PDF is scanned / designed (Canva) / simple flowing text.

    Not an OCR issue when text_chars > 0 — Canva and multi-column PDFs still
    break under flowing-text reconstruction (pdf2docx).
    """
    doc = fitz.open(src)
    try:
        total_chars = 0
        total_text_blocks = 0
        total_image_blocks = 0
        total_drawings = 0
        pages = doc.page_count
        producer = (doc.metadata or {}).get("producer") or ""
        creator = (doc.metadata or {}).get("creator") or ""
        for page in doc:
            text = page.get_text("text") or ""
            total_chars += len(text.strip())
            blocks = page.get_text("dict").get("blocks") or []
            total_text_blocks += sum(1 for b in blocks if b.get("type") == 0)
            total_image_blocks += sum(1 for b in blocks if b.get("type") == 1)
            total_drawings += len(page.get_drawings())
    finally:
        doc.close()

    is_scanned = total_chars < 40 and total_image_blocks > 0
    designed_tool = any(
        key in f"{producer} {creator}".lower()
        for key in ("canva", "figma", "adobe illustrator", "sketch")
    )
    # Many absolute text boxes + vector decorations ⇒ complex floating layout
    complex_layout = (
        designed_tool
        or total_drawings >= 20
        or (pages > 0 and total_text_blocks / pages >= 25)
    )
    recommended = "visual" if (is_scanned or complex_layout) else "editable"
    return {
        "pages": pages,
        "text_chars": total_chars,
        "text_blocks": total_text_blocks,
        "image_blocks": total_image_blocks,
        "drawings": total_drawings,
        "producer": producer,
        "creator": creator,
        "is_scanned": is_scanned,
        "complex_layout": complex_layout,
        "recommended_mode": recommended,
        "reason": (
            "掃描影像 PDF（無文字層，需 OCR 才能可編輯）"
            if is_scanned
            else (
                "設計稿／多欄絕對定位（如 Canva），文字重建會跑版"
                if complex_layout
                else "文字流動版面，可嘗試可編輯重建"
            )
        ),
    }


def pdf_to_docx_visual(src: Path, dst: Path, *, dpi: float = 200) -> Path:
    """Pixel-faithful PDF → DOCX: each page becomes a full-page image.

    Guarantees layout for Canva/multi-column resumes. Text is not reflow-editable.
    """
    pdf = fitz.open(src)
    document = Document()
    zoom = dpi / 72.0
    try:
        for i, page in enumerate(pdf):
            width_pt = float(page.rect.width)
            height_pt = float(page.rect.height)
            section = document.sections[0] if i == 0 else document.add_section()
            section.page_width = Emu(int(width_pt * _PT_TO_EMU))
            section.page_height = Emu(int(height_pt * _PT_TO_EMU))
            section.left_margin = Emu(0)
            section.right_margin = Emu(0)
            section.top_margin = Emu(0)
            section.bottom_margin = Emu(0)

            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = BytesIO(pix.tobytes("png"))
            paragraph = (
                document.paragraphs[0]
                if i == 0 and document.paragraphs
                else document.add_paragraph()
            )
            if i > 0:
                paragraph = document.add_paragraph()
            _zero_paragraph_spacing(paragraph)
            paragraph.paragraph_format.space_before = Pt(0)
            paragraph.paragraph_format.space_after = Pt(0)
            run = paragraph.add_run()
            run.add_picture(img, width=Emu(int(width_pt * _PT_TO_EMU)))
    finally:
        pdf.close()

    document.save(str(dst))
    return dst


def pdf_to_docx_editable(src: Path, dst: Path) -> Path:
    """Editable reconstruction via pdf2docx (best for simple single-column docs)."""
    cv = Converter(str(src))
    try:
        # Tighter thresholds reduce spurious tables / broken sections on dense pages
        cv.convert(
            str(dst),
            line_separate_threshold=3.0,
            float_image_ignorable_gap=2.0,
            min_section_height=12.0,
            connected_border_tolerance=0.2,
            parse_stream_table=False,
            extract_stream_table=False,
            delete_end_line_hyphen=True,
        )
    finally:
        cv.close()
    return dst


def pdf_to_docx(src: Path, dst: Path, *, mode: str = "auto") -> Path:
    """PDF → DOCX with layout-aware engine selection.

    Modes:
      - auto: complex/Canva/scanned → visual; otherwise editable
      - visual: page images (no reflow) — true 不跑版
      - editable: pdf2docx text reconstruction
    """
    mode = (mode or "auto").lower().strip()
    if mode == "auto":
        mode = analyze_pdf_layout(src)["recommended_mode"]
    if mode == "visual":
        return pdf_to_docx_visual(src, dst)
    if mode == "editable":
        return pdf_to_docx_editable(src, dst)
    raise ValueError(f"未知的 layout_mode: {mode}（請用 auto / visual / editable）")


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


def convert_file(
    src: Path,
    target_ext: str,
    work_dir: Path,
    *,
    layout_mode: str = "auto",
) -> Path:
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
            return pdf_to_docx(src, dst, mode=layout_mode)
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
            pdf_to_docx(src, interim, mode=layout_mode)
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
