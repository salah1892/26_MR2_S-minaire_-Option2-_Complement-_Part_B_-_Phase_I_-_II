from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    source_path: str
    page: int
    chunk_id: str
    text: str


def chunk_text(
    *,
    doc_id: str,
    source_path: str,
    page: int,
    text: str,
    max_words: int = 220,
    overlap_words: int = 40,
) -> list[Chunk]:
    # Simple word-based chunking that behaves deterministically and is easy to explain.
    words = text.split()
    if not words:
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words).strip()
        if chunk_text:
            chunks.append(
                Chunk(
                    doc_id=doc_id,
                    source_path=source_path,
                    page=page,
                    chunk_id=f"p{page}-c{idx}",
                    text=chunk_text,
                )
            )
        if end >= len(words):
            break
        start = max(0, end - overlap_words)
        idx += 1

    return chunks
