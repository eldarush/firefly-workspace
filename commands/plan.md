---
description: Plan a non-trivial task with the human as architect - interview, options, approval gate
argument-hint: "<task description>"
disable-model-invocation: true
---

Plan this task with the user as the architect: $ARGUMENTS

Hard rule: NO code edits during planning. This command produces an approved
plan, nothing else.

1. **Frame**: restate the task in one sentence. List your assumptions about
   intent, scope, and constraints. If the task is trivial (single file, obvious
   change), say so and suggest skipping to direct implementation.

2. **Scout**: if the relevant code area is unfamiliar, delegate a `scout`
   subagent to map it (repo shape, relevant files, conventions, verifier).
   Otherwise read the key files yourself - never plan against imagined code.

3. **Interview the architect** - one question at a time, never a wall of
   questions. Ask ONLY decisions that belong to a human: API shape, ownership,
   tradeoffs (speed vs completeness, compat vs cleanliness), rollout strategy,
   risk tolerance. For each, offer 2-3 concrete options with your
   recommendation marked. Skip questions the codebase already answers.

4. **Draft**: delegate the `planner` subagent with everything learned (task,
   answers, scout brief) to produce the structured plan, or draft it yourself
   for medium tasks using `${CLAUDE_PLUGIN_ROOT}/assets/templates/plan.md`.

5. **Challenge**: before presenting, attack your own plan: what breaks first?
   which step is least certain? what would a hostile reviewer flag? Adjust.

6. **Approval gate**: present the plan compactly. Ask explicitly:
   "Approve as-is, or change something?" Iterate until approved.

7. **Persist**: write the approved plan to `.firefly/plan.md` (status:
   APPROVED, date, the architect's decisions recorded verbatim). Then suggest
   `/ff:implement` to execute it.
