---
name: lesson-capture
description: Use when something in the session deserves to become a durable team lesson - a painful failure, a discovered trap, a correction from the user, or a win worth repeating.
---

# Lesson capture

The plugin's hooks capture friction automatically, but the BEST lessons are
noticed in the moment by you or the user. This skill is how to capture one
well, right now, without derailing the task.

## When to capture

- The user corrected a behavior that could recur ("never X in this repo")
- A failure had a non-obvious cause that took real effort to find
- An approach worked surprisingly well and is repeatable
- A trap: something that looks right but is wrong in this environment

Do NOT capture: one-off typos, tool flakiness, anything already in the
playbook (check `.firefly/PLAYBOOK.md` first), vague advice ("be careful").

## Quality bar for the lesson text

- Imperative and checkable: "Run `helm template | kubeconform` before any
  helm upgrade" - not "validate charts carefully"
- Generalizable beyond this incident, concrete enough to act on
- <= 300 chars; one rule per lesson (split compound rules)
- Scoped: global | sre | qa | dev | research | repo, plus 2-4 topic tags

## How to capture (10 seconds)

Append ONE line to `.firefly/proposals.jsonl`:

```json
{"op":"add","scope":"sre","tags":["helm","ci"],"lesson":"Run helm template | kubeconform before any helm upgrade; the cluster rejects what the chart allows.","evidence":["<session>: upgrade failed on CRD"],"origin":"auto"}
```

If the USER explicitly dictated the rule, use `"origin":"human"` - human
lessons activate immediately; auto lessons start quarantined until they prove
helpful twice.

The curator picks it up at the next prompt automatically. Then return to the
task - capture must never cost more than 30 seconds.

## Closing the loop

When an injected playbook lesson saves you (or misfires), report it:

```json
{"op":"feedback","id":"lsn-xxx","helpful":1,"evidence":"prevented bad helm upgrade"}
```

Counters drive injection ranking, promotion, and auto-quarantine - feedback is
what makes the playbook self-correcting rather than self-accumulating.
