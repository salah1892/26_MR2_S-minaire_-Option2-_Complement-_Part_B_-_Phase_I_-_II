from __future__ import annotations

import argparse
import pathlib
import re
from typing import Iterable

from pypdf import PdfReader


def _find_pages(reader: PdfReader, patterns: Iterable[str]) -> list[tuple[int, str]]:
    rx = re.compile("|".join(patterns), re.IGNORECASE)
    hits: list[tuple[int, str]] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        match = rx.search(text)
        if not match:
            continue

        start = max(match.start() - 200, 0)
        end = min(match.end() + 1200, len(text))
        snippet = " ".join(text[start:end].split())
        hits.append((page_index, snippet[:2000]))

    return hits


def _default_exam_pdf(cwd: pathlib.Path) -> pathlib.Path | None:
    candidates = sorted(cwd.glob("*Examen*.pdf"))
    return candidates[0] if candidates else None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Extract Part B text from an exam PDF")
    parser.add_argument("--pdf", type=str, default=None, help="Path to the exam PDF")
    parser.add_argument("--debug", action="store_true", help="Print per-page extraction previews")
    args = parser.parse_args(argv)

    cwd = pathlib.Path.cwd()
    pdf_path = pathlib.Path(args.pdf) if args.pdf else (_default_exam_pdf(cwd) or cwd / "Examen.pdf")
    if not pdf_path.exists():
        raise SystemExit(
            f"PDF not found: {pdf_path}. Provide --pdf <path-to-exam.pdf> or place the PDF in this folder."
        )

    reader = PdfReader(str(pdf_path))

    all_text_pages: list[str] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        all_text_pages.append(text)
        if args.debug:
            preview = " ".join(text[:500].split())
            print(f"[debug] page {page_index}: chars={len(text)} preview={preview!r}")

    all_text = "\n\n".join(
        f"\n--- page {i} ---\n\n{t}" for i, t in enumerate(all_text_pages, start=1)
    )
    (pdf_path.parent / "Examen_MR2_extracted.txt").write_text(all_text, encoding="utf-8")

    patterns = [
        r"part\s*b",
        r"partie\s*b",
        r"phase\s*1",
        r"phase\s*2",
    ]

    hits = _find_pages(reader, patterns)

    print(f"pages={len(reader.pages)} hits={len(hits)}")
    for page, snippet in hits:
        print(f"\n--- page {page} ---")
        print(snippet)

    # Try to isolate Part B section (best effort)
    joined = "\n\n".join(all_text_pages)
    m = re.search(r"Part\s*B\s*:\s*Total:.*?(?=Part\s*C\s*:|\Z)", joined, flags=re.IGNORECASE | re.DOTALL)
    if m:
        (pdf_path.parent / "Part_B_extracted.txt").write_text(m.group(0), encoding="utf-8")
        print("\n[info] Wrote Part_B_extracted.txt")
    else:
        # fallback: from first 'Part B' to end
        m2 = re.search(r"Part\s*B\s*:", joined, flags=re.IGNORECASE)
        if m2:
            (pdf_path.parent / "Part_B_extracted.txt").write_text(joined[m2.start():], encoding="utf-8")
            print("\n[info] Wrote Part_B_extracted.txt (fallback)")
        else:
            print("\n[warn] Could not isolate Part B")


if __name__ == "__main__":
    main()
