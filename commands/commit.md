---
description: Disciplined commit - review the diff, split logical units, write a real message
argument-hint: "[optional commit message hint]"
disable-model-invocation: true
---

Create a disciplined commit: $ARGUMENTS

1. **Survey**: `git status` + `git diff` (+ `--staged`). If nothing changed,
   stop. Flag anything that should never be committed: secrets/keys/tokens,
   `.env`, large binaries, debug leftovers (print/console.log/TODO HACK),
   commented-out code. Fix or exclude before proceeding.

2. **Verify first**: if code files changed and the verifier was not run since
   the last edit, run it now (`.firefly/config.json` verify.commands).
   Committing unverified code defeats the whole workflow.

3. **Split logical units**: if the diff mixes unrelated concerns (feature +
   refactor + config), propose separate commits and stage selectively
   (`git add -p` / per-file). One reviewable idea per commit.

4. **Message**: imperative subject <= 72 chars stating WHAT changed; body
   explaining WHY (the diff already shows the what). Use the team's convention
   if visible in `git log --oneline -10` (e.g. conventional commits).

5. **Commit and confirm**: show the final `git log -1 --stat`.

Never push - pushing is the user's explicit decision (and the guard will ask).
