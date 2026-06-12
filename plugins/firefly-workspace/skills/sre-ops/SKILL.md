---
description: Use for SRE, Kubernetes, Helm, Argo CD, Kargo, GitLab CI, Grafana, operator, incident, or runbook work.
---

Run the Firefly SRE/Ops workflow for $ARGUMENTS.

## Workflow

1. Classify mode:
   - read-only diagnosis;
   - MR-only remediation;
   - approval-required operation;
   - break-glass incident.
2. Collect context: service, owner, cluster, namespace, workload, Argo app, Kargo stage, GitLab pipeline, dashboards, alerts, runbooks, recent changes, Firefly asset/guardrail state.
3. Build a hypothesis tree with confidence.
4. Prefer safe evidence: status, events, logs, metrics, rendered manifests, diffs, dry runs, offline docs.
5. Propose remediation through Git/MR when possible.
6. Include rollback and blast radius.

## Safety

- Read-only by default.
- Do not restart, delete, sync, promote, apply, or mutate live systems without explicit approval and policy allowance.
- Do not request secrets.

## Output

Return:

- `Mode`
- `Context brief`
- `Evidence`
- `Hypotheses`
- `Blast radius`
- `Safe next checks`
- `Remediation plan`
- `Rollback`
