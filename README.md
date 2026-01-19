# Agentic RAG (local-first) — Tunisian Heritage (MR2)

This workspace contains a **minimal, coherent implementation** of the “Agentic RAG System for Tunisian Heritage” requested in Part B.

## What you must deliver (Part B, explained)

Phase 1 (in class):
- Architecture diagram (global blocks + one sub-block decomposition)
- Workflows (ingestion + query/agent) + one subworkflow with branches
- Agent decision pseudocode + explicit evaluation hook points

Phase 2 (optional, out of class):
- Implement ingestion + query workflows in an orchestration style
- Provide execution evidence (logs, screenshots) + at least 3 example queries
- Provide an evaluation mini-report

This repo focuses on **Phase 2 implementation**, while also providing Phase 1-style artifacts in [docs/phase1_design.md](docs/phase1_design.md).

## Run

Use the already configured venv python:
- `".venv\Scripts\python.exe" -m heritage_assistant.cli ingest`
- `".venv\Scripts\python.exe" -m heritage_assistant.cli ask "Donne-moi un exemple de rituel tunisien."`
- `".venv\Scripts\python.exe" -m heritage_assistant.cli demo`

Outputs:
- Local index: `data/index/`
- Logs: `logs/agent_log.jsonl`
- Demo results: `reports/demo_outputs.json`

## Sovereignty constraints (how this implementation respects them)

- **Local storage**: chunks + vector index stored under `data/`.
- **No foreign calls**: no API calls are made (translation is mocked offline for demo).
- **Extensible**: you can later swap `generate_answer()` with a local LLM (Ollama / llama.cpp / etc.).
