---
name: handoff-and-clear
description: Use when context grows stale, before /clear, at day end, or when handing work to another person or session.
---
# Handoff and Clear

**Long contexts rot: stale assumptions accumulate, instructions get drowned, the model drifts. The cure is handoff + reset.**

## When to Trigger

- Responses feel sluggish or off-track.
- You have re-explained the same constraint twice.
- A major milestone just completed.
- Before any long risky operation (pre-checkpoint).
- Day end / shift change.
- Before `/clear` or a compaction event.

In Firefly: `/ff:handoff` automates this.

## What a Good Handoff Contains (<= 600 tokens)

Reconstruct from the SYSTEM (git, files, test output), not from memory.

```markdown
## Handoff: <short label> - <date>

### Goal
<one sentence>

### Progress
Done:
- [ ] step 1: <description> (commit: <sha>)
- [x] step 2: <description>

Not done:
- [ ] step 3: <description>

### Ground Truth (from system, not memory)
```
git status
git log --oneline -5
git diff --stat HEAD~1
<last verifier output>
```

### Decisions Made
- Chose X over Y because <reason> (see ADR-NNN if applicable)

### Traps Found
- <filename>:<line> does X, not Y - easy to misread
- Environment variable FOO must be set before running tests

### Next 3 Actions
1. <specific command or action>
2. <specific command or action>
3. <specific command or action>
```

## Storage

Write to `.firefly/handoff.md`. SessionStart re-injects this file automatically after `/clear` or compaction.

```bash
# Capture ground truth
git status
git log --oneline -5
git diff --stat HEAD~1
cat .firefly/debug/state.md   # if debugging was in progress
```

## Rules

- MUST reconstruct ground truth from git/files, not from conversation memory.
- NEVER include implementation justifications in the handoff - those are context pollution for the next session.
- Keep it <= 600 tokens so it survives re-injection without crowding the context.
- MUST list "traps" - surprising or misleading things the next session will hit.
- After writing handoff: run the verifier one last time; record output in ground truth section.
