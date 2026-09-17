"""PDF→DOCX pipeline: Layout Detection → Hybrid Conversion → Quality Score."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .layout_detect import detect_layout
from .quality import pick_best_candidate, score_conversion


@dataclass
class ConversionReport:
    path: Path
    mode_used: str
    layout: dict[str, Any]
    quality: dict[str, Any]
    candidates: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pipeline": [
                "layout_detection",
                "hybrid_conversion",
                "quality_score",
            ],
            "path": str(self.path),
            "mode_used": self.mode_used,
            "layout": self.layout,
            "quality": self.quality,
            "candidates": [
                {
                    "mode": c["mode"],
                    "overall": c["quality"]["overall"],
                    "grade": c["quality"]["grade"],
                    "layout_fidelity": c["quality"]["layout_fidelity"],
                    "text_completeness": c["quality"]["text_completeness"],
                    "editability": c["quality"]["editability"],
                }
                for c in self.candidates
            ],
        }

    def write_json(self, dest: Path) -> Path:
        dest.write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return dest


def convert_pdf_to_docx_pipeline(
    src: Path,
    dst: Path,
    work_dir: Path,
    *,
    mode: str = "auto",
    # late imports avoid circular deps with engine helpers
) -> ConversionReport:
    """Run detection → hybrid (or forced mode) → quality scoring."""
    from .engine import pdf_to_docx_editable, pdf_to_docx_visual

    mode = (mode or "auto").lower().strip()
    layout = detect_layout(src)

    # Forced single-engine modes still get scored
    if mode in {"visual", "editable"}:
        if mode == "visual":
            pdf_to_docx_visual(src, dst)
        else:
            if layout.get("is_scanned"):
                # editable on pure scans is useless — fall back visually
                pdf_to_docx_visual(src, dst)
                mode = "visual"
            else:
                pdf_to_docx_editable(src, dst)
        quality = score_conversion(src, dst, mode_used=mode, layout=layout)
        return ConversionReport(
            path=dst,
            mode_used=mode,
            layout=layout,
            quality=quality,
            candidates=[{"mode": mode, "path": dst, "quality": quality}],
        )

    # auto / hybrid: build candidates and pick best
    candidates: list[dict[str, Any]] = []

    visual_path = work_dir / f"{src.stem}.__visual__.docx"
    pdf_to_docx_visual(src, visual_path)
    v_quality = score_conversion(src, visual_path, mode_used="visual", layout=layout)
    candidates.append({"mode": "visual", "path": visual_path, "quality": v_quality})

    if not layout.get("is_scanned"):
        editable_path = work_dir / f"{src.stem}.__editable__.docx"
        try:
            pdf_to_docx_editable(src, editable_path)
            e_quality = score_conversion(
                src, editable_path, mode_used="editable", layout=layout
            )
            candidates.append(
                {"mode": "editable", "path": editable_path, "quality": e_quality}
            )
        except Exception:  # noqa: BLE001
            # Keep visual-only if editable engine crashes on exotic PDFs
            pass

    best = pick_best_candidate(candidates, layout)
    shutil.copy2(best["path"], dst)

    report = ConversionReport(
        path=dst,
        mode_used=best["mode"],
        layout=layout,
        quality=best["quality"],
        candidates=candidates,
    )
    report.layout = {
        **layout,
        "pipeline_step": "hybrid_conversion",
        "hybrid_selected": best["mode"],
    }
    # Re-tag quality step for clarity
    report.quality = {**best["quality"], "pipeline_step": "quality_score"}
    return report
