# Airgap Release Guide

## Release Artifact

A production Firefly Workspace release should contain:

- this Claude Code marketplace repository;
- plugin cache or seed directory;
- signed policy bundle;
- approved MCP catalog and tool schema hashes;
- offline docs snapshots;
- package mirrors or wheelhouses;
- OCI images or image archives;
- SBOMs and vulnerability reports;
- in-toto/SLSA provenance;
- install lockfile with digests.

## Build Steps

1. Tag the repository.
2. Run unit and structure tests.
3. Run `claude plugin validate .` if Claude Code is available.
4. Generate SBOM and vulnerability report with your internal tooling.
5. Sign the release bundle and policy bundle.
6. Export artifacts through the approved transfer process.

## Import Steps

1. Import the signed bundle.
2. Verify signatures and digests.
3. Install or seed the marketplace.
4. Configure managed settings to allow only approved marketplaces, MCP servers, hooks, and permissions.
5. Run no-egress validation:

```bash
python -m unittest discover -s tests -v
claude plugin validate .
```

6. Start Claude Code and verify `/firefly-workspace:architect` appears.

## Managed Settings Sketch

```json
{
  "enabledPlugins": {
    "firefly-workspace@fireflyteam": true
  },
  "permissions": {
    "deny": [
      "Read(//**/.env*)",
      "Read(//**/.ssh/**)",
      "Bash(curl *|*sh*)",
      "Bash(wget *|*sh*)",
      "Bash(rm -rf *)",
      "Bash(terraform apply*)",
      "Bash(terraform destroy*)",
      "Bash(git push --force*)"
    ],
    "ask": [
      "Bash(kubectl *)",
      "Bash(helm upgrade *)",
      "Bash(docker push *)"
    ]
  },
  "env": {
    "DISABLE_AUTOUPDATER": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_LOGS_EXPORTER": "otlp"
  }
}
```

Treat this as a starting point; exact managed-setting keys and policy support should be validated against the Claude Code version deployed in your environment.

## Rollback

Keep:

- previous signed marketplace tag;
- previous signed policy bundle;
- emergency managed settings that disable write MCP tools;
- known-good plugin seed directory.

Rollback should be tested before each promotion.
