---
description: Use before claiming work is complete, after tests fail, after tool failures, or when deciding whether a result is actually shippable.
---

Verify and reflect on $ARGUMENTS.

## Workflow

1. List the claims being made.
2. Map each claim to evidence.
3. Run or inspect the smallest relevant verification commands.
4. Classify each check:
   - passed;
   - failed;
   - skipped with reason;
   - unavailable;
   - not run.
5. If a check fails, summarize the failure and choose the smallest next diagnostic step.
6. Create retrospective proposals only for repeatable workflow improvements, not for one-off noise.

## Evidence Hierarchy

Prefer deterministic evidence:

1. tests and CI;
2. type/lint/static analysis;
3. rendered manifests, dry runs, diffs;
4. QAAS evidence packets;
5. logs/metrics/traces;
6. manual reasoning.

## Output

Return:

- `Verdict`
- `Claim-to-evidence table`
- `Commands run`
- `Failed checks`
- `Not run`
- `Next repair step`
- `Improvement proposal`
