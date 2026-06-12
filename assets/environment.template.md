# Firefly environment spec

<!-- This file is the SINGLE SOURCE OF TRUTH about your environment.
     Agents trust it over guesses: exact URLs, cluster names, conventions.
     The FF:ALWAYS block below is injected into EVERY session (keep it under
     ~25 short lines); everything else is indexed by section name and read
     on demand. Update it like code: review changes, keep facts current.
     Location options (resolution order):
       1. $FIREFLY_ENV_SPEC (env var; great for an org-wide mounted file)
       2. .firefly/config.json -> environment.spec_path
       3. FIREFLY-ENV.md at the repo root (committed, recommended)
       4. .firefly/environment.md (local, untracked)
     Manage with /ff:env. -->

<!-- FF:ALWAYS -->
- Org: REPLACE-ME | Airgapped: yes - the internet does NOT exist; use internal mirrors only
- GitLab: https://gitlab.REPLACE-ME.internal (CI runners on k3s; CI library: REPLACE-ME)
- Container registry: registry.REPLACE-ME.internal
- Artifact/package mirror: REPLACE-ME (pip/npm/go proxy)
- Docs (Kiwix/WikiAll): http://wikiall.REPLACE-ME.internal
- Clusters: dev=REPLACE-CTX | staging=REPLACE-CTX | prod=REPLACE-CTX (prod is READ-ONLY for agents)
- GitOps: Argo CD at https://argocd.REPLACE-ME.internal; promotions via Kargo
<!-- /FF:ALWAYS -->

## Clusters

| name | kube context | purpose | notes |
|---|---|---|---|
| dev | REPLACE | development | free to mutate with approval |
| staging | REPLACE | pre-prod validation | mutations need approval |
| prod | REPLACE | production | READ-ONLY for agents, always |

## Git and CI

- GitLab: https://gitlab.REPLACE-ME.internal - group structure: REPLACE
- CI library: REPLACE (how to include jobs, where templates live)
- Runners: k3s-hosted; tags: REPLACE

## Deployment and GitOps

- Argo CD apps live in: REPLACE (repo/path)
- Helm common library: REPLACE (registry/repo, how to consume)
- Kargo pipelines: REPLACE (stages, promotion policy)

## Observability

- Grafana: https://grafana.REPLACE-ME.internal (key dashboards: REPLACE)
- Logs/metrics stack: REPLACE
- SRE agent (HolmesGPT): REPLACE (how to invoke)

## Testing and QA

- QaaS framework: REPLACE (endpoint, how tests are triggered from CI)
- K8s test operators: REPLACE (CRDs, how to run component tests)

## Docs and knowledge

- Kiwix/WikiAll: http://wikiall.REPLACE-ME.internal (ZIM sets available: REPLACE)
- Internal product docs: REPLACE

## Dev environments

- Coder: https://coder.REPLACE-ME.internal (templates: REPLACE)

## MCP servers

- REPLACE: list the MCP servers available and what each is for

## Conventions

- Naming: REPLACE (namespaces, branches, chart names)
- Approvals: REPLACE (who signs off on prod changes)

## Escalation

- REPLACE: on-call/owners per area
