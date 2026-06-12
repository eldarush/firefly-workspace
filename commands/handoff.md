---
description: Write a context handoff before /clear or ending the day - the next session continues seamlessly
argument-hint: "[optional notes to include]"
disable-model-invocation: true
---

Write a session handoff: $ARGUMENTS

Long conversations rot: stale assumptions accumulate and the model drowns in
its own history. The fix is a clean reset with a good handoff. This command
writes one; SessionStart re-injects it automatically after /clear or compact.

1. **Reconstruct ground truth** - from the actual system, not memory:
   `git status`, `git diff --stat`, `git log --oneline -5`, the state of
   `.firefly/plan.md` if present, last verifier result.

2. **Write `.firefly/handoff.md`** using
   `${CLAUDE_PLUGIN_ROOT}/assets/templates/handoff.md`:
   - current goal and HOW FAR it got (done / not done, by plan step)
   - ground truth snapshot from step 1
   - key decisions made this session and their reasons (verbatim where the
     user ruled on something)
   - traps discovered (things that LOOK right but are not - the next context
     will fall into them otherwise)
   - the next 3 concrete actions, in order
   - any user notes from the arguments

3. **Trim**: the handoff must be <= ~600 tokens. Cut narrative; keep facts,
   decisions, and next actions.

4. **Confirm**: show the handoff, then recommend `/clear` (fresh start) and
   remind that the next session will see it automatically at start.
