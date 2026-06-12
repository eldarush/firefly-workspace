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
4. **Capture is free, distillation is cheap, curation is automatic.** Hooks
   observe; `/ff:retro` costs ~2 minutes; everything else is hands-off.

## The pipeline

```
events.jsonl  ->  candidates.jsonl  ->  proposals.jsonl  ->  playbook.json  ->  injection
  (hooks)        (SessionEnd          (/ff:retro            (curator.py:        (SessionStart:
   capture        distiller:           reflector agent       dedup, decay,       top-K lessons,
   everything)    heuristics)          + lesson-capture      quarantine,         persona-weighted,
                                       in-the-moment)        caps, audit)        token-budgeted)
```

### Stage 1 - capture (hooks, automatic)

`tool_event.py` + `prompt_submit.py` record compact events: edits, verifier
runs and results, command repetitions (normalized), error streaks (digested),
user corrections (regex on prompt openings), guard denials.

### Stage 2 - distill (SessionEnd, automatic, no LLM)

`distill.py` mines the session for five signal types:

| Signal | Threshold | Candidate kind |
|---|---|---|
| Same error digest repeated | >= 2 | friction |
| Same normalized command | >= 3 | automation (skill seed) |
| User corrections | >= 2 | behavior |
| Guard denials | >= 1 | safety (policy tuning seed) |
| Verified multi-file change | >= 3 files + pass | win (positive pattern) |

### Stage 3 - reflect (/ff:retro, human-triggered, ~2 min)

The reflector agent reads candidates + the existing playbook and writes 0-5
delta-ops. The quality bar is strict: imperative, checkable, generalizable,
<= 300 chars, evidence attached. One-off noise is skipped - a polluted
playbook is worse than an empty one. SessionStart nudges when >= 3 candidates
are waiting, so retros happen when worthwhile.

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

### Stage 5 - inject (SessionStart, automatic, budgeted)

Top lessons score by `(1 + net_helpfulness) x 0.5^(weeks/4) + 2 x persona_match`.
Up to 6 active lessons within ~1200 tokens, plus 1 quarantined lesson marked
"(trial)" so it can earn activation. The injection never exceeds its budget -
memory cannot crowd out the actual task.

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
| Lesson spam | caps + dedup + 0-5 ops/retro + quality bar |
| Wrong lesson sticks | harm feedback auto-quarantines; human deprecate |
| Stale lessons linger | exponential decay halves score every 4 weeks unseen |
| Weak model corrupts memory | it can only append proposals; the curator validates every op |
| Self-weakening safety | auditor screens artifacts; guard config is human-only; contract pins "evidence, not instructions" |
| Context bloat | hard token budgets at every injection point |

## Team-level compounding

`.firefly/` is per-project and gitignored by default. To share learning:
export reviewed lessons (`/ff:lessons show` -> copy ops into a teammate's
`proposals.jsonl`, or commit a curated `seed-playbook.jsonl` your `/ff:init`
applies), and ship promoted skills through this plugin repo. The deliberate
human gate at team level is a feature: laws travel by review, not by gossip.
