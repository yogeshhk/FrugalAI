"""Parse the curriculum PDF with Docling and keep the result on disk, so it is parsed once, not per question.

Writes parsed/curriculum.md (Markdown with tables), parsed/curriculum.json (the lossless Docling document) and
parsed/tables.json (every table as rows of cells with its page number).
"""

import json
import time
from pathlib import Path
from typing import List, Tuple

from . import config


def _pages(ranges: List[Tuple[int, int]]) -> List[int]:
    return [p for a, b in ranges for p in range(a, b + 1)]


def ensure_models(folder: Path = config.ROOT / "models" / "docling", log=print) -> Path:
    """Download Docling's layout and table models into a project folder.

    On Windows without symlink rights, Docling's default download into the Hugging Face cache fails with
    WinError 1314. A folder download needs no symlinks. The folder is git-ignored.
    """
    from docling.utils.model_downloader import download_models

    marker = folder / ".complete"
    if not marker.exists():
        log(f"downloading Docling models into {folder} (one time) ...")
        download_models(output_dir=folder, progress=False, with_layout=True, with_tableformer=True,
                        with_code_formula=False, with_picture_classifier=False, with_easyocr=False)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("ok", encoding="utf-8")
    return folder


def convert_pages(pdf: Path, pages: List[int], accurate_tables: bool = True):
    """Docling conversion of selected pages. OCR is off: this PDF has a text layer."""
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions(artifacts_path=str(ensure_models()))
    opts.do_ocr = False
    opts.do_table_structure = True
    opts.table_structure_options.mode = TableFormerMode.ACCURATE if accurate_tables else TableFormerMode.FAST
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    lo, hi = min(pages), max(pages)
    result = conv.convert(str(pdf), page_range=(lo, hi))
    return result.document


def table_records(doc, keep_pages: List[int]) -> List[dict]:
    """Every table as a grid of cell texts, with page number and the spans Docling found."""
    out = []
    for t in doc.tables:
        page = t.prov[0].page_no if t.prov else None
        if page not in keep_pages:
            continue
        cells = [{"r0": c.start_row_offset_idx, "r1": c.end_row_offset_idx, "c0": c.start_col_offset_idx,
                  "c1": c.end_col_offset_idx, "text": c.text, "header": bool(c.column_header or c.row_header)}
                 for c in t.data.table_cells]
        out.append({"page": page, "rows": t.data.num_rows, "cols": t.data.num_cols, "cells": cells,
                    "markdown": t.export_to_markdown(doc)})
    return out


def parse(pdf: Path = config.PDF, ranges=config.PAGES, out_dir: Path = config.PARSED, log=print) -> dict:
    pages = _pages(ranges)
    t0 = time.perf_counter()
    doc = convert_pages(pdf, pages)
    seconds = time.perf_counter() - t0
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "curriculum.md").write_text(doc.export_to_markdown(), encoding="utf-8")
    (out_dir / "curriculum.json").write_text(json.dumps(doc.export_to_dict()), encoding="utf-8")
    tables = table_records(doc, pages)
    (out_dir / "tables.json").write_text(json.dumps(tables, indent=1), encoding="utf-8")
    info = {"pages_requested": pages, "seconds": round(seconds, 1), "tables": len(tables),
            "table_pages": [t["page"] for t in tables]}
    (out_dir / "parse_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    log(f"parsed {len(pages)} pages in {seconds:.0f} s; {len(tables)} tables on pages {info['table_pages']}")
    return info
