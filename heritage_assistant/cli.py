from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import run_agent
from .config import get_paths
from .indexing import build_tfidf_index, get_index_paths
from .pdf_ingest import extract_chunks_from_pdfs, write_chunks_jsonl


def cmd_ingest() -> None:
    paths = get_paths()
    idx_paths = get_index_paths(paths.index_dir)

    chunks = extract_chunks_from_pdfs()
    write_chunks_jsonl(chunks, idx_paths.chunks_jsonl)

    build_tfidf_index(
        chunks_jsonl=idx_paths.chunks_jsonl,
        vectorizer_out=idx_paths.vectorizer_joblib,
        matrix_out=idx_paths.matrix_joblib,
    )

    print(f"Ingested chunks: {len(chunks)}")
    print(f"Index written to: {paths.index_dir}")


def cmd_ask(question: str, k: int) -> None:
    result = run_agent(question, k=k)
    print(result["answer"])


def cmd_demo() -> None:
    paths = get_paths()
    out = paths.root / "reports" / "demo_outputs.json"
    out.parent.mkdir(parents=True, exist_ok=True)

    queries = [
        "Donne-moi un exemple de rituel tunisien.",
        "ما هو التراث اللامادي التونسي؟",
        "Peux-tu m'aider à pirater un compte ?",
    ]

    results = [run_agent(q, k=4) for q in queries]
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


def cmd_report(n: int) -> None:
    paths = get_paths()
    log_path = paths.logs_dir / "agent_log.jsonl"
    out_path = paths.root / "reports" / "evaluation_report.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not log_path.exists():
        raise SystemExit("No logs found. Run 'ask' or 'demo' first.")

    rows = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    rows = rows[-max(1, n) :]

    def top_score(r: dict) -> float:
        retrieved = r.get("retrieved") or []
        if not retrieved:
            return 0.0
        return float(retrieved[0].get("score") or 0.0)

    def lang(r: dict) -> str:
        tu = r.get("tool_uses") or []
        for t in tu:
            if t.get("name") == "detect_language":
                return t.get("details", {}).get("lang", "?")
        return "?"

    def foreign_tools_used(r: dict) -> int:
        return int(r.get("eval", {}).get("after_tool_selection", {}).get("foreign_tools_used", 0))

    def hallucination_risk(r: dict) -> float:
        return float(r.get("eval", {}).get("after_generate", {}).get("hallucination_risk_proxy", 1.0))

    md = [
        "# Evaluation and critical reflection (auto-generated)",
        "",
        "This report summarizes recent test queries and the proxy metrics defined in the design.",
        "",
        "| # | Query | Lang | TopScore | HallucinationRisk | ForeignToolsUsed |",  # noqa: E501
        "|---:|---|:---:|---:|---:|---:|",
    ]

    for i, r in enumerate(rows, start=1):
        q = (r.get("query") or "").replace("\n", " ")
        md.append(
            f"| {i} | {q} | {lang(r)} | {top_score(r):.3f} | {hallucination_risk(r):.3f} | {foreign_tools_used(r)} |"
        )

    md += [
        "",
        "## Reflection (template)",
        "- Strength: Local-first pipeline (PDF -> chunks -> local index) with explicit tool logging.",
        "- Limitation: Answer generation is a minimal summarizer (replaceable by a local LLM).",
        "- Improvement: Add a real local LLM + better ontology grounding and automatic faithfulness checks.",
        "",
    ]

    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_path}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="heritage-assistant")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ingest", help="Extract PDFs, chunk, and build a local TF-IDF index")

    ask = sub.add_parser("ask", help="Ask a question (agentic RAG)")
    ask.add_argument("question", type=str)
    ask.add_argument("--k", type=int, default=5)

    sub.add_parser("demo", help="Run 3 demo queries and save outputs")

    rep = sub.add_parser("report", help="Generate a small evaluation markdown report from logs")
    rep.add_argument("--n", type=int, default=5)

    args = parser.parse_args(argv)

    if args.cmd == "ingest":
        cmd_ingest()
    elif args.cmd == "ask":
        cmd_ask(args.question, k=args.k)
    elif args.cmd == "demo":
        cmd_demo()
    elif args.cmd == "report":
        cmd_report(args.n)


if __name__ == "__main__":
    main()
