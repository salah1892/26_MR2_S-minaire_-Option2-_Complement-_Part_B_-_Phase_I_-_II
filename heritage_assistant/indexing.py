from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class IndexPaths:
    chunks_jsonl: Path
    vectorizer_joblib: Path
    matrix_joblib: Path


def get_index_paths(index_dir: Path) -> IndexPaths:
    return IndexPaths(
        chunks_jsonl=index_dir / "chunks.jsonl",
        vectorizer_joblib=index_dir / "tfidf_vectorizer.joblib",
        matrix_joblib=index_dir / "tfidf_matrix.joblib",
    )


def build_tfidf_index(*, chunks_jsonl: Path, vectorizer_out: Path, matrix_out: Path) -> None:
    texts: list[str] = []
    with chunks_jsonl.open("r", encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            texts.append(rec["text"])

    # Character n-grams: robust across French/Arabic/English tokens and noisy PDFs.
    # (Works well for a minimal, offline-first exam implementation.)
    vectorizer = TfidfVectorizer(
        lowercase=True,
        strip_accents="unicode",
        analyzer="char_wb",
        ngram_range=(3, 5),
        max_features=80000,
    )

    matrix = vectorizer.fit_transform(texts)
    vectorizer_out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(vectorizer, vectorizer_out)
    joblib.dump(matrix, matrix_out)


def load_index(vectorizer_path: Path, matrix_path: Path):
    vectorizer = joblib.load(vectorizer_path)
    matrix = joblib.load(matrix_path)
    return vectorizer, matrix


def top_k(
    *,
    query: str,
    vectorizer: TfidfVectorizer,
    matrix,
    k: int = 5,
) -> tuple[list[int], list[float]]:
    qv = vectorizer.transform([query])
    sims = cosine_similarity(qv, matrix).ravel()
    if k <= 0:
        return [], []
    idx = sims.argsort()[::-1][:k]
    return idx.tolist(), sims[idx].tolist()
