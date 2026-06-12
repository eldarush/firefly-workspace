---
name: distilling-lessons
description: Use when reviewing session friction or wins to extract durable playbook lessons - quality bar, delta-op format, and lifecycle rules.
---
# Distilling Lessons

**A polluted playbook is worse than an empty one. Write fewer, better lessons.**

## Sources

Read `.firefly/candidates.jsonl` - contains: error streaks, repeated commands, corrections by human, guard denials, wins. The automatic loop (auto-retro at Stop, recurrence auto-lessons at SessionEnd) skims fresh signals using THIS same schema and quality bar; the manual deep pass reviews the whole backlog.

## Quality Bar per Lesson

Each lesson MUST be:
- **Imperative + checkable**: "Run X before Y" not "Consider running X".
- **Generalizable**: applies beyond the specific incident, but still concrete.
- **<= 300 characters**.
- **One rule per lesson**: compound rules (A and B) split into two lessons.
- **Scoped**: `global | sre | qa | dev | research | repo:<name>`.
- **Tagged**: 2-4 tags (e.g., `["helm","deploy","rollback"]`).
- **Evidence attached**: session ID + one sentence why.

Skip: one-offs, tool flakes (kiwix timeout, network hiccup), lessons already covered by an existing playbook entry.

Repeated multi-step workflow (>= 3 occurrences) -> suggest a new SKILL file, not a lesson.

## Delta-Op Format (JSON Lines)

```jsonl
{"op":"add","scope":"sre","tags":["helm","deploy"],"lesson":"Run helm template | kubeconform before helm upgrade in any env.","evidence":["sid:abc123 - upgrade failed due to invalid apiVersion"]}
{"op":"feedback","id":"lsn-042","helpful":1,"evidence":"Applied in sid:def456, caught broken chart immediately"}
{"op":"feedback","id":"lsn-007","harmful":1,"evidence":"sid:ghi789 - rule caused unnecessary delay in hotfix path"}
{"op":"edit","id":"lsn-042","lesson":"<revised text>","evidence":["reason for edit"]}
{"op":"deprecate","id":"lsn-003","evidence":"Covered by lsn-042 with broader scope"}
```

## Lifecycle

```
added -> quarantined -> active -> deprecated
                    ^
                    2x helpful, 0x harmful
                    OR human approval
```

- Auto-quarantine if harmful >= helpful + 2.
- Human can override any lifecycle transition.

## Conservatism Rules

- 0-5 ops per retro session. More means you are not filtering.
- NEVER add a lesson without evidence.
- NEVER add a lesson that captures only YOUR session's context.
- Prefer editing an existing near-miss lesson over adding a new one.
- If uncertain: do not add. Re-examine next retro.
