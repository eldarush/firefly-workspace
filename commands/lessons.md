---
description: Review and govern the lesson playbook - approve, edit, deprecate (the human is the lawmaker)
argument-hint: "[approve <id> | deprecate <id> <reason> | add <lesson text> | show]"
disable-model-invocation: true
---

Manage the Firefly playbook as the lawmaker: $ARGUMENTS

The playbook (`.firefly/playbook.json`, rendered at `.firefly/PLAYBOOK.md`) is
the team's earned memory. Lessons are injected into every session. The HUMAN
owns this law book; you are the clerk.

1. **Show state**: render a compact table of lessons - id, status
   (active/quarantined/deprecated), scope/tags, text, +helpful/-harmful,
   origin. Quarantined lessons first (they need decisions).

2. **Execute the subcommand** (or interview the user if none given):
   - `approve <id>` / `deprecate <id> <reason>` / `quarantine <id>`: append the
     matching op to `.firefly/proposals.jsonl` with `"actor":"human"`
   - `add <text>`: interview briefly for scope + tags, then append an add-op
     with `"origin":"human"` (human lessons activate immediately)
   - `edit <id>`: collect the new text, append an edit-op
   - feedback: if the user says a lesson helped/hurt, append a feedback-op

3. **Apply immediately**: run
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/curator.py"` (`py` on Windows) and
   show the resulting state of the touched lessons.

4. **Housekeeping prompts**: if any ACTIVE lesson has harmful >= helpful,
   recommend deprecation. If two lessons contradict, surface both and ask the
   lawmaker to resolve. If the playbook nears its caps (100 active / 20 per
   scope), suggest pruning the lowest-scoring entries.

Audit: every op lands in `.firefly/audit.log` automatically - mention it when
the user asks about traceability.
