"""Conversion Quality Score — evaluate PDF→DOCX output fidelity."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import fitz
from docx import Document


_SPACE_LETTER = re.compile(
    r"(?:\b(?:[A-Za-z0-9]\s+){3,}[A-Za-z0-9]\b)|(?:(?:[\u4e00-\u9fff]\s+){3,}[\u4e00-\u9fff])"
)


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text("text") or "" for page in doc)
    finally:
        doc.close()


def _docx_text(path: Path) -> str:
    document = Document(str(path))
    parts: list[str] = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            parts.append("\t".join(cell.text for cell in row.cells))
    return "\n".join(parts)


def _docx_stats(path: Path) -> dict[str, int]:
    document = Document(str(path))
    inline = len(document.inline_shapes)
    return {
        "paragraphs": len(document.paragraphs),
        "tables": len(document.tables),
        "sections": len(document.sections),
        "inline_shapes": inline,
    }


def _spaced_out_ratio(text: str) -> float:
    if not text.strip():
        return 0.0
    hits = _SPACE_LETTER.findall(text)
    # Rough: fraction of characters inside spaced-out matches
    hit_len = sum(len(h) for h in hits)
    return min(1.0, hit_len / max(1, len(text)))


def _text_overlap(a: str, b: str) -> float:
    """Token Jaccard overlap — lightweight text completeness signal."""
    ta = set(_normalize(a).split())
    tb = set(_normalize(b).split())
    if not ta and not tb:
        return 1.0
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def score_conversion(
    pdf_path: Path,
    docx_path: Path,
    *,
    mode_used: str,
    layout: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return 0–100 scores: layout / text / editability / overall."""
    layout = layout or {}
    pdf_txt = _pdf_text(pdf_path)
    docx_txt = _docx_text(docx_path)
    stats = _docx_stats(docx_path)
    spaced = _spaced_out_ratio(docx_txt)
    overlap = _text_overlap(pdf_txt, docx_txt)

    pdf_chars = len(pdf_txt.strip())
    docx_chars = len(docx_txt.strip())
    char_coverage = (
        1.0
        if pdf_chars == 0 and mode_used == "visual"
        else min(1.0, docx_chars / max(1, pdf_chars))
        if mode_used != "visual"
        else (0.85 if pdf_chars > 0 else 0.95)
    )

    # --- layout fidelity ---
    if mode_used == "visual":
        layout_score = 96.0
        if layout.get("is_scanned"):
            layout_score = 94.0
    else:
        layout_score = 35.0 + 55.0 * overlap - 40.0 * spaced
        if layout.get("complex_layout") or layout.get("layout_type") in {
            "complex",
            "designed",
        }:
            layout_score *= 0.55
        if stats["sections"] > max(3, (layout.get("pages") or 1) * 2):
            layout_score -= 12  # pdf2docx often explodes sections on bad layouts

    # --- text completeness ---
    if mode_used == "visual":
        # Visual keeps glyphs as pixels; credit high when source had text or is scan
        text_score = 88.0 if pdf_chars > 0 or layout.get("is_scanned") else 70.0
    else:
        text_score = 100.0 * (0.65 * overlap + 0.35 * char_coverage) - 35.0 * spaced

    # --- editability ---
    if mode_used == "visual":
        edit_score = 18.0
        if stats["inline_shapes"] > 0:
            edit_score = 22.0
    else:
        edit_score = 92.0 - 50.0 * spaced
        if stats["paragraphs"] + stats["tables"] < 2 and pdf_chars > 80:
            edit_score -= 20

    layout_score = max(0.0, min(100.0, layout_score))
    text_score = max(0.0, min(100.0, text_score))
    edit_score = max(0.0, min(100.0, edit_score))

    # Prefer layout for designed/complex; prefer editability for simple
    if layout.get("layout_type") in {"designed", "complex", "scanned"}:
        overall = 0.55 * layout_score + 0.25 * text_score + 0.20 * edit_score
    else:
        overall = 0.35 * layout_score + 0.35 * text_score + 0.30 * edit_score

    grade = (
        "A"
        if overall >= 85
        else "B"
        if overall >= 70
        else "C"
        if overall >= 55
        else "D"
    )

    return {
        "pipeline_step": "quality_score",
        "mode_used": mode_used,
        "overall": round(overall, 1),
        "grade": grade,
        "layout_fidelity": round(layout_score, 1),
        "text_completeness": round(text_score, 1),
        "editability": round(edit_score, 1),
        "metrics": {
            "text_overlap": round(overlap, 3),
            "char_coverage": round(char_coverage, 3),
            "spaced_out_ratio": round(spaced, 3),
            "docx": stats,
            "pdf_chars": pdf_chars,
            "docx_chars": docx_chars,
        },
    }


def pick_best_candidate(
    candidates: list[dict[str, Any]],
    layout: dict[str, Any],
) -> dict[str, Any]:
    """Choose winning conversion using layout-aware weighting."""
    if not candidates:
        raise ValueError("No conversion candidates")

    layout_type = layout.get("layout_type", "simple")

    def key(c: dict[str, Any]) -> float:
        q = c["quality"]
        if layout_type in {"designed", "complex", "scanned"}:
            return (
                0.6 * q["layout_fidelity"]
                + 0.25 * q["overall"]
                + 0.15 * q["text_completeness"]
            )
        # simple docs: reward editable if quality is close
        bonus = 4.0 if c["mode"] == "editable" and q["overall"] >= 65 else 0.0
        return q["overall"] + bonus

    return max(candidates, key=key)
