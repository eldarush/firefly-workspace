---
description: Best-of-N parallel exploration - try 2-3 approaches in isolation, judge, adopt the winner
argument-hint: "<problem with plausible competing approaches>"
disable-model-invocation: true
---

Explore competing approaches in parallel: $ARGUMENTS

Use this when a problem has 2-3 genuinely different solution strategies and
arguing about them abstractly is slower than trying them. Weak models gain a
LOT from best-of-n selection - generation is cheap, judgment is easier.

1. **Define the bake-off**: with the user, fix (a) the exact task, (b) 2-3
   named approaches (e.g. "regex-based" vs "AST-based"), (c) the SAME
   acceptance test all candidates must pass, (d) judging criteria ranked
   (correctness > simplicity > performance > diff size, unless user reorders).

2. **Isolate**: create one git worktree or branch per approach
   (`git worktree add ../bake-A approach-a` or plain branches if worktrees are
   unavailable). Candidates must not see each other.

3. **Map**: launch one `implementer` subagent per approach IN PARALLEL. Each
   prompt: the task, ONLY its assigned approach, the acceptance test, the
   working directory, and orders to report diff + verifier output.

4. **Filter deterministically**: run the acceptance test on each candidate
   yourself. Candidates that fail are OUT - no LLM judging of broken code.

5. **Judge**: spawn the `evaluator` subagent with the surviving diffs
   (anonymized as A/B/C) + the criteria. It returns a ranked verdict with
   reasoning per criterion.

6. **Decide**: present the matrix + your recommendation. The HUMAN picks.
   Merge the winner into the working branch; clean up the losing
   worktrees/branches after explicit confirmation.
