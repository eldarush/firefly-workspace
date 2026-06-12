# Firefly Workspace

Firefly Workspace is a Claude Code-native marketplace and plugin for airgapped engineering teams. It gives developers, SREs, QA engineers, researchers, and architects a governed workspace with reusable skills, specialist agents, local hooks, and an improvement queue.

The core principle is simple: the human is the architect; Claude and its agents are implementors, reviewers, researchers, and verifiers.

## What It Ships

- A Claude Code marketplace catalog: `.claude-plugin/marketplace.json`
- One plugin: `plugins/firefly-workspace`
- Default main agent: `firefly-architect`
- Specialist agents for codebase mapping, implementation, verification, SRE, QA, security, and workflow mining
- Skills for architecture, context mapping, deep research, implementation, verification, SRE, QA, governance, offline release, and prompt/skill improvement
- A dependency-free Python hook engine for local ledger, context injection, policy checks, and retrospective proposals
- Starter governance policy, MCP allowlist, proposal/audit schemas, and prompt-injection eval seeds

## Install Locally

From this repository root:

```bash
claude plugin marketplace add .
claude plugin install firefly-workspace@fireflyteam
```

For one-session development:

```bash
claude --plugin-dir ./plugins/firefly-workspace
```

After editing plugin hooks, agents, MCP config, or settings:

```text
/reload-plugins
```

## Airgapped Install Pattern

Use this repository as a signed internal workspace release:

1. Build and validate in a connected staging environment.
2. Pin the release by git tag and commit SHA.
3. Scan, sign, and attest the bundle.
4. Import into the airgap through your approved transfer process.
5. Add the marketplace as a local path or seed it with `CLAUDE_CODE_PLUGIN_SEED_DIR`.
6. Force-enable the plugin with managed settings when appropriate.
7. Keep public package, docs, and MCP dependencies mirrored internally.

See [docs/airgap-release.md](docs/airgap-release.md).

## Daily Use

Invoke skills with the plugin namespace:

```text
/firefly-workspace:architect
/firefly-workspace:context-map
/firefly-workspace:implementation-loop
/firefly-workspace:verify-and-reflect
/firefly-workspace:sre-ops
/firefly-workspace:qa-release
/firefly-workspace:governance
/firefly-workspace:mine-skill
```

Add project-specific context in:

```text
.firefly/context.md
```

The hook engine injects approved context at session start and prompt submit, records local ledger entries under Claude Code plugin data, blocks a small set of dangerous shell patterns, and creates retrospective proposals after turns.

## Verify

```bash
python -m unittest discover -s tests -v
```

If Claude Code is installed:

```bash
claude plugin validate .
```

## Status

This is an initial `0.1.0` foundation. It intentionally does not self-modify. It observes, reflects, proposes, and waits for human-reviewed promotion through evals and signed releases.
