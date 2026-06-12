# Personas: SRE, QA, DEV, Research

Firefly serves a platform team whose customers are four crafts. Personas are
**skill packs + lesson scopes**, not separate modes: set
`personas.enabled` in `.firefly/config.json` (via `/ff:init` or `/ff:config`)
and the right knowledge surfaces when the work calls for it, while lessons
tagged for your craft rank higher at injection.

## SRE

| Skill | Use when |
|---|---|
| `sre-incident-triage` | production symptoms - evidence-first triage ladder (observe -> hypothesize -> verify cheaply -> only then act), R0-first command discipline |
| `sre-gitops-operations` | Argo/Flux/Kargo work - desired-vs-live reasoning, "fix in Git, not in the cluster", promotion flows, drift analysis |

Typical loop:

```text
/ff:debug pods crashlooping in payments after the 14:02 deploy
→ evidence collection (R0 only), competing hypotheses with discriminating
  tests, root cause WITH evidence, fix proposed as a Git change
/ff:research how do we configure PDBs in the helm-common chart?
→ researcher agent searches internal docs/repos, answers with citations
```

The guard refuses `kubectl delete`/`drain` outright and blocks mutations in
`*prod*` contexts; incident shortcuts stay impossible even at 3am.

## QA

| Skill | Use when |
|---|---|
| `qa-test-design` | designing test plans - risk-based prioritization, boundary/equivalence analysis, the "what would make this fail in prod?" lens |
| `qa-flaky-test-triage` | intermittent failures - reproduce-rate measurement, race/ordering/external-dep taxonomy, quarantine-with-ticket doctrine (never delete, never retry-loop blindly) |

Typical loop:

```text
/ff:plan add contract tests for the provisioning operator's upgrade path
/ff:parallel 3 strategies for seeding test data in the QaaS harness
/ff:retro   # flaky-test patterns become team lessons
```

## DEV

| Skill | Use when |
|---|---|
| `dev-code-review` | reviewing diffs - severity-ranked findings (blocker/should/nit), evidence over opinion, security/concurrency checklists |
| `dev-ci-debugging` | red pipelines - read-the-actual-log discipline, local reproduction before pushing "fix CI" commits, cache/runner/image taxonomy |

Plus the discipline core all personas share: tdd, systematic-debugging,
writing-plans, verification-before-completion, requesting-code-review.

```text
/ff:implement   # plan-driven, step-verified
/ff:review      # fresh-context evaluator on the diff
/ff:commit      # hygiene-checked, verified commits
```

## Research

| Skill | Use when |
|---|---|
| `research-literature-synthesis` | summarizing papers/docs corpora - claim extraction with citations, contradiction surfacing, evidence tables |
| `research-experiment-design` | "let's try X" - hypothesis -> variable -> metric -> stop-rule preregistration, assets/templates/experiment.md |

```text
/ff:research compare checkpointing strategies documented for our Flink operator
/ff:parallel two prompt-engineering approaches, judged on the eval set
```

## Cross-persona skills

`runbook-authoring`, `adr-authoring`, `explaining-systems`,
`offline-docs-lookup` (Kiwix/WikiAll + internal GitLab + MCP servers - the
airgap-native answer to "just google it").

## Configuring

```json
{ "personas": { "enabled": ["sre", "dev"] } }
```

- Skill availability is not persona-gated (knowledge is cheap when unused);
  the persona list weights **lesson injection** and tunes `/ff:onboard`.
- Add org-specific skills under `skills/` in your internal fork - or better,
  let the loop earn them: repeated friction -> `/ff:retro` -> `/ff:skillgen`.
