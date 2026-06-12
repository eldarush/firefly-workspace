---
name: brainstorming
description: Use when requirements are fuzzy, multiple designs are possible, or the user asks to explore ideas before committing to an approach.
---
# Brainstorming

## Protocol

1. **Clarify before diverging.** Answer the unlock questions (see below) with the human FIRST. Fuzzy input produces worthless options.
2. **Diverge: generate 3+ options.** One sentence name + steelman (2-3 sentences of the strongest case FOR it). NEVER evaluate while generating - label this phase "DIVERGE" explicitly.
3. **Agree on evaluation criteria.** With the human. Typical: correctness, simplicity, blast radius, maintenance cost, reversibility. Weight them together.
4. **Converge: score each option.** Decision matrix (option x criterion, 1-5). Show totals. Give your recommendation with one-sentence rationale.
5. **Human picks.** You present; the human decides. Do not default.
6. **Record.** Decision + runner-up + rejected options -> feed `adr-authoring` skill for durable capture.

## Questions That Unlock Fuzzy Requirements

- Who consumes this output? (human / service / both?)
- What breaks if this does not exist?
- What is the cheapest experiment that would tell us if the approach works?
- What does success look like in 6 months?
- What is explicitly out of scope?
- Is this reversible if we pick wrong?

## Decision Matrix Template

| Option | Correctness | Simplicity | Blast Radius | Maintenance | Total |
|--------|-------------|------------|--------------|-------------|-------|
| A      |             |            |              |             |       |
| B      |             |            |              |             |       |
| C      |             |            |              |             |       |

Score 1 (bad) to 5 (good). Agree weights before filling.

## Anti-Patterns

| Anti-Pattern | Symptom | Correction |
|---|---|---|
| Anchoring | First idea shapes all others | Generate options independently; name them before describing |
| Strawmen | Two options are real; one is absurd filler | Every option MUST have a genuine steelman |
| Evaluating while generating | "Option A is better because..." during DIVERGE phase | Hard stop: finish all options before any evaluation |
| Skipping criteria agreement | AI picks criteria post-hoc to justify preference | Write criteria + weights with human before scoring |
| No record | Decision made verbally, lost on /clear | Always write decision + rejects to ADR or handoff |

## Rules

- MUST generate >= 3 options before evaluating any.
- MUST steelman each option honestly; if you cannot steelman it, it is not a real option.
- NEVER present a recommendation without a decision matrix.
- The human picks; you recommend.
- Rejected options MUST be recorded with the reason they lost - they are the document's value.
