# P3: Context Budgeting for 128k Agents (internal, 2025)

## Abstract
How should a 128k-context agent split its budget between retrieved docs,
working memory, and instructions?

## Key findings
- Retrieval beyond 12 chunks per query yields negative marginal utility:
  answer quality drops as distractor chunks crowd the context.
- A fixed 20% ceiling on retrieved content per turn outperformed dynamic
  schemes on 3 of 4 internal benchmarks.
- Chunk size for code: 40-line chunks beat function-level chunks on our
  retrieval-augmented bugfix benchmark by +5% pass@1, CONTRA P1's
  function-level recommendation, but we did not control for staleness.

## Recommendation
Budget: instructions <= 15%, retrieved <= 20%, the rest for working state.
Re-retrieve rather than carry stale chunks across turns.
