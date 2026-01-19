from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from .config import get_paths
from .indexing import get_index_paths, load_index, top_k


@dataclass(frozen=True)
class ToolUse:
    name: str
    details: dict


def detect_language(text: str) -> str:
    # Heuristic: Arabic if any Arabic Unicode block present.
    for ch in text:
        if "\u0600" <= ch <= "\u06FF" or "\u0750" <= ch <= "\u077F" or "\u08A0" <= ch <= "\u08FF":
            return "ar"
    return "fr"  # default for this exam context


def sovereignty_checks_ok() -> tuple[bool, str]:
    # Local-first: in this minimal implementation, we don't call any external services.
    return True, "local-only"


def should_refuse(query: str) -> tuple[bool, str]:
    q = query.lower()
    if any(x in q for x in ["mot de passe", "password", "pirater", "hack"]):
        return True, "security"
    return False, ""


def mock_translate_ar_to_fr(query_ar: str) -> tuple[str, bool]:
    # Minimal offline translation: only supports a few demo phrases.
    mapping = {
        "ما هو التراث اللامادي التونسي؟": "Qu'est-ce que le patrimoine immatériel tunisien ?",
        "اعطني مثال عن طقوس تونسية": "Donne-moi un exemple de rituel tunisien.",
    }
    return mapping.get(query_ar, query_ar), mapping.get(query_ar) is not None


def generate_answer(query: str, contexts: list[dict]) -> str:
    # Minimal "LLM-like" response: grounded summary using retrieved contexts.
    if not contexts:
        return (
            "Je ne trouve pas de passage pertinent dans la base locale. "
            "Peux-tu préciser (région, période, nom de rituel/chanson) ?"
        )

    lines = ["Réponse (basée sur la base locale):"]
    for i, c in enumerate(contexts, start=1):
        src = Path(c["source_path"]).name
        lines.append(f"- Contexte {i} ({src} p.{c['page']}): {c['text']}")

    lines.append("\nSynthèse: (à compléter par un modèle LLM local si disponible)")
    lines.append(
        "- Je me base sur les extraits ci-dessus; si tu veux une réponse plus détaillée, "
        "je peux reformuler et structurer davantage."
    )
    return "\n".join(lines)


def run_agent(query: str, *, k: int = 5) -> dict:
    paths = get_paths()
    idx_paths = get_index_paths(paths.index_dir)

    ok, reason = sovereignty_checks_ok()
    tool_uses: list[ToolUse] = [ToolUse(name="sovereignty_check", details={"ok": ok, "reason": reason})]
    if not ok:
        return {
            "answer": "Refus: contraintes de souveraineté.",
            "tool_uses": [t.__dict__ for t in tool_uses],
        }

    refuse, refuse_reason = should_refuse(query)
    if refuse:
        tool_uses.append(ToolUse(name="refuse", details={"reason": refuse_reason}))
        return {
            "answer": "Je ne peux pas aider pour cette demande. Pose une question sur le patrimoine immatériel tunisien.",
            "tool_uses": [t.__dict__ for t in tool_uses],
        }

    lang = detect_language(query)
    tool_uses.append(ToolUse(name="detect_language", details={"lang": lang}))

    normalized_query = query
    if lang == "ar":
        translated, did = mock_translate_ar_to_fr(query)
        tool_uses.append(ToolUse(name="translate", details={"from": "ar", "to": "fr", "applied": did}))
        normalized_query = translated

    vectorizer, matrix = load_index(idx_paths.vectorizer_joblib, idx_paths.matrix_joblib)
    ids, scores = top_k(query=normalized_query, vectorizer=vectorizer, matrix=matrix, k=k)
    tool_uses.append(ToolUse(name="retrieve", details={"k": k, "top_scores": scores[:3]}))

    contexts: list[dict] = []
    if ids:
        with idx_paths.chunks_jsonl.open("r", encoding="utf-8") as f:
            all_chunks = [json.loads(line) for line in f]
        for rank, (i, score) in enumerate(zip(ids, scores), start=1):
            rec = all_chunks[i]
            rec = {**rec, "score": float(score), "rank": rank}
            contexts.append(rec)

    answer = generate_answer(normalized_query, contexts)

    # Evaluation hooks (simple)
    hallucination_risk = float(1.0 - (sum(scores) / max(1, len(scores)))) if scores else 1.0
    eval_hooks = {
        "after_generate": {"hallucination_risk_proxy": hallucination_risk},
        "after_tool_selection": {"foreign_tools_used": 0},
    }

    payload = {
        "query": query,
        "normalized_query": normalized_query,
        "answer": answer,
        "tool_uses": [t.__dict__ for t in tool_uses],
        "eval": eval_hooks,
        "retrieved": contexts,
        "timestamp": time.time(),
    }

    paths.logs_dir.mkdir(parents=True, exist_ok=True)
    log_path = paths.logs_dir / "agent_log.jsonl"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return payload
