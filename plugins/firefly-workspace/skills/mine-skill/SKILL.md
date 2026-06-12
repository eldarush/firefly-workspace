---
description: Use when a conversation, prompt, troubleshooting path, review checklist, or release workflow should become a reusable Firefly skill, agent, hook, memory, or eval.
---

Mine a reusable workflow from $ARGUMENTS.

## Workflow

1. Identify the repeated job-to-be-done.
2. Determine the smallest durable artifact:
   - `.firefly/context.md` for project facts;
   - approved memory for durable preference;
   - skill for reusable multi-step workflow;
   - agent for repeated role/tool boundary;
   - hook for deterministic lifecycle control;
   - eval for regression prevention;
   - policy entry for risky commands/tools.
3. Extract trigger conditions and anti-triggers.
4. Extract required inputs, steps, tools, validation, examples, and failure modes.
5. Propose a draft artifact.
6. Define replay/eval cases from real source sessions.
7. Mark as proposal until reviewed by a human owner.

## Promotion Rules

- No generated skill becomes default behavior without review.
- No prompt or policy change ships without eval evidence.
- Every proposal needs owner, source, version, and rollback path.

## Output

Return:

- `Opportunity`
- `Recommended artifact`
- `Draft content`
- `Validation plan`
- `Owner/review cadence`
- `Approval needed`
