---
description: Use when implementing code or configuration changes after the goal, scope, and acceptance criteria are clear.
---

Run the Firefly implementation loop for $ARGUMENTS.

## Workflow

1. Confirm scope, files, and acceptance criteria.
2. Write or identify the failing test, policy check, render check, or reproducible command first when feasible.
3. Make the smallest coherent change.
4. Run focused verification.
5. Repair based on evidence, not guesswork.
6. Stop after the smallest useful green increment.
7. Request broader verification only when the touched surface justifies it.

## Constraints

- Do not change unrelated files.
- Do not rewrite large areas to satisfy style preferences.
- Do not widen tool permissions.
- Do not push, deploy, apply, sync, or promote unless the user explicitly asks and policy allows it.

## Output

Return:

- `Scope`
- `Files changed`
- `Behavior changed`
- `Verification`
- `Failures and repairs`
- `Not run`
- `Residual risk`
