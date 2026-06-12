---
description: Execute the approved plan step-by-step with verification gates after every step
argument-hint: "[plan path or step range, default .firefly/plan.md]"
disable-model-invocation: true
---

Execute the approved plan: $ARGUMENTS

1. **Load**: read `.firefly/plan.md` (or the given path). If it does not exist
   or status is not APPROVED, stop and point the user to `/ff:plan`. Confirm
   which steps are already DONE (check git status/log against the plan).

2. **Execute step by step**. For each plan step:
   - announce the step in one line
   - make the changes (or delegate a well-scoped `implementer` subagent for
     bulk, self-contained steps; keep cross-cutting steps in the main thread)
   - run the step's verifier (or the project verifier from .firefly/config.json)
   - on PASS: mark the step DONE in .firefly/plan.md, continue
   - on FAIL: fix it. If the SAME error occurs twice, stop the loop and switch
     to ff:systematic-debugging discipline instead of blind retries.

3. **Scope discipline**: implement exactly the plan. When you discover the plan
   is wrong or incomplete mid-flight, do NOT silently improvise: present the
   deviation to the user (what changed, why, options) and get a decision.
   Record approved deviations in the plan file.

4. **Final gate**: after the last step, run the FULL verifier suite, then run a
   hostile self-review of the complete diff (`git diff`): edge cases, error
   paths, leftover debug code, consistency. Fix what you find. Re-verify.

5. **Report**: files changed, verification evidence (real output), deviations
   from plan, residual risks. Then suggest `/ff:review` for an independent
   clean-context review.
