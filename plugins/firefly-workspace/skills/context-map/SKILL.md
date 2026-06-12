---
description: Use when a task needs repository, service, test, CI, ownership, or deployment context before planning or editing.
---

Create a high-signal context map for $ARGUMENTS.

## Workflow

1. Inspect the repository with fast search first.
2. Identify project type, package manager, build/test commands, CI files, deployment manifests, Helm charts, operators, docs, runbooks, and ownership hints.
3. Find relevant symbols, modules, tests, and recent failure evidence.
4. Separate evidence into:
   - directly relevant;
   - possibly relevant;
   - stale or uncertain.
5. Keep context lean. Do not paste large files unless the next step requires them.
6. Recommend whether to proceed with local implementation, ask an architect decision, or run a deeper research pass.

## Output

Return:

- `Repo shape`
- `Relevant files`
- `Relevant tests and commands`
- `Deployment/operations surface`
- `Local conventions`
- `Missing context`
- `Recommended next action`
