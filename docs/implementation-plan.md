# Firefly Workspace Implementation Plan

## Phase 0: Foundation

- Create Claude Code marketplace catalog.
- Create `firefly-workspace` plugin manifest.
- Add default `firefly-architect` agent.
- Add bounded specialist agents.
- Add reusable workflow skills.
- Add dependency-free hook engine.
- Add starter governance policy, schemas, and eval seeds.
- Add unit and structure tests.

Status: implemented in `0.1.0`.

## Phase 1: Internal Hardening

- Replace starter command regex policy with a signed policy bundle.
- Validate all JSONL ledger events against `schemas/audit-event.schema.json`.
- Validate all retrospective proposals against `schemas/proposal.schema.json`.
- Add redaction tests for common secret formats.
- Add a local `claude plugin validate .` CI job.
- Add prompt-injection corpus tests against the governance skill and security agent.
- Add release provenance and SBOM generation.

## Phase 2: Airgap Release Pipeline

- Create connected staging build.
- Mirror approved docs, packages, MCP servers, and images.
- Package Claude plugin seed directory.
- Sign release artifact and policy bundle.
- Test install with public network disabled.
- Publish to internal marketplace path or Git host.
- Produce rollback bundle for the previous signed version.

## Phase 3: Firefly Team Specialization

- Add `.firefly/context.md` templates for SRE, QA, DEV, and Research teams.
- Connect approved MCP servers for GitLab, Grafana, Firefly, WikiAll, QAAS, Kubernetes read-only, and CI evidence.
- Convert top 10 repeated internal workflows into skills.
- Create QAAS release evidence integration.
- Add GitLab MR and CI componentization workflows.

## Phase 4: Improvement Foundry

- Mine conversations and ledger entries into opportunity cards.
- Generate draft skills from successful threads.
- Replay source tasks against candidate skills.
- Add stable/beta channels.
- Track adoption, first-pass usefulness, verification coverage, unsafe-command blocks, and accepted outcome cost.

## Phase 5: Advanced Orchestration

- Add visible task graph artifacts.
- Add multi-agent debate only for architecture/security tradeoffs.
- Add Tree-of-Thought style planning only for high-risk ambiguous designs.
- Add prompt evolution experiments with regression gates.
- Keep human approval for all durable behavior changes.
