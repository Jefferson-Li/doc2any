"""Layout Detection — classify PDF structure before conversion."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz


DESIGN_TOOLS = ("canva", "figma", "adobe illustrator", "sketch", "indesign")


def _page_metrics(page: fitz.Page) -> dict[str, Any]:
    text = page.get_text("text") or ""
    chars = len(text.strip())
    blocks = page.get_text("dict").get("blocks") or []
    text_blocks = [b for b in blocks if b.get("type") == 0]
    image_blocks = [b for b in blocks if b.get("type") == 1]
    drawings = page.get_drawings()

    # Rough column hint: cluster text block x0 positions
    xs = sorted(
        float(b["bbox"][0])
        for b in text_blocks
        if "bbox" in b and (b.get("lines") or True)
    )
    columns = 1
    if len(xs) >= 4:
        gaps = []
        for a, b in zip(xs, xs[1:]):
            if b - a > 80:  # large horizontal gap between block origins
                gaps.append(b - a)
        # Distinct x-clusters
        clusters = [xs[0]]
        for x in xs[1:]:
            if x - clusters[-1] > 120:
                clusters.append(x)
        columns = min(3, max(1, len(clusters)))

    width = float(page.rect.width) or 1.0
    # Density of absolute boxes
    blocks_per_width = len(text_blocks) / max(1.0, width / 100.0)

    is_scanned = chars < 40 and len(image_blocks) > 0
    complex_layout = (
        len(drawings) >= 15
        or len(text_blocks) >= 25
        or columns >= 2 and len(text_blocks) >= 12
        or blocks_per_width >= 4.5
    )

    if is_scanned:
        layout_type = "scanned"
        recommended = "visual"
    elif complex_layout:
        layout_type = "complex"
        recommended = "visual"
    else:
        layout_type = "simple"
        recommended = "editable"

    return {
        "page_index": page.number,
        "chars": chars,
        "text_blocks": len(text_blocks),
        "image_blocks": len(image_blocks),
        "drawings": len(drawings),
        "columns_estimate": columns,
        "is_scanned": is_scanned,
        "complex_layout": complex_layout,
        "layout_type": layout_type,
        "recommended_mode": recommended,
    }


def detect_layout(src: Path) -> dict[str, Any]:
    """Full-document layout detection with per-page breakdown."""
    doc = fitz.open(src)
    try:
        producer = (doc.metadata or {}).get("producer") or ""
        creator = (doc.metadata or {}).get("creator") or ""
        pages_detail = [_page_metrics(page) for page in doc]
        page_count = doc.page_count
    finally:
        doc.close()

    total_chars = sum(p["chars"] for p in pages_detail)
    total_text_blocks = sum(p["text_blocks"] for p in pages_detail)
    total_image_blocks = sum(p["image_blocks"] for p in pages_detail)
    total_drawings = sum(p["drawings"] for p in pages_detail)
    max_columns = max((p["columns_estimate"] for p in pages_detail), default=1)

    designed_tool = any(
        key in f"{producer} {creator}".lower() for key in DESIGN_TOOLS
    )
    is_scanned = bool(pages_detail) and all(p["is_scanned"] for p in pages_detail)
    complex_layout = designed_tool or any(p["complex_layout"] for p in pages_detail)

    # Document-level type
    if is_scanned:
        layout_type = "scanned"
    elif designed_tool:
        layout_type = "designed"
    elif complex_layout:
        layout_type = "complex"
    else:
        layout_type = "simple"

    mixed = len({p["recommended_mode"] for p in pages_detail}) > 1

    if is_scanned or designed_tool or (complex_layout and not mixed):
        recommended = "visual"
    elif mixed:
        recommended = "hybrid"
    else:
        recommended = "editable"

    confidence = 0.55
    if designed_tool or is_scanned:
        confidence = 0.92
    elif layout_type == "simple" and total_chars > 200:
        confidence = 0.8
    elif mixed:
        confidence = 0.7
    else:
        confidence = 0.65

    reason_zh = {
        "scanned": "掃描影像 PDF（無文字層，需 OCR 才能可編輯）",
        "designed": "設計稿工具匯出（如 Canva），建議視覺／混合保版",
        "complex": "多欄或高密度絕對定位，文字重建容易跑版",
        "simple": "文字流動版面，可嘗試可編輯或混合轉換",
    }[layout_type]

    return {
        "pages": page_count,
        "text_chars": total_chars,
        "text_blocks": total_text_blocks,
        "image_blocks": total_image_blocks,
        "drawings": total_drawings,
        "columns_estimate": max_columns,
        "producer": producer,
        "creator": creator,
        "designed_tool": designed_tool,
        "is_scanned": is_scanned,
        "complex_layout": complex_layout,
        "mixed_pages": mixed,
        "layout_type": layout_type,
        "recommended_mode": recommended,
        "confidence": round(confidence, 2),
        "reason": reason_zh,
        "pages_detail": pages_detail,
        # pipeline step marker
        "pipeline_step": "layout_detection",
    }


# Backwards-compatible alias used across the app
def analyze_pdf_layout(src: Path) -> dict[str, Any]:
    return detect_layout(src)
