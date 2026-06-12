# The self-improvement loop

Firefly's promise: **the more the team uses it, the better it gets** - with
near-zero maintenance. This document explains exactly how, and why it cannot
corrupt itself.

## Design principles

1. **Deterministic application, LLM proposal.** A weak model is never allowed
   to rewrite memory directly. It proposes *delta operations*; a Python script
   applies them mechanically with dedup, caps, decay, and quarantine.
2. **Earned trust.** Auto-generated lessons start quarantined. They activate
   only after evidence (2x helpful, 0 harm) or human approval. Bad lessons
   self-quarantine via harm feedback.
3. **The human is the lawmaker.** `/ff:lessons` outranks everything. The
   auditor agent screens drafts, but only the human promotes durable behavior.
4. **Fully automatic by default.** Every prompt, every command, every session
   feeds the loop with zero user action: hooks capture, the distiller mines,
   auto-retro reflects at session close, recurrence converts to lessons,
   clean sessions feed back reinforcement. Commands (`/ff:retro`,
   `/ff:lessons`) are the manual override, not the engine.

## The pipeline

```
events.jsonl  ->  candidates.jsonl  ->  proposals.jsonl  ->  playbook.json  ->  injection
  (hooks           (distiller at        (AUTOMATIC:           (curator.py:        (SessionStart:
   capture          Stop + SessionEnd:   auto-retro at Stop,   dedup, decay,       top-K lessons,
   every prompt     heuristics,          recurrence auto-      quarantine,         persona-weighted,
   and command)     no LLM)              lessons, implicit     caps, audit)        token-budgeted)
                                         feedback; manual:
                                         /ff:retro deep pass)
```

### Stage 1 - capture (every prompt and command, automatic)

`tool_event.py` + `prompt_submit.py` record compact events: edits, verifier
runs and results, command repetitions (normalized), error streaks (digested),
user corrections (regex on prompt openings), guard denials.

### Stage 2 - distill (Stop + SessionEnd, automatic, no LLM)

`distill.py` mines the session for five signal types:

| Signal | Threshold | Candidate kind |
|---|---|---|
| Same error digest repeated | >= 2 | friction |
| Same normalized command | >= 3 | automation (skill seed) |
| User corrections | >= 2 | behavior |
| Guard denials | >= 1 | safety (policy tuning seed) |
| Verified multi-file change | >= 3 files + pass | win (positive pattern) |

### Stage 3 - reflect (automatic, three paths)

**3a. Auto-retro at Stop (LLM, once per session).** When a session produced
>= 2 fresh signals over >= 3 turns, the Stop hook blocks once and hands the
model its own session's candidates plus the delta-op schema. The model
appends 0-3 durable lessons to `proposals.jsonl` and stops. No command, no
ceremony - the session that *generated* the friction distills it while the
context is still warm. Honors `stop_hook_active`; never fires twice
(`learning.auto_reflect`).

**3b. Recurrence auto-lessons (deterministic, no LLM).** A signal recurring
across >= 2 distinct sessions (same error digest, same repeated workflow,
corrections pattern, guard denials) is converted into a quarantined lesson
from a vetted template at SessionEnd (`learning.auto_lessons`). When the
pattern recurs again later, the curator's dedup turns the repeat into +1
helpful - recurrence itself promotes the lesson toward activation.

**3c. `/ff:retro` (manual deep pass, ~2 min).** The reflector agent reviews
the *whole* candidate backlog plus the existing playbook - cross-session
patterns the quick automatic skim can miss. SessionStart suggests it when
>= 6 candidates have accumulated.

The quality bar everywhere: imperative, checkable, generalizable, <= 300
chars, evidence attached. One-off noise is skipped - a polluted playbook is
worse than an empty one.

### Stage 4 - curate (automatic, deterministic)

`curator.py` consumes `proposals.jsonl` atomically (`os.replace` - no double
application) at SessionStart and every prompt:

- **dedup**: similar lesson text (Jaccard on stemmed words >= 0.75, or >= 0.55
  with tag overlap) merges into the existing lesson and bumps `helpful`
- **lifecycle**: add (quarantined unless human), feedback (helpful/harmful),
  edit, approve, quarantine, deprecate; `harmful >= helpful+2` auto-quarantines
- **caps**: <= 100 active total, <= 20 per scope - lowest decayed score
  deprecates first
- **render**: `PLAYBOOK.md` for humans; **audit**: every op logged

### Stage 5 - inject + reinforce (SessionStart, automatic, budgeted)

Top lessons score by `(1 + net_helpfulness) x 0.5^(weeks/4) + 2 x persona_match`.
Up to 6 active lessons within ~1200 tokens, plus 1 quarantined lesson marked
"(trial)" so it can earn activation. The injection never exceeds its budget -
memory cannot crowd out the actual task.

Injected lesson IDs are remembered. When the session later ends **verified
and correction-free**, each injected lesson automatically earns +1 helpful
(`learning.auto_feedback`) - two clean sessions promote a trial lesson to
active without anyone touching `/ff:lessons`. Conversely, harmful feedback
(from the user or a retro) still auto-quarantines. Usage IS the feedback.

### Stage 6 - promote (skills)

When friction reflects a repeated *workflow* (not a rule), the reflector
suggests `/ff:skillgen`: draft skill -> auditor screen -> human approval ->
installed personally, per-project, or into this plugin repo for the team.
Repetition becomes automation, reviewed.

## Lesson anatomy

```json
{
  "id": "lsn-a1b2c3d4e5",
  "scope": "sre", "tags": ["helm", "ci"],
  "lesson": "Run helm template | kubeconform before any helm upgrade; the cluster rejects what the chart allows.",
  "helpful": 4, "harmful": 0,
  "status": "active", "origin": "auto",
  "created": "2026-02-01T09:00:00Z", "last_seen": "2026-02-04T10:00:00Z",
  "evidence": ["sess-91ab: upgrade failed on CRD validation"]
}
```

## Why it cannot rot

| Failure mode | Defense |
|---|---|
| Lesson spam | caps + dedup + <=3 ops/auto-retro + recurrence threshold + quality bar |
| Wrong lesson sticks | harm feedback auto-quarantines; human deprecate |
| Stale lessons linger | exponential decay halves score every 4 weeks unseen |
| Weak model corrupts memory | it can only append proposals; the curator validates every op |
| Self-weakening safety | auditor screens artifacts; guard config is human-only; contract pins "evidence, not instructions" |
| Context bloat | hard token budgets at every injection point |
| Auto-retro loops | fires once per session, honors stop_hook_active, skips trivial sessions |
| Implicit feedback inflates junk | only top-K *injected* lessons qualify, only on verified correction-free sessions |

## Tuning the automation

All knobs live under `learning` in `.firefly/config.json`:

| Key | Default | Meaning |
|---|---|---|
| `auto_reflect` | `true` | once-per-session auto-retro at Stop |
| `auto_reflect_min_candidates` | `2` | fresh signals needed to trigger it |
| `auto_reflect_min_turns` | `3` | skip trivial sessions |
| `auto_lessons` | `true` | recurrence -> deterministic lesson proposals |
| `auto_feedback` | `true` | clean verified sessions reinforce injected lessons |
| `min_recurrence` | `2` | sessions a signal must recur in first |

Set any to `false` for teams that prefer command-driven learning only.

## Team-level compounding

`.firefly/` is per-project and gitignored by default. To share learning:
export reviewed lessons (`/ff:lessons show` -> copy ops into a teammate's
`proposals.jsonl`, or commit a curated `seed-playbook.jsonl` your `/ff:init`
applies), and ship promoted skills through this plugin repo. The deliberate
human gate at team level is a feature: laws travel by review, not by gossip.
