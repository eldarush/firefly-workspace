# Research Synthesis

This document summarizes the research used to shape Firefly Workspace.

## Claude Code Native Packaging

Claude Code plugins can bundle skills, agents, hooks, MCP servers, LSP servers, settings, and related assets. The plugin uses the native layout:

```text
plugins/firefly-workspace/
  .claude-plugin/plugin.json
  skills/
  agents/
  hooks/hooks.json
  settings.json
```

Useful official references:

- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Plugins reference: https://code.claude.com/docs/en/plugins-reference
- Plugin marketplaces: https://code.claude.com/docs/en/plugin-marketplaces
- Skills: https://code.claude.com/docs/en/skills
- Subagents: https://code.claude.com/docs/en/sub-agents
- Hooks: https://code.claude.com/docs/en/hooks
- MCP: https://code.claude.com/docs/en/mcp

## Prompting And Context Engineering

The strongest pattern for weaker or offline models is not longer prompts. It is workflow scaffolding:

- staged task flow;
- explicit context slots;
- retrieved local evidence;
- examples;
- structured outputs;
- verification loops.

References:

- Anthropic prompting best practices: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices
- Effective context engineering: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- ReAct: https://arxiv.org/abs/2210.03629
- Least-to-Most prompting: https://arxiv.org/abs/2205.10625
- Plan-and-Solve: https://arxiv.org/abs/2305.04091
- Lost in the Middle: https://arxiv.org/abs/2307.03172

## Agent Orchestration

Use simple composable workflows before adding autonomous agents. Parallel agents are valuable for independent research and review, but routine coding should remain a bounded planner/implementer/verifier loop.

References:

- Building effective agents: https://www.anthropic.com/engineering/building-effective-agents
- Multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system
- Tree of Thoughts: https://arxiv.org/abs/2305.10601
- Reflexion: https://arxiv.org/abs/2303.11366
- Self-Refine: https://arxiv.org/abs/2303.17651
- SWE-agent: https://arxiv.org/abs/2405.15793

## Self-Improvement

The assistant should improve through governed release mechanics, not autonomous self-editing. Capture evidence, propose changes, run evals, approve, version, monitor, and roll back.

References:

- DSPy: https://arxiv.org/abs/2310.03714
- Reflexion: https://arxiv.org/abs/2303.11366
- Self-Refine: https://arxiv.org/abs/2303.17651
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- OWASP LLM Top 10: https://owasp.org/www-project-top-10-for-large-language-model-applications/

## DevOps, SRE, QA, And Governance

Firefly Workspace should default to read-only diagnosis, MR-only remediation, explicit release evidence, and approval-gated production impact.

References:

- NIST SSDF: https://csrc.nist.gov/pubs/sp/800/218/final
- SLSA provenance: https://slsa.dev/spec/v1.2/build-provenance
- in-toto attestations: https://github.com/in-toto/attestation
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/concepts/semantic-conventions/
- CycloneDX: https://cyclonedx.org/
- pytest flaky tests: https://docs.pytest.org/en/stable/explanation/flaky.html
- Kubernetes server-side apply: https://kubernetes.io/docs/reference/using-api/server-side-apply/
- Helm chart tests: https://helm.sh/docs/topics/chart_tests/
- Argo CD GitOps: https://argo-cd.readthedocs.io/

## Adoption

Senior architects need less "prompt training" and more workflow surfaces: prompt composers, context receipts, trust ladders, one-click skill mining, and ROI measurement tied to accepted outcomes and verification burden.

Track:

- active users;
- skill invocations;
- first-pass useful rate;
- retries per task;
- verification coverage;
- rejected suggestions by reason;
- unsafe-command blocks;
- accepted PR/MR outcomes;
- team sentiment.
