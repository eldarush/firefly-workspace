---
name: systematic-debugging
description: Use when a bug resists the first fix attempt, an error repeats, or behavior diverges from expectations without obvious cause.
---
# Systematic Debugging

**Rule zero: NO fixes before root cause.**

## Debug Loop (max 5 iterations, then escalate)

1. **Reproduce reliably.** Capture the EXACT error: message, file, line, stack. Paste it verbatim. If you cannot reproduce it, say so and stop.
2. **Read what the error names.** The error message names a file and line. Read that file. Read that line and the 10 lines around it. Do this BEFORE forming hypotheses.
3. **Form 2-3 ranked hypotheses.** For each: what would be true if this is the cause? What evidence would refute it?
4. **Test top hypothesis with the cheapest READ-ONLY probe.** `grep`, `curl --dry-run`, one extra log line, one assertion. Not a code change.
   - Refuted -> next hypothesis. Update state.
   - Confirmed -> proceed to step 5.
5. **Minimal fix at the CAUSE.** Not at the symptom. Not "while I'm here" extras.
6. **Verify:** original repro passes AND full test suite passes (no regression).

## State File

Write progress to `.firefly/debug/state.md` after each iteration. This survives context resets.

```markdown
## Debug: <ticket or short description>
Error: <verbatim>
Reproduce: <command>
Hypotheses:
- [x] H1: <desc> - REFUTED because <evidence>
- [ ] H2: <desc> - testing
Fix attempted: none
```

## Binary Search Tactics

| Problem type | Tactic |
|---|---|
| Regression with known timeframe | `git bisect start; git bisect bad HEAD; git bisect good <sha>` |
| Bad data in pipeline | Bisect the data set: run on first half, then second half |
| Multi-layer stack (client/API/DB) | Probe each layer boundary independently; isolate the failing layer |
| Flaky test | Run 20x in loop: `for i in {1..20}; do go test -run TestFoo; done` - capture failure rate |

## Anti-Patterns

| Anti-Pattern | Symptom | Correction |
|---|---|---|
| Shotgun fix | Multiple changes at once | One change, one probe, one verify |
| Fixing the symptom | Error gone, root cause active | Ask: where does this value originate? Fix there. |
| "While I'm here" | Unrelated change in same commit | Separate commit or separate PR |
| Retry identical command | Same command, hoping | New hypothesis required before retry |
| Explaining without reading | "It probably..." | Read the file the error names. Always. |
| Iteration overflow | >5 cycles, still stuck | STOP. Write findings to state.md. Present to human. |

## Rules

- MUST reproduce before fixing.
- MUST read the file the error names before forming hypotheses.
- NEVER apply a fix before confirming the hypothesis.
- NEVER make more than one change per hypothesis test.
- After 5 iterations without resolution: stop, present findings, ask for human input.
