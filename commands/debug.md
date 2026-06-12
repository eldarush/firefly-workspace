---
description: Systematic root-cause debugging loop with hypothesis tracking - max 5 iterations, no blind retries
argument-hint: "<symptom or failing command>"
disable-model-invocation: true
---

Debug systematically: $ARGUMENTS

Discipline: NO fixes before a confirmed root cause. Track everything in
`.firefly/debug/state.md` so the investigation survives context resets.

1. **Reproduce**: run the failing command / reproduce the symptom. Capture the
   EXACT error. If you cannot reproduce it, that is the first problem - gather
   the conditions (env, versions, data) until you can.

2. **Initialize** `.firefly/debug/state.md`: symptom, exact error, repro
   command, iteration counter 0, empty hypothesis table.

3. **Loop (max 5 iterations)** - each iteration:
   a. READ the relevant code/config/logs - the error message names them.
   b. Write 2-3 ranked hypotheses in the state file (cause -> mechanism ->
      what evidence would CONFIRM and what would REFUTE each).
   c. Test the TOP hypothesis with the cheapest read-only probe first
      (log read, targeted grep, one assertion, dry-run) - not a code change.
   d. Record the result. Refuted -> next hypothesis. Confirmed -> step 4.
   e. Increment the counter. At 5 without a root cause: STOP, write a summary
      of everything ruled out, and present it to the user with your best
      remaining theory - do not thrash.

4. **Fix minimally**: the smallest change that addresses the ROOT CAUSE (not
   the symptom). State explicitly why this cause produces this symptom.

5. **Verify + regress**: re-run the original repro (must pass) AND the project
   verifier (must not regress). Where feasible, add the missing test that
   would have caught this.

6. **Distill**: append one line to the state file: "lesson candidate: ..." if
   this failure pattern is generalizable - the automatic learning loop picks
   it up at session close.
