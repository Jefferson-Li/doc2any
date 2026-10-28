"""PDF→DOCX orchestration: detect, convert, score, retry."""

from __future__ import annotations

import json

from app.converters.pipeline import ConversionReport, convert_pdf_to_docx_pipeline


def _quality(mode, overall=90, layout=90, text=90):
    return {
        "overall": overall,
        "grade": "A",
        "layout_similarity": layout,
        "text_preservation": text,
        "image_preservation": 100,
        "element_alignment": 90,
        "page_structure": 90,
        "weights": {"layout_similarity": 1},
        "explain": {"layout_similarity": {"method": mode}},
        "thresholds": {"layout_retry": 70},
        "mode_used": mode,
    }


class _Engines:
    def __init__(self, monkeypatch, *, editable_error=False):
        self.calls = []
        self.editable_error = editable_error
        monkeypatch.setattr(
            "app.converters.engine.pdf_to_docx_visual", self.visual
        )
        monkeypatch.setattr(
            "app.converters.engine.pdf_to_docx_editable", self.editable
        )

    def visual(self, src, dst):
        self.calls.append(("visual", src, dst))
        dst.write_bytes(b"visual-docx")
        return dst

    def editable(self, src, dst):
        self.calls.append(("editable", src, dst))
        if self.editable_error:
            raise RuntimeError("positioned failed")
        dst.write_bytes(b"editable-docx")
        return dst


def _patch_score(monkeypatch, scores):
    def fake(src, dst, *, mode_used, layout):
        return scores[mode_used]

    monkeypatch.setattr("app.converters.pipeline.score_conversion", fake)


def test_report_round_trip(tmp_path):
    report = ConversionReport(
        path=tmp_path / "out.docx",
        mode_used="positioned",
        layout={"layout_type": "simple"},
        quality={"overall": 91, "grade": "A"},
        candidates=[
            {
                "mode": "positioned",
                "quality": {"overall": 91, "grade": "A", "text_preservation": 80},
            }
        ],
        retry={"from_mode": "positioned", "to_mode": "visual", "reason": "collapsed"},
    )
    payload = report.to_dict()
    assert payload["pipeline"] == [
        "layout_detection",
        "hybrid_conversion",
        "quality_score",
    ]
    assert payload["quality"]["overall"] == 91
    assert payload["quality"]["layout_similarity"] is None
    assert payload["candidates"][0]["text_preservation"] == 80
    assert payload["candidates"][0]["image_preservation"] is None
    assert payload["retry"]["reason"] == "collapsed"
    dest = report.write_json(tmp_path / "conversion_report.json")
    assert json.loads(dest.read_text(encoding="utf-8"))["mode_used"] == "positioned"


def test_forced_visual_and_editable(monkeypatch, tmp_path):
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF")
    engines = _Engines(monkeypatch)
    _patch_score(
        monkeypatch,
        {
            "visual": _quality("visual", 88),
            "positioned": _quality("positioned", 91),
        },
    )
    monkeypatch.setattr(
        "app.converters.pipeline.detect_layout",
        lambda path: {"is_scanned": False, "layout_type": "simple"},
    )

    visual_dst = tmp_path / "visual.docx"
    visual = convert_pdf_to_docx_pipeline(src, visual_dst, tmp_path, mode=" VISUAL ")
    assert visual.mode_used == "visual"
    assert visual_dst.read_bytes() == b"visual-docx"
    assert visual.quality["pipeline_step"] == "quality_score"
    assert [call[0] for call in engines.calls] == ["visual"]
    assert visual.retry is None

    engines.calls.clear()
    editable_dst = tmp_path / "edit.docx"
    editable = convert_pdf_to_docx_pipeline(src, editable_dst, tmp_path, mode="editable")
    assert editable.mode_used == "positioned"
    assert editable_dst.read_bytes() == b"editable-docx"
    assert [call[0] for call in engines.calls] == ["editable"]

    engines.calls.clear()
    monkeypatch.setattr(
        "app.converters.pipeline.detect_layout",
        lambda path: {"is_scanned": True, "layout_type": "scanned"},
    )
    scanned_dst = tmp_path / "scan.docx"
    scanned = convert_pdf_to_docx_pipeline(src, scanned_dst, tmp_path, mode="editable")
    assert scanned.mode_used == "visual"
    assert scanned_dst.read_bytes() == b"visual-docx"
    assert [call[0] for call in engines.calls] == ["visual"]
    assert scanned.candidates[0]["mode"] == "visual"


def test_auto_picks_editable_and_records_retry(monkeypatch, tmp_path):
    src = tmp_path / "doc.pdf"
    src.write_bytes(b"%PDF")
    engines = _Engines(monkeypatch)
    _patch_score(
        monkeypatch,
        {
            "visual": _quality("visual", overall=70, layout=95, text=90),
            "positioned": _quality("positioned", overall=92, layout=90, text=95),
        },
    )
    monkeypatch.setattr(
        "app.converters.pipeline.detect_layout",
        lambda path: {"is_scanned": False, "layout_type": "simple", "pages": 1},
    )
    dst = tmp_path / "out.docx"
    report = convert_pdf_to_docx_pipeline(src, dst, tmp_path, mode=None)
    assert report.mode_used == "positioned"
    assert dst.read_bytes() == b"editable-docx"
    assert report.retry is None
    assert report.layout["pipeline_step"] == "hybrid_conversion"
    assert report.layout["hybrid_selected"] == "positioned"
    assert [item["mode"] for item in report.candidates] == ["visual", "positioned"]
    saved = json.loads((report.write_json(tmp_path / "report.json")).read_text())
    assert saved["candidates"][1]["overall"] == 92

    engines.calls.clear()
    _patch_score(
        monkeypatch,
        {
            "visual": _quality("visual", overall=20, layout=80, text=90),
            "positioned": _quality("positioned", overall=0, layout=10, text=10),
        },
    )
    retry_dst = tmp_path / "retry.docx"
    retried = convert_pdf_to_docx_pipeline(src, retry_dst, tmp_path, mode="hybrid")
    assert retried.mode_used == "visual"
    assert retry_dst.read_bytes() == b"visual-docx"
    assert retried.retry["from_mode"] == "positioned"
    assert retried.retry["to_mode"] == "visual"
    assert "fallback" in retried.retry["reason"]


def test_auto_skips_editable_for_scans_and_swallows_editable_errors(monkeypatch, tmp_path):
    src = tmp_path / "scan.pdf"
    src.write_bytes(b"%PDF")
    engines = _Engines(monkeypatch)
    _patch_score(monkeypatch, {"visual": _quality("visual", 93), "positioned": _quality("positioned")})
    monkeypatch.setattr(
        "app.converters.pipeline.detect_layout",
        lambda path: {"is_scanned": True, "layout_type": "scanned"},
    )
    dst = tmp_path / "out.docx"
    report = convert_pdf_to_docx_pipeline(src, dst, tmp_path, mode="")
    assert report.mode_used == "visual"
    assert report.retry is None
    assert [call[0] for call in engines.calls] == ["visual"]

    broken = _Engines(monkeypatch, editable_error=True)
    monkeypatch.setattr(
        "app.converters.pipeline.detect_layout",
        lambda path: {"is_scanned": False, "layout_type": "simple"},
    )
    failed = tmp_path / "failed.docx"
    rescued = convert_pdf_to_docx_pipeline(src, failed, tmp_path, mode="auto")
    assert rescued.mode_used == "visual"
    assert failed.read_bytes() == b"visual-docx"
    assert "editable" in [call[0] for call in broken.calls]
    assert rescued.retry is None
