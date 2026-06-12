# Changelog

All notable changes to Firefly Workspace.

## [1.2.0] - 2026-02-05

Hardened by a 100-run simulation campaign (10 waves x 10 weak-model agents
on realistic SRE/QA/DEV/Research scenarios, independent stronger-model
evaluator between waves, fixes committed per wave). Probe-scored quality
rose from 0.854 (wave 1) to a 0.954 campaign best (wave 9), with zero
destructive-bait executions and zero web-access attempts across all 100
runs. Full data: `evals/simulation/RESULTS.md`.

### Added

- **Team learning store** (`scripts/team.py`): an append-only, file-based
  lesson exchange at `.firefly-team/` (or `$FIREFLY_TEAM_DIR` - point it at
  any shared mount) so each member's confirmed lessons improve everyone
  else's sessions. Per-author JSONL, content-addressed ids, votes folded at
  read time, zero servers - safe on NFS/SMB.
- **End-of-response save confirmation** (`stop_gate.py` + `team_share.py`):
  after auto-retro distills proposals, the Stop checkpoint asks the USER
  once per session whether the session's lessons should be saved/shared -
  yes shares to the team store with attribution; no records what should
  have been done differently as a correction signal. Proven lessons
  (helpful >= 2, never harmful) auto-share at SessionEnd without asking.
- **Teammate attribution at SessionStart**: injected team lessons show
  author + origin ("from maya, confirmed"), and SessionEnd folds your
  helpful/harmful experience back as votes on the author's entry.
- **Environment spec** (`/ff:env`, `scripts/env_spec.py`): drop one
  `ENVIRONMENT.md` (or set `$FIREFLY_ENV_FILE`) describing your GitLab
  URLs, clusters, registries, mirrors - every session injects a compact
  digest and treats it as the source of truth. Works fine when absent.
- **Verify as a first-class action**: `ff verify` runs the project's
  registered verifier and records pass/fail in the flight recorder; the
  Stop gate cites the tracked outcome. Verifiers auto-register from
  observed test commands (`scripts/verifier_detect.py`).
- **Guard dry-run + audit-record contract** (`guard --check`): classify any
  command without executing it, get a paste-ready `audit line:` for the
  postmortem/PR; the CONTRACT now frames guard verdicts as the audit record
  for risky suggestions - especially ones you decide NOT to run, even when
  another rule already forbids them - and deny messages include next-step
  guidance. In simulation, recorded verdicts for refused bait went from
  10-30% of agents to 50% in one wave after the reframe.
- **Plan-aware prompt frames + FRAME_SHORT**: repeat prompts in a session
  get a 3-line frame instead of the full block; frames surface the active
  plan file when one exists.
- **Simulation harness** (`evals/simulation/`): 8 cheat-proofed scenarios,
  `ff_sim` lifecycle shim, 13-point objective probe, golden+control
  selftest, wave prep/orchestration docs, and `RESULTS.md` - rerun the
  campaign against any future change.
- 62 new harness checks - 152 total.

### Changed

- SessionStart contract: TL;DR line up top; Windows consoles get a
  `PYTHONUTF8=1` hint (cp1252 was the #1 weak-model friction); team
  lessons section with attribution; compact env-spec digest.
- `session_end.py` chain extended: distill -> auto-propose -> implicit
  feedback -> team share-promoted -> team feedback votes.
- Team checkpoint fires from 2 turns (was 3) - short focused sessions
  (one-fix TDD runs) never reached the old gate.
- `auto_reflect` threshold, curator caps, and team knobs all configurable
  under `learning` / `team` in `.firefly/config.json`.

### Fixed

- **Guard pipe-to-shell bypass**: `curl ... | sh` style installers were
  split on the pipe before pattern matching, so the pipe-to-shell deny
  patterns could never fire and such commands classified read-only. A
  whole-line pass now runs first; `curl ... | jq` correctly stays read.
  (Found by the simulation campaign's bait probe - upgrade recommended.)
- Research scenario citation rule (s7) - synthesis questions now require
  inline `[P1]`-style citations, closing the "right answer, no evidence"
  gap probed in waves 5-6.
- Console encoding crashes on Windows cp1252 consoles for hook output
  (emoji-free, ASCII-safe rendering).

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
