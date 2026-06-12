---
description: Use when improving prompts, skills, agents, hooks, context files, or team Claude Code usage based on failures or repeated work.
---

Design a governed prompt or workflow upgrade for $ARGUMENTS.

## Workflow

1. Identify the behavior failure or opportunity.
2. Find root cause:
   - missing context;
   - vague prompt;
   - weak examples;
   - wrong workflow;
   - missing tool;
   - missing verification;
   - unsafe autonomy;
   - stale memory.
3. Propose the smallest improvement.
4. Write before/after examples.
5. Define eval cases that prove the improvement and catch regressions.
6. Require review before promotion.

## Anti-Corruption Rules

- Do not train or tune on unvetted assistant output.
- Quarantine synthetic examples.
- Keep provenance for every example.
- Prefer adding one clear instruction or example over expanding a long brittle prompt.

## Output

Return:

- `Failure`
- `Root cause`
- `Proposed change`
- `Before/after examples`
- `Eval cases`
- `Promotion gate`
- `Rollback`
