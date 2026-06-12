# Adoption playbook & ROI

A plugin nobody adopts improves nobody. This is the rollout that turns
"the model is not good enough" into measurable throughput - without
mandating anything.

## Why your architects' prompts fail (and what changes)

| Failure pattern | Firefly counter |
|---|---|
| One-line prompt, 500-line expectation | `/ff:plan` interviews them; the plan is theirs to approve |
| Whole repo dumped into context | scout agent + context discipline: curated <= 2K tok briefs |
| Model claims "done", nobody checks | stop gate + verification-before-completion skill |
| Same fix re-derived weekly | lessons + playbook injection; `/ff:skillgen` automates repetition |
| "The model is bad" | model-discipline skill: weak-model harness (small steps, explicit verification, fresh contexts) makes M2-class models punch above their weight |

## Rollout (8 weeks, one team)

**Week 0 - baseline.** 30-minute interviews: where does AI help/fail today?
Capture per-engineer metrics for comparison: tasks attempted with AI,
first-pass useful rate (gut estimate), retries per task. Install nothing yet.

**Weeks 1-2 - pilot with 2 architects.** Install via internal mirror
(`docs/INSTALL-airgapped.md`), `/ff:init` on one real repo each,
`/ff:onboard` together. Rule of the fortnight: every non-trivial task starts
with `/ff:plan`. Learning happens automatically at every session close; the
platform team just watches `.firefly/PLAYBOOK.md` fill up.

**Weeks 3-4 - convert friction to assets.** Review pilot lessons; promote
2-3 recurring workflows into skills with `/ff:skillgen` (e.g. "add a QaaS
test suite", "debug our CI library job"). These become the demo material: the
plugin already knows *your* environment.

**Weeks 5-6 - team rollout.** Managed settings auto-enable. One brown-bag:
the architect/implementer contract, the 6 core verbs (`plan`, `implement`,
`review`, `debug`, `research`, `retro`), and one live demo of a promoted
skill. Each engineer runs `/ff:onboard` solo after.

**Weeks 7-8 - ROI readout.** Re-measure week-0 metrics. Review
`.firefly/audit.log` safety saves (denied destructive commands are near-miss
reports). Ship the readout to leadership with the playbook diff: *N lessons,
M skills, the team's operational knowledge now compounds.*

## Metrics that matter

| Metric | Source | Healthy trend |
|---|---|---|
| First-pass useful rate | engineer rating per task (1 keystroke in retro) | up and to the right |
| Retries / corrections per task | `.firefly/events.jsonl` corrections counter | falling |
| Verification coverage | sessions where verify ran before "done" (events) | -> ~100% |
| Unsafe commands blocked | audit.log | nonzero = layered defense working |
| Lessons active / skills promoted | playbook.json | steady growth, then plateau |
| Sentiment: "model is bad" complaints | vibes / interviews | replaced by specific, fixable asks |

## Sustaining (the low-effort part)

- **Weekly, 15 min, platform team:** skim new playbook lessons across pilot
  repos; approve/deprecate; promote anything twice-requested into a skill.
- **Monthly:** version-bump the plugin with new skills/lessons baked in;
  announce in the team channel with one concrete before/after.
- **Quarterly:** re-run the eval corpus (`evals/`) against your current model
  gateway; prune skills nobody's used (check events).

## Anti-patterns

- **Mandating /ff:plan for everything.** Trivial tasks deserve trivial flow;
  the plugin nudges, never blocks legitimate work. Forced ceremony breeds
  resentment and shadow usage.
- **Letting the playbook rot.** Quarantine exists, decay exists, but a human
  glance weekly keeps trust high. An untrusted playbook gets ignored.
- **Measuring lines of code.** Measure verified-task throughput and rework
  rate. 50x comes from parallelism + fewer redos + knowledge reuse, not
  typing speed.
