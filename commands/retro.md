---
description: Retrospective - turn captured friction into playbook lessons (the self-improvement loop)
argument-hint: "[optional focus, e.g. 'this session' or 'helm failures']"
disable-model-invocation: true
---

Run a Firefly retrospective: $ARGUMENTS

This is the heart of the self-improvement loop: hooks captured friction into
`.firefly/candidates.jsonl`; you now distill it into playbook proposals that
the deterministic curator will apply.

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

Cadence: run after any painful session, or when the SessionStart notice shows
pending candidates. Takes ~2 minutes; compounds forever.
