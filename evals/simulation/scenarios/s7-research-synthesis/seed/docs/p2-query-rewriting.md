# P2: Query Rewriting Helps Weak Models Retrieve (internal, 2025)

## Abstract
We evaluate LLM query rewriting ahead of retrieval for 7B-32B models
operating over internal documentation and code.

## Key findings
- For weak models, rewriting the user query into 2-3 keyword variants
  improved recall@5 by +11% on documentation corpora.
- Gains shrink with model size: +2% for the 32B model.
- CONTRA P1: we find query rewriting also helps code retrieval (+4% nDCG)
  when rewrites preserve identifier tokens verbatim; stripping identifiers
  is what hurts.

## Caveats
- Stale-index robustness was not the focus; we observed an 8% nDCG drop on
  24h-old dense indexes, partially mitigated (to 5%) by rewriting.

## Recommendation
Rewrite queries only when the base query has no code identifiers in it.
