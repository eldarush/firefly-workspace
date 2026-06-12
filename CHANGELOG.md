# Changelog

All notable changes to Firefly Workspace.

## [1.1.0] - 2026-02-04

The learning loop is now **fully automatic** - every prompt, every command,
every session improves the playbook with zero user action.

### Added

- **Auto-retro at Stop** (`stop_gate.py`): when a session produced >= 2 fresh
  learnable signals (and >= 3 turns), the Stop hook blocks once and hands the
  model its own friction summary + the delta-op schema; the model appends
  <= 3 high-bar proposals to `.firefly/proposals.jsonl` before finishing.
  Once per session, fail-open, honors `stop_hook_active`.
- **Recurrence auto-lessons** (`distill.py auto_propose`): signals recurring
  across >= 2 distinct sessions (error patterns, repeated workflows,
  corrections, guard denials) become quarantined lesson proposals from vetted
  templates - fully deterministic, no LLM involved. Re-recurrence converts to
  +1 helpful via curator dedup, so persistent patterns self-activate.
- **Implicit feedback** (`session_end.py` + `session_start.py`): sessions
  that end verified, correction-free, >= 3 turns emit +1 helpful for every
  lesson injected at SessionStart (capped at 6). Two clean sessions activate
  a trial lesson. Usage is the feedback - no thumbs required.
- **`learning` config block** (`.firefly/config.json`): `auto_reflect`,
  `auto_reflect_min_candidates`, `auto_reflect_min_turns`, `auto_lessons`,
  `auto_feedback`, `min_recurrence` - all on by default, all tunable.
- 12 new harness checks (`[auto-learning]`) - 90 total.

### Changed

- `session_end.py` now chains distill -> auto-propose -> implicit feedback.
- SessionStart shows "Playbook auto-updated: N ops applied" when the curator
  consumed proposals, and the manual-retro nudge now fires at a backlog of
  6+ candidates (was 3) since the automatic loop skims fresh signals.
- `/ff:retro` repositioned as the optional **deep pass** over the full
  backlog; `/ff:onboard`, README, ARCHITECTURE, SELF-IMPROVEMENT, ADOPTION,
  PERSONAS updated to describe the automatic-first loop.

## [1.0.0] - 2026-02-04

First public release.

### Added

- **Plugin core**: `ff` plugin + self-hosting marketplace manifest
  (`strict: true`), MIT licensed.
- **14 commands**: `/ff:init`, `/ff:plan`, `/ff:implement`, `/ff:review`,
  `/ff:debug`, `/ff:research`, `/ff:parallel`, `/ff:retro`, `/ff:lessons`,
  `/ff:skillgen`, `/ff:commit`, `/ff:handoff`, `/ff:onboard`, `/ff:config` -
  all user-invoked only (`disable-model-invocation`).
- **7 agents** (`model: inherit`, least-privilege tools): planner, scout,
  implementer, evaluator, researcher, reflector, auditor.
- **25 skills**: 11 discipline (model-discipline, brainstorming,
  writing-plans, tdd, systematic-debugging, verification-before-completion,
  requesting-code-review, best-of-n, critical-decision, handoff-and-clear,
  skill-authoring), 2 self-improvement (lesson-capture, distilling-lessons),
  4 cross-persona (runbook-authoring, adr-authoring, explaining-systems,
  offline-docs-lookup), 8 persona (SRE incident-triage + gitops-operations,
  QA test-design + flaky-test-triage, DEV code-review + ci-debugging,
  Research literature-synthesis + experiment-design).
- **8 hook wirings** (Python 3.8+ stdlib, fail-open, LF-only):
  SessionStart contract+lesson injection, UserPromptSubmit task frames +
  correction capture, PreToolUse Bash guard (R4 deny / R3
  protected-context deny + audit log), PostToolUse/SubagentStop flight
  recorder with error-streak nudges, Stop verification gate, PreCompact
  handoff snapshot, SessionEnd heuristic distiller.
- **Self-improvement engine**: deterministic curator (delta ops, Jaccard
  dedup, decay, quarantine lifecycle, caps, PLAYBOOK.md render, audit),
  heuristic distiller, reflector/auditor agent pair, `/ff:skillgen`
  promotion path. LLM proposes; Python applies; human is the lawmaker.
- **Safety model**: R0-R4 risk classes, pipe-to-shell deny, protected
  contexts/namespaces globs, evidence-not-instructions contract rule,
  prompt-injection eval corpus (9 scenarios).
- **Docs**: architecture, safety, self-improvement, personas, airgapped
  install (mirror/managed-settings/release checklist), adoption playbook
  with ROI metrics.
- **Tests**: 58-check stdlib harness (`python3 tests/run_tests.py`) covering
  curator lifecycle, guard classification, distiller mining, hook I/O
  contracts, budgets, and repo structure.

### Provenance

Design synthesized from 10 parallel research threads (Claude Code plugin
internals, hooks reference, agent-skills spec, ACE/Reflexion/Voyager-style
memory architectures, context-engineering practice, weak-model harnessing,
multi-agent orchestration patterns, DevOps persona workflows, prior art
review) aggregated and ranked before implementation. Selected concepts
(risk-class vocabulary, injection eval corpus seed, airgap release checklist,
adoption rollout cadence) refined from the Firefly team's internal draft.
