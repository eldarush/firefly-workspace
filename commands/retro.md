---
description: Deep retrospective - sweep the full candidate backlog into playbook lessons (the automatic loop only skims fresh signals)
argument-hint: "[optional focus, e.g. 'this session' or 'helm failures']"
disable-model-invocation: true
---

Run a Firefly deep retrospective: $ARGUMENTS

Learning runs automatically (auto-retro at session close, recurrence
auto-lessons, implicit feedback). THIS command is the manual deep pass: it
reviews the WHOLE backlog with the reflector agent and the human in the loop,
catching cross-session patterns the automatic skim misses.

1. **Gather**: read `.firefly/candidates.jsonl` (entries with status "new")
   and `.firefly/playbook.json`. If there are no new candidates, also consider
   the CURRENT conversation: did anything go wrong/repeat/get corrected that
   deserves a lesson? If nothing at all, report "nothing to distill" and stop.

2. **Reflect**: spawn the `reflector` subagent with the candidate list, the
   existing playbook lesson summaries (id + text), and any user focus from the
   arguments. It appends delta-ops to `.firefly/proposals.jsonl` and reports
   what it proposed/skipped.

3. **Apply**: run the curator:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/curator.py"`
   (use `py` on Windows). It dedups, quarantines new lessons, applies feedback,
   enforces caps, and re-renders `.firefly/PLAYBOOK.md`.

4. **Mark processed**: run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/distill.py" mark <comma-separated-keys>`
   with the candidate keys the reflector reported as handled.

5. **Report to the architect**: show new/updated lessons with their status
   (new ones start QUARANTINED - they activate after proving helpful twice, or
   immediately via human approval in `/ff:lessons`). Mention any skill
   suggestions the reflector made (`/ff:skillgen`).

Cadence: when SessionStart reports an accumulated backlog (>= 6 candidates),
after an especially painful week, or before promoting lessons to the team
repo. Takes ~2 minutes; compounds forever.
