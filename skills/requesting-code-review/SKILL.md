---
name: requesting-code-review
description: Use when work is ready for review or the user asks for a second opinion on changes - how to request and process an independent review.
---
# Requesting Code Review

**The value of review is INDEPENDENCE. The reviewer must see the spec and diff only - never your conversation, justifications, or implementation notes. Contamination destroys independence.**

## How to Package a Review Request

Provide exactly these three things to the reviewer, nothing more:

1. **Spec / acceptance criteria** - what the change is supposed to do, as a list of checkable statements.
2. **The diff** - `git diff main...HEAD` or `git diff --staged`. Clean, no debug leftovers.
3. **Verifier command + last output** - the command to reproduce your test results and the actual output.

Do NOT include: your reasoning, what you tried first, why you made specific choices. The code must speak.

## Review Package Template

```markdown
## Review Request

### Spec
- [ ] <criterion 1>
- [ ] <criterion 2>

### Diff
<paste or attach diff>

### Verifier
Command: `<command>`
Output:
```
<paste trimmed real output>
```
```

In Firefly: `/ff:review` automates packaging and invokes the evaluator agent.

## Triage Findings

Triage every finding honestly. NEVER drop a finding silently.

| Finding Type | Definition | Action |
|---|---|---|
| Fix-now | Bug or spec violation | Fix before merging; re-verify |
| Defer | Real issue, out of scope | Tell the human explicitly; open a ticket |
| Reject | False positive | Explain WHY the code is correct in a comment; do not just restate intent |

## Rules

- NEVER argue with a finding by restating your intent - the code must speak. If the code is correct, add a comment that makes it obvious; then the finding is resolved.
- NEVER silently drop a finding; triage every one.
- MUST re-run verifier after fixing findings.
- If a "fix-now" finding is disputed, escalate to the human - do not decide alone.
- NEVER request review on code with known failing tests; fix them first.

## After Review

1. Apply fix-now items.
2. Re-run full verifier.
3. Confirm each fix-now finding is resolved in the response.
4. List defer items with ticket references.
5. List reject items with rationale.
