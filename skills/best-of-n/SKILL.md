---
name: best-of-n
description: Use when a problem has 2-3 plausibly different approaches and arguing abstractly is slower than implementing and comparing them.
---
# Best-of-N

**Weak models gain disproportionately from best-of-N: generation is cheap; judging is easier than generating from scratch.**

## When to Use

- 2-3 genuinely different approaches exist (not cosmetically different).
- A cheap shared acceptance test can filter failures deterministically.
- Arguing abstractly about which approach is better would take longer than trying.

## When NOT to Use

- Only one reasonable approach exists.
- Candidates differ only in formatting or naming.
- No cheap acceptance test exists (judging broken code with LLM is wasteful).
- N > 3 (cost explodes; diminishing returns).

## Protocol

1. **Define the bake-off with the human.** Agree on:
   - Task (1-2 sentences, same for all candidates).
   - Named approaches (e.g., A: event-driven, B: polling, C: streaming).
   - ONE shared acceptance test (command + expected output/exit code).
   - Ranked judging criteria (e.g., simplicity > performance > lines of code).

2. **Isolate candidates.**
   ```bash
   git worktree add ../candidate-a -b bake/candidate-a
   git worktree add ../candidate-b -b bake/candidate-b
   ```

3. **Generate in parallel.** One subagent per approach, same task description, no cross-talk between agents.

4. **Deterministic filter first.** Run the acceptance test on each candidate.
   - Fails acceptance test -> ELIMINATED. No LLM judging of broken code.
   - Passes -> proceeds to judging.

5. **Judge survivors with a clean-context evaluator.** Anonymize (A/B/C). Provide: spec + diff + acceptance test output. Ask evaluator to score each surviving criterion.

6. **Build the selection matrix.** Share with human.

   | Criterion | Weight | Candidate A | Candidate B |
   |---|---|---|---|
   | Simplicity | 3 | 4 | 3 |
   | Performance | 2 | 3 | 5 |
   | Weighted total | | 18 | 19 |

7. **Human picks.** Merge winner. Clean up worktrees.
   ```bash
   git worktree remove ../candidate-a
   git worktree remove ../candidate-b
   ```

## Rules

- MUST define the acceptance test BEFORE generating candidates.
- MUST eliminate failures deterministically before any LLM judging.
- NEVER let candidates influence each other during generation.
- MUST anonymize candidates when presenting to evaluator.
- Human makes the final pick; you present the matrix.
- Record the outcome in `.firefly/handoff.md` and feed `adr-authoring` for significant choices.
