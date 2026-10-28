"""Small generated fixtures shared by unit tests."""

from __future__ import annotations

from pathlib import Path

import fitz
from PIL import Image


def write_pdf(path: Path, populate) -> Path:
    doc = fitz.open()
    populate(doc)
    if doc.page_count == 0:
        doc.new_page()
    doc.save(str(path))
    doc.close()
    return path


def add_page(doc: fitz.Document, text: str | None = None, **insert_kwargs) -> fitz.Page:
    page = doc.new_page()
    if text is not None:
        page.insert_text((72, 72), text, **insert_kwargs)
    return page


def solid_image(
    path: Path,
    size: tuple[int, int] = (32, 32),
    color: tuple[int, ...] = (255, 0, 0),
    mode: str = "RGB",
) -> Path:
    if mode == "P":
        image = Image.new("P", size)
        image.putpalette([0, 0, 0] * 256)
        image.save(path)
    else:
        Image.new(mode, size, color).save(path)
    return path
