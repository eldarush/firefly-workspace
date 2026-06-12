# Runbook: {title}

> Audience: on-call engineer at 03:00. No prior context assumed.

## Symptom
What you observe (alerts, dashboards, user reports).

## Impact
Who/what is affected; severity guidance.

## Preconditions / access
Tools, kubeconfig contexts, permissions needed.

## Diagnosis (read-only, in order)
1. `command` - what a healthy vs unhealthy result looks like
2. ...

## Decision tree
- If X -> section A
- If Y -> section B
- Anything else -> escalate (see below)

## Remediation A: {name}
> Mutating steps - get incident-commander ack first.
1. `command` - expected result, rollback if wrong: `command`

## Verification
How to prove the system is healthy again.

## Escalation
Who to page, with what information.

## History
| Date | Incident | Notes |
|------|----------|-------|
