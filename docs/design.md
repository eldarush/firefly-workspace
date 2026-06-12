# Firefly Workspace Design

## Goal

Build a Claude Code-native workspace that makes strong AI engineering behavior the default for an airgapped DevOps organization.

## Product Thesis

The problem is not only model quality. Senior engineers lose value when a coding assistant depends on perfect prompts, ad hoc context stuffing, and manual verification discipline. Firefly Workspace supplies the missing operating system: staged workflows, context budgets, specialist agents, governed hooks, offline documentation, evals, and a controlled improvement loop.

## Architecture

Firefly Workspace is a marketplace repository with one plugin:

- `skills/`: reusable workflows invoked as `/firefly-workspace:<skill>`.
- `agents/`: bounded specialists for orchestration, research, implementation, verification, SRE, QA, governance, and workflow mining.
- `hooks/`: Claude Code lifecycle hooks for context injection, local ledger, starter policy checks, failure guidance, and retrospective proposals.
- `policy/`: starter command risk policy and MCP allowlist.
- `schemas/`: improvement proposal and audit-event schemas.
- `evals/`: prompt-injection and governance regression seeds.

## Operating Model

The main agent, `firefly-architect`, keeps the human in the architect seat:

1. Understand the goal.
2. Localize evidence.
3. Expose architecture decisions.
4. Build a small task graph.
5. Delegate independent work.
6. Implement bounded changes.
7. Verify with concrete evidence.
8. Reflect into proposals, not automatic mutation.

## Self-Improvement

Firefly does not rewrite its own prompts or policies at runtime. It uses a governed loop:

```text
observe -> reflect -> propose -> evaluate -> approve -> version -> release -> monitor -> rollback
```

The hook engine stores local retrospective proposals. The `mine-skill` and `prompt-upgrade` skills turn successful or frustrating sessions into draft artifacts with validation plans. Human owners promote only after evals and review.

## Airgap Assumptions

The plugin assumes:

- no public internet inside the target environment;
- local model or approved model gateway;
- internal Git, package mirrors, OCI registries, Kiwix/WikiAll, MCP servers, CI runners, and docs;
- signed import/release process;
- no live dependency pulls from public registries during use.

## Safety Boundaries

Risk classes:

- `R0`: read-only.
- `R1`: workspace-only edits and local tests.
- `R2`: shared CI/config/dependency/release changes.
- `R3`: cluster, deployment, registry, secret, or production impact.
- `R4`: destructive or policy-weakening.

`R2+` actions should require explicit approval; `R3` should require service-owner/two-person approval; `R4` is denied by default.

## Non-Goals For 0.1.0

- No autonomous prompt or policy self-editing.
- No bundled external MCP servers.
- No package-manager dependency installation.
- No direct production deployment workflow.
- No claim of 50x productivity without local ROI measurement.
