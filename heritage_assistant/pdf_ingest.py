from __future__ import annotations

import json
import shutil
from pathlib import Path

from pypdf import PdfReader

from .chunking import Chunk, chunk_text
from .config import get_paths


def _ensure_raw_pdfs() -> list[Path]:
    paths = get_paths()
    paths.raw_dir.mkdir(parents=True, exist_ok=True)

    # Copy any PDFs sitting in the project root into data/raw/.
    root_pdfs = list(paths.root.glob("*.pdf"))
    for pdf in root_pdfs:
        dest = paths.raw_dir / pdf.name
        if not dest.exists():
            shutil.copy2(pdf, dest)

    return sorted(paths.raw_dir.glob("*.pdf"))


def extract_chunks_from_pdfs() -> list[Chunk]:
    paths = get_paths()
    pdf_paths = _ensure_raw_pdfs()
    chunks: list[Chunk] = []

    for pdf_path in pdf_paths:
        reader = PdfReader(str(pdf_path))
        doc_id = pdf_path.stem
        try:
            source_path = str(pdf_path.relative_to(paths.root))
        except ValueError:
            source_path = str(pdf_path)
        for page_index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if not text:
                continue
            chunks.extend(
                chunk_text(
                    doc_id=doc_id,
                    source_path=source_path,
                    page=page_index,
                    text=text,
                )
            )

    return chunks


def write_chunks_jsonl(chunks: list[Chunk], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(
                json.dumps(
                    {
                        "doc_id": c.doc_id,
                        "source_path": c.source_path,
                        "page": c.page,
                        "chunk_id": c.chunk_id,
                        "text": c.text,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
