---
name: runbook-authoring
description: Use when writing or updating operational runbooks for services, alerts, or incident procedures.
---
# Runbook Authoring

**Audience: on-call engineer at 03:00 with zero context and elevated cortisol. Every sentence must earn its place.**

Template: `${CLAUDE_PLUGIN_ROOT}/assets/templates/runbook.md`

## Required Sections

1. **Symptom** - what you SEE: alert name(s), metric name(s), error messages verbatim. Not what it means.
2. **Impact** - who is affected, how badly, SLA implication.
3. **Preconditions** - access/tools required before starting (VPN, kubectl context, vault token).
4. **Diagnosis Steps** (READ-ONLY first, in order)
   - Each step: command (copy-pasteable) + expected healthy output + unhealthy output.
   - Order: cheapest/safest first.
5. **Decision Tree** - `if <diagnosis result A> -> go to section X; if B -> section Y; else -> escalate`.
6. **Remediation** - mutating steps. Each mutating step MUST have:
   - The command.
   - Required approval (none / team-lead / on-call manager).
   - Rollback command immediately below it.
7. **Verification of Recovery** - commands that confirm the system is healthy again.
8. **Escalation** - who, how, what information to include in the page.
9. **History** - table: date | incident | what changed.

## Diagnosis Step Template

```markdown
### D3. Check pod restart count
Command: `kubectl get pods -n <NAMESPACE> -l app=<APP>`
Healthy: all pods Running, RESTARTS < 5
Unhealthy: CrashLoopBackOff, or RESTARTS > 20 in past hour -> proceed to D4
```

## Remediation Step Template

```markdown
### R2. Restart the deployment
Approval: none required
Command: `kubectl rollout restart deployment/<DEPLOY> -n <NAMESPACE>`
Rollback: `kubectl rollout undo deployment/<DEPLOY> -n <NAMESPACE>`
Verify: `kubectl rollout status deployment/<DEPLOY> -n <NAMESPACE>`
```

## Rules

- EVERY command MUST be copy-pasteable with documented placeholders (`<NAMESPACE>`, `<APP>`).
- NEVER write a mutating command without its rollback immediately below it.
- MUST test the diagnosis path against a real or staging system before publishing.
- MUST include the review date in the document header.
- READ-ONLY steps MUST precede mutating steps in every section.
- If a step requires approval, name the approver role explicitly.
