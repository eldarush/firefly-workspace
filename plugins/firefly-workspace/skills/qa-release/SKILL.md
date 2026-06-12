---
description: Use for QAAS, test generation, flaky test triage, experiment design, release qualification, or evidence packets.
---

Run the Firefly QA/release workflow for $ARGUMENTS.

## Workflow

1. Identify change risk and impacted components.
2. Build a risk-based test matrix:
   - unit;
   - regression;
   - integration;
   - contract;
   - property;
   - security;
   - release lane.
3. Select runner labels, shards, retries, seed capture, artifact capture, and expected duration.
4. For flakes, distinguish product failure, test defect, environment drift, race, timeout, and data issue.
5. Build release evidence: commit, runner image digest, tool versions, model/prompt/skill version, test selection inputs, skipped tests, SBOM/provenance, approvals.
6. Make a gate recommendation.

## Rules

- Retries are evidence, not proof.
- Quarantine requires owner, reason, expiry, and release risk.
- Missing evidence must be explicit.

## Output

Return:

- `Risk profile`
- `Test matrix`
- `QAAS plan`
- `Flake analysis`
- `Evidence packet`
- `Gate recommendation`
