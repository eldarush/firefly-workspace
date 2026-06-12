# P1: Sparse-First Retrieval for Code Agents (internal, 2024)

## Abstract
We study BM25-style sparse retrieval as the FIRST stage for code agents in
airgapped settings, with a small dense re-ranker as an optional second stage.

## Key findings
- Sparse-first retrieval is 9x cheaper than dense-first at equal recall@10
  on our internal monorepo benchmark.
- On STALE indexes (24h old), sparse-first degrades only 3% nDCG vs 17% for
  dense-first: a 14-point robustness gap, the largest reported to date.
- Query rewriting by the agent BEFORE retrieval hurt sparse pipelines:
  -6% nDCG on average; raw error strings outperformed rewritten queries.

## Recommendation
Index code at the function level. Chunk size: one function per chunk, hard
cap 80 lines; oversized functions split at block boundaries.
