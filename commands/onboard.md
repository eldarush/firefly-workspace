---
description: Interactive tour of Firefly Workspace - what it does, how to work with it, first wins
disable-model-invocation: true
---

Give the user a hands-on tour of Firefly Workspace. Keep it conversational -
short sections, check questions, no wall of text.

1. **The philosophy (30 seconds)**: explain plainly:
   - YOU (the human) are the architect, lawmaker, and orchestrator. Claude and
     its agents implement, verify, research, and propose.
   - The plugin enforces engineering discipline mechanically: plans before
     code, verification before "done", root cause before fixes, production
     read-only by default.
   - It LEARNS: hooks watch for friction (repeated errors, corrections,
     repeated commands), /ff:retro distills lessons, lessons get injected into
     future sessions. The more the team uses it, the better it gets.

2. **Show the state**: check whether `.firefly/config.json` exists. If not,
   offer to run /ff:init now. If yes, show: personas, verifier commands,
   protected contexts, lesson count from `.firefly/PLAYBOOK.md`.

3. **The daily loop** - walk through with a tiny example from THEIR repo:
   - `/ff:plan <task>` -> interview -> approved plan
   - `/ff:implement` -> step-by-step with verification gates
   - `/ff:review` -> independent clean-context review
   - `/ff:commit` -> disciplined commit
   - `/ff:retro` weekly or after pain -> the plugin gets smarter

4. **The safety net**: explain in 3 sentences: destructive commands are denied
   outright, mutations against production contexts are blocked, everything is
   audited in `.firefly/audit.log`. The agent cannot bypass this; only the
   human can change `.firefly/config.json`.

5. **Specialist moves** (mention, don't demo): `/ff:debug` for nasty bugs,
   `/ff:research` for offline doc dives, `/ff:parallel` for trying competing
   approaches, `/ff:skillgen` when a workflow repeats, `/ff:handoff` before
   /clear, `/ff:lessons` to govern the playbook.

6. **First win**: ask what they are working on TODAY and suggest the exact
   first command to run on it.
