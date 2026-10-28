"""Layout detection on generated PDFs and crafted page metrics."""

from __future__ import annotations

import fitz

from app.converters.layout_detect import (
    DESIGN_TOOLS,
    _page_metrics,
    analyze_pdf_layout,
    detect_layout,
)
from tests.support import add_page, solid_image, write_pdf


class _Rect:
    def __init__(self, width: float, height: float = 800):
        self.width = width
        self.height = height


class FakePage:
    def __init__(self, text="", blocks=None, drawings=None, width=600, number=0):
        self._text = text
        self._blocks = blocks or []
        self._drawings = drawings if drawings is not None else []
        self.rect = _Rect(width)
        self.number = number

    def get_text(self, kind="text"):
        if kind == "dict":
            return {"blocks": self._blocks}
        return self._text

    def get_drawings(self):
        return self._drawings


class FakeDoc:
    def __init__(self, pages, metadata=None):
        self._pages = list(pages)
        self.metadata = metadata
        self.page_count = len(self._pages)
        self.closed = False

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        self.closed = True


def _block(x, lines=True, kind=0):
    return {
        "type": kind,
        "bbox": (x, 0, x + 10, 10),
        "lines": [{"spans": []}] if lines else [],
    }


def test_page_metrics_cover_column_and_complexity_rules():
    simple = _page_metrics(FakePage(text="hello", blocks=[_block(10)], width=500))
    assert simple["layout_type"] == "simple"
    assert simple["columns_estimate"] == 1
    assert simple["is_scanned"] is False
    assert simple["complex_layout"] is False

    scanned = _page_metrics(
        FakePage(text="x" * 10, blocks=[_block(0, kind=1)], width=400)
    )
    assert scanned["is_scanned"] is True
    assert scanned["layout_type"] == "scanned"
    assert scanned["recommended_mode"] == "visual"

    short_without_image = _page_metrics(FakePage(text="hi", blocks=[_block(1)]))
    assert short_without_image["is_scanned"] is False

    long_with_image = _page_metrics(
        FakePage(text="y" * 50, blocks=[_block(1), _block(2, kind=1)])
    )
    assert long_with_image["is_scanned"] is False

    drawings = _page_metrics(
        FakePage(text="z" * 50, blocks=[_block(1)], drawings=list(range(15)))
    )
    assert drawings["complex_layout"] is True
    assert drawings["layout_type"] == "complex"

    many_blocks = _page_metrics(
        FakePage(text="z" * 80, blocks=[_block(i) for i in range(25)], width=400)
    )
    assert many_blocks["complex_layout"] is True

    close_gaps = _page_metrics(
        FakePage(
            text="z" * 40,
            blocks=[_block(x) for x in (0, 90, 100, 110)],
            width=600,
        )
    )
    assert close_gaps["columns_estimate"] == 1
    assert close_gaps["complex_layout"] is False

    wide_steps = _page_metrics(
        FakePage(
            text="z" * 40,
            blocks=[_block(x) for x in (0, 100, 200, 300)],
            width=800,
        )
    )
    assert wide_steps["columns_estimate"] == 2

    four_columns = _page_metrics(
        FakePage(
            text="z" * 40,
            blocks=[_block(x) for x in (0, 150, 300, 450)],
            width=800,
        )
    )
    assert four_columns["columns_estimate"] == 3

    two_col_complex = _page_metrics(
        FakePage(
            text="z" * 80,
            blocks=[_block(0 if i < 6 else 400) for i in range(12)],
            width=800,
        )
    )
    assert two_col_complex["columns_estimate"] >= 2
    assert two_col_complex["complex_layout"] is True

    two_col_sparse = _page_metrics(
        FakePage(
            text="z" * 40,
            blocks=[_block(0), _block(0), _block(400), _block(400)],
            width=900,
        )
    )
    assert two_col_sparse["columns_estimate"] == 2
    assert two_col_sparse["text_blocks"] < 12
    assert two_col_sparse["complex_layout"] is False

    dense = _page_metrics(
        FakePage(text="z" * 40, blocks=[_block(10) for _ in range(5)], width=80)
    )
    assert dense["complex_layout"] is True

    narrow = _page_metrics(FakePage(text="z" * 40, blocks=[_block(1)], width=50))
    assert narrow["layout_type"] == "simple"

    zero_width = _page_metrics(FakePage(text="z" * 40, blocks=[_block(1)], width=0))
    assert zero_width["chars"] == 40

    missing_bbox = _page_metrics(
        FakePage(
            text="abc",
            blocks=[
                {"type": 0, "lines": []},
                {"type": 0, "bbox": (5, 0, 15, 10)},
                {"type": 2, "bbox": (9, 0, 12, 4)},
            ],
        )
    )
    assert missing_bbox["text_blocks"] == 2
    assert missing_bbox["columns_estimate"] == 1


def test_detect_layout_on_generated_pdfs(tmp_path):
    simple = write_pdf(
        tmp_path / "simple.pdf",
        lambda doc: add_page(doc, "Just a simple sentence."),
    )
    simple_info = detect_layout(simple)
    assert simple_info["pipeline_step"] == "layout_detection"
    assert simple_info["pages"] == 1
    assert simple_info["layout_type"] == "simple"
    assert simple_info["recommended_mode"] == "editable"
    assert simple_info["confidence"] == 0.65
    assert simple_info["mixed_pages"] is False
    assert "文字流動" in simple_info["reason"]
    assert analyze_pdf_layout(simple) == simple_info

    def draw_long(doc):
        page = doc.new_page()
        for index in range(15):
            page.insert_text((72, 40 + index * 30), "alphabet words " * 4)

    long = write_pdf(tmp_path / "long.pdf", draw_long)
    long_info = detect_layout(long)
    assert long_info["layout_type"] == "simple"
    assert long_info["confidence"] == 0.8
    assert long_info["text_chars"] > 200

    image = solid_image(tmp_path / "scan.png", size=(40, 40), color=(10, 10, 10))

    def draw_scan(doc):
        page = doc.new_page()
        page.insert_image(page.rect, filename=str(image))

    scanned = detect_layout(write_pdf(tmp_path / "scan.pdf", draw_scan))
    assert scanned["layout_type"] == "scanned"
    assert scanned["is_scanned"] is True
    assert scanned["recommended_mode"] == "visual"
    assert scanned["confidence"] == 0.92
    assert "掃描" in scanned["reason"]

    def draw_canva(doc):
        add_page(doc, "Designed resume headline")
        doc.set_metadata({"producer": "Canva", "creator": "Canva"})

    designed = detect_layout(write_pdf(tmp_path / "canva.pdf", draw_canva))
    assert designed["designed_tool"] is True
    assert designed["layout_type"] == "designed"
    assert designed["recommended_mode"] == "editable"
    assert designed["confidence"] == 0.92
    assert designed["complex_layout"] is True
    assert "Canva" in designed["reason"]

    def draw_figma(doc):
        add_page(doc, "Figma frame")
        doc.set_metadata({"producer": "Figma", "creator": ""})

    assert detect_layout(write_pdf(tmp_path / "figma.pdf", draw_figma))["layout_type"] == "designed"

    def draw_word(doc):
        add_page(doc, "Plain producer")
        doc.set_metadata({"producer": "Microsoft Word", "creator": "Word"})

    plain = detect_layout(write_pdf(tmp_path / "word.pdf", draw_word))
    assert plain["designed_tool"] is False
    assert plain["layout_type"] == "simple"

    def draw_art(doc):
        page = add_page(doc, "Has drawings and some text content here")
        for i in range(16):
            page.draw_rect(fitz.Rect(10 + i, 10, 40 + i, 50))

    complex_info = detect_layout(write_pdf(tmp_path / "art.pdf", draw_art))
    assert complex_info["layout_type"] == "complex"
    assert complex_info["recommended_mode"] == "editable"
    assert complex_info["drawings"] >= 15
    assert "多欄" in complex_info["reason"]

    def draw_mixed(doc):
        page = doc.new_page()
        page.insert_image(page.rect, filename=str(image))
        add_page(doc, "hello")

    mixed = detect_layout(write_pdf(tmp_path / "mixed.pdf", draw_mixed))
    assert mixed["mixed_pages"] is True
    assert mixed["is_scanned"] is False
    assert mixed["recommended_mode"] == "hybrid"
    assert mixed["confidence"] == 0.7

    def draw_complex_mix(doc):
        page = add_page(doc, "complex page with enough characters to count")
        for i in range(16):
            page.draw_line((i, 0), (i, 30))
        add_page(doc, "simple sibling")

    complex_mix = detect_layout(write_pdf(tmp_path / "cmix.pdf", draw_complex_mix))
    assert complex_mix["layout_type"] == "complex"
    assert complex_mix["mixed_pages"] is True
    assert complex_mix["recommended_mode"] == "hybrid"
    assert complex_mix["confidence"] == 0.7


def test_detect_layout_empty_document_and_missing_metadata(monkeypatch, tmp_path):
    holder = {}

    def fake_open(src):
        holder["doc"] = FakeDoc([], metadata=None)
        return holder["doc"]

    monkeypatch.setattr("app.converters.layout_detect.fitz.open", fake_open)
    info = detect_layout(tmp_path / "empty.pdf")
    assert holder["doc"].closed is True
    assert info["pages"] == 0
    assert info["columns_estimate"] == 1
    assert info["layout_type"] == "simple"
    assert info["recommended_mode"] == "editable"
    assert info["is_scanned"] is False
    assert info["confidence"] == 0.65
    assert info["producer"] == ""
    assert info["creator"] == ""
    assert info["pages_detail"] == []


def test_design_tool_names_are_recognized(monkeypatch, tmp_path):
    for tool in DESIGN_TOOLS:
        doc = FakeDoc(
            [FakePage(text="hello world", blocks=[_block(1)])],
            metadata={"producer": tool.upper(), "creator": None},
        )
        monkeypatch.setattr(
            "app.converters.layout_detect.fitz.open", lambda src, doc=doc: doc
        )
        info = detect_layout(tmp_path / f"{tool}.pdf")
        assert info["designed_tool"] is True
        assert info["layout_type"] == "designed"
