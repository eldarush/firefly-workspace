# Firefly Workspace Plugin

This plugin is the Claude Code-native implementation of Firefly Workspace.

## Agents

- `firefly-architect`: default orchestrator and human-as-architect workflow.
- `codebase-cartographer`: read-only codebase and context mapping.
- `plan-critic`: read-only plan and architecture critique.
- `implementation-worker`: bounded code/config implementation.
- `verification-sentinel`: independent verification and evidence review.
- `sre-diagnostician`: read-only SRE/Kubernetes/GitOps incident analysis.
- `qa-strategist`: QAAS, release qualification, flake triage, and experiment design.
- `security-governor`: policy, prompt injection, secrets, MCP risk, and approvals.
- `workflow-miner`: converts repeated work into proposals for skills, hooks, agents, evals, memory, or policy.

## Skills

- `architect`: plan and orchestrate non-trivial work.
- `context-map`: gather lean repository and operations context.
- `deep-research`: split independent research tracks and synthesize.
- `implementation-loop`: implement small verified changes.
- `verify-and-reflect`: evidence before completion claims.
- `mine-skill`: convert repeated workflows into reusable artifacts.
- `sre-ops`: SRE, Kubernetes, Helm, Argo, Kargo, Grafana, CI, operators.
- `qa-release`: QAAS, test generation, flaky triage, release evidence.
- `prompt-upgrade`: governed prompt/skill improvement.
- `offline-release`: airgapped bundle planning.
- `governance`: risk, approvals, audit, MCP/tool policy, prompt injection.

## Hook Engine

`scripts/firefly_hook.py` is dependency-free and supports:

- `SessionStart`: create data directories and inject approved memory/context.
- `UserPromptSubmit`: record prompt and inject project context.
- `PreToolUse`: deny starter dangerous Bash patterns.
- `PostToolUseFailure`: add failure-handling guidance.
- `Stop`: create retrospective proposals for human review.

Persistent state is written to `${CLAUDE_PLUGIN_DATA}`.

## Local Context

Create `.firefly/context.md` in a project to teach Firefly local conventions without editing the plugin:

```markdown
# Firefly Local Context

- Use QAAS for release evidence.
- Helm charts should use the common repository helpers.
- Production changes must be MR-only unless incident break-glass is active.
```
