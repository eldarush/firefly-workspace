---
description: Independent clean-context review of the current diff against its spec
argument-hint: "[base ref, default: working tree + staged changes]"
disable-model-invocation: true
---

Run an independent review of the current changes: $ARGUMENTS

1. **Collect the artifact**: `git diff` + `git diff --staged` (or diff against
   the given base ref). If there is no diff, say so and stop. Collect the spec:
   `.firefly/plan.md` if present, else reconstruct the task statement from the
   conversation in 3-5 bullet points and confirm it with the user.

2. **Delegate to the evaluator**: spawn the `evaluator` subagent with ONLY:
   (a) the spec, (b) the diff, (c) the project verifier command from
   `.firefly/config.json`. Do NOT include the conversation history - the value
   of this review is the clean context: the evaluator judges what was built,
   not what was discussed.

3. **Triage the findings yourself**: for each finding, classify
   - `fix-now`: real bug / spec violation -> fix it immediately, re-verify
   - `defer`: legitimate but out of scope -> list for the user
   - `reject`: false positive -> say why in one line
   Never silently drop a finding.

4. **Report**: evaluator verdict, findings table with your triage, fixes
   applied (with re-verification evidence), deferred items.

Use this before every merge request of consequence. It is the cheapest
code-review cycle your team has.
