# Evaluation and critical reflection (auto-generated)

This report summarizes recent test queries and the proxy metrics defined in the design.

| # | Query | Lang | TopScore | HallucinationRisk | ForeignToolsUsed |
|---:|---|:---:|---:|---:|---:|
| 1 | ما هو التراث اللامادي التونسي؟ | ar | 0.167 | 0.918 | 0 |
| 2 | Donne-moi un exemple de rituel tunisien. | fr | 0.122 | 0.913 | 0 |
| 3 | ما هو التراث اللامادي التونسي؟ | ar | 0.167 | 0.918 | 0 |
| 4 | Donne-moi un exemple de rituel tunisien. | fr | 0.122 | 0.913 | 0 |
| 5 | ما هو التراث اللامادي التونسي؟ | ar | 0.167 | 0.918 | 0 |

## Reflection (template)
- Strength: Local-first pipeline (PDF -> chunks -> local index) with explicit tool logging.
- Limitation: Answer generation is a minimal summarizer (replaceable by a local LLM).
- Improvement: Add a real local LLM + better ontology grounding and automatic faithfulness checks.
