---
description: Use when a question benefits from multiple independent research tracks, design alternatives, or specialist analysis before making a decision.
---

Run Firefly deep research on $ARGUMENTS.

## Workflow

1. Define the research question and success criteria.
2. Split the work into independent tracks. Examples:
   - current implementation;
   - architecture alternatives;
   - security/governance;
   - SRE/operations;
   - QA/testing;
   - adoption/maintainability;
   - offline/airgap constraints;
   - prior art or internal docs.
3. Dispatch only truly independent tracks to subagents.
4. Require each subagent to return a concise memo with evidence, tradeoffs, and recommendation.
5. Aggregate the memos into a ranked decision matrix.
6. Call out where evidence is weak or missing.
7. End with a recommended plan and the decision that belongs to the human architect.

## Guardrails

- Do not duplicate research across agents.
- Do not ask agents to edit overlapping files.
- Treat internet results as unavailable unless the environment explicitly has approved access.
- Prefer internal docs and local evidence in airgapped sessions.

## Output

Return:

- `Research question`
- `Tracks`
- `Findings`
- `Ranked options`
- `Recommendation`
- `Open decisions`
- `Implementation plan seed`
