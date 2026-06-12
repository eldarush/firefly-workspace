---
name: adr-authoring
description: Use when an architecture decision was made and needs recording, or when evaluating whether a past decision should be superseded.
---
# ADR Authoring

**An ADR captures the WHY that survives personnel and context changes. The rejected options are the document's primary value.**

Template: `${CLAUDE_PLUGIN_ROOT}/assets/templates/adr.md`

## Required Sections

```markdown
# ADR-<NNN>: <Title - imperative phrase, e.g. "Use PostgreSQL for the job queue">

Status: proposed | accepted | superseded-by-ADR-<NNN>
Date: YYYY-MM-DD
Author: <name or role>

## Context
<3-6 sentences: the forces at play, the problem being solved, constraints that shaped the options.
Do NOT include the decision here.>

## Decision
We will <active voice, one sentence>.

## Options Considered

### Option A: <name>
Pros: ...
Cons: ...

### Option B: <name> (chosen)
Pros: ...
Cons: ...

### Option C: <name>
Pros: ...
Cons: ...

## Consequences
Positive: ...
Negative / debt accepted: ...

## Verification
How we will know this decision is working: <metric, test, or review trigger>
Revisit date or trigger: <date or condition>
```

## Rules

- One decision per ADR. Compound decisions -> two ADRs.
- Write within one day of deciding. Memory decays fast; the ADR is worthless if reconstructed a week later.
- NEVER edit an accepted ADR's decision text. To change the decision: write a new ADR with `supersedes: ADR-<NNN>` and update the old one's status to `superseded-by-ADR-<NNN>`.
- MUST include rejected options with honest pros/cons. An ADR with only the chosen option is incomplete.
- Link from the code or README where the decision manifests: `// See ADR-012` or `[why Postgres](docs/adr/012-postgres-job-queue.md)`.
- Feed from: `brainstorming` (the decision matrix), `best-of-n` (bake-off result), `critical-decision` (irreversible choices).

## File Naming

```
docs/adr/NNN-<slug>.md
# e.g. docs/adr/012-postgres-job-queue.md
```

Use three-digit zero-padded numbers. Slugs use hyphens, lowercase.
