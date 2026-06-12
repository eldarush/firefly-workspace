---
name: critical-decision
description: Use when a choice affects architecture, public APIs, data schemas, security, production systems, or anything expensive to reverse.
---
# Critical Decision

## Decision Classes

| Class | Examples | Protocol |
|---|---|---|
| Reversible-cheap | Variable name, log format, internal refactor | Decide; note it in code comment or commit message |
| Reversible-expensive | Library swap, DB index, config schema | Decide with written rationale; record in ADR |
| Irreversible | Data deletion, published API, security boundary, prod migration | ALWAYS the human's decision. Present options. |

**NEVER decide an irreversible question by default, silence, or by burying it inside an implementation step.**

## One-Way-Door Checklist

If ANY of these is YES, this is an irreversible decision:

- [ ] Data deleted or irreversibly transformed?
- [ ] API published to external consumers?
- [ ] Security boundary moved or removed?
- [ ] Migration cannot be rolled back without data loss?
- [ ] Production system touched directly?
- [ ] Secret or credential rotated/revoked?
- [ ] Third-party dependency version locked in a shared artifact?

## How to Present a Decision to the Human

Frame as: question + options + tradeoffs + recommendation + what would change your recommendation.

```
Decision needed: <one sentence question>

Option A: <name>
  - Benefit: ...
  - Cost/risk: ...

Option B: <name>
  - Benefit: ...
  - Cost/risk: ...

Recommendation: Option A because <one concrete reason>.
I would change this to Option B if: <condition>.

Please confirm before I proceed.
```

## Rules

- NEVER bury a real decision inside an implementation step. Surface it explicitly.
- NEVER decide an irreversible question; always present to the human.
- MUST wait for human confirmation before executing irreversible changes.
- Record outcomes for reversible-expensive and irreversible decisions using `adr-authoring`.
- If unsure which class: treat as irreversible.

## Signals That a Hidden Decision Exists

- The plan says "update the schema" without specifying the migration strategy.
- The plan says "remove the legacy endpoint" without confirming consumers.
- You are about to `kubectl delete`, `DROP TABLE`, or `terraform destroy` anything.
- A config key is being renamed (old key may be in config files you haven't seen).
