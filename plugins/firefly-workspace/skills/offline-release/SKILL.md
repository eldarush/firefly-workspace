---
description: Use when packaging Firefly Workspace, MCP servers, docs, policies, skills, dependencies, or models for airgapped/offline distribution.
---

Create an airgapped workspace release plan for $ARGUMENTS.

## Release Contents

Include:

- Claude Code marketplace/plugin bundle;
- approved skills, agents, hooks, policies, schemas, evals;
- MCP server catalog with fingerprints and tool schemas;
- offline docs snapshots with source URLs, versions, and hashes;
- package mirrors or wheelhouses;
- OCI images or image archives;
- SBOMs, vulnerability reports, license reports;
- signatures, attestations, and install lockfile.

## Workflow

1. Pin every artifact by version and digest.
2. Build in a connected staging environment.
3. Scan, sign, and attest.
4. Test install with public network disabled.
5. Import into the airgap through the approved transfer path.
6. Verify seed directories, local marketplace, internal registries, and no-egress operation.
7. Document rollback to the previous signed release.

## Output

Return:

- `Release manifest`
- `Artifact sources`
- `Security gates`
- `Install steps`
- `No-egress verification`
- `Rollback plan`
