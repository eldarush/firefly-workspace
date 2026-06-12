# Airgapped install & rollout

Firefly Workspace is designed to run with **zero network access**: Python
stdlib hooks, no external services, no telemetry. The only network-shaped task
is getting the repo inside your perimeter.

## 1. Mirror the repo

On the connected side:

```bash
git clone --mirror https://github.com/eldarush/firefly-workspace
# pin the release you reviewed:
git -C firefly-workspace.git tag --list   # use v1.x.y tags
```

Transfer per your approved process (signed bundle, data diode, sneakernet),
then push to your internal Git:

```bash
git -C firefly-workspace.git push --mirror https://gitlab.internal/platform/firefly-workspace
```

Treat upgrades as releases: pin by tag + commit SHA, diff-review before
import, keep the previous tag available for rollback.

## 2. Install per user

```text
/plugin marketplace add https://gitlab.internal/platform/firefly-workspace
/plugin install ff@firefly-workspace
```

A local filesystem path also works (useful on shared dev images):

```text
/plugin marketplace add /opt/claude/firefly-workspace
```

Set this environment variable on every machine (CI images, Coder templates):

```bash
export CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1
```

Without it, a failed `git pull` against an unreachable origin can wipe the
marketplace cache on startup.

## 3. Team-wide rollout (managed settings)

Drop into the project's `.claude/settings.json` (committed) or your managed
settings layer so every engineer gets the plugin without manual steps:

```json
{
  "extraKnownMarketplaces": {
    "firefly-workspace": {
      "source": {
        "source": "git",
        "url": "https://gitlab.internal/platform/firefly-workspace"
      }
    }
  },
  "enabledPlugins": {
    "ff@firefly-workspace": true
  }
}
```

Optionally add defense-in-depth permission rules at the same layer (these
complement the plugin's guard hook - the guard is policy-aware, these are
blunt):

```json
{
  "permissions": {
    "deny": [
      "Read(//**/.ssh/**)",
      "Read(//**/.env*)"
    ]
  }
}
```

## 4. Model backend notes (single offline model)

With one model (e.g. MiniMax M2.7 behind an Anthropic-compatible gateway):

```bash
export ANTHROPIC_BASE_URL=https://llm-gateway.internal
export ANTHROPIC_AUTH_TOKEN=<internal>
export ANTHROPIC_DEFAULT_SONNET_MODEL=<model-id>
export ANTHROPIC_DEFAULT_OPUS_MODEL=<model-id>
export ANTHROPIC_DEFAULT_HAIKU_MODEL=<model-id>
```

All plugin agents declare `model: inherit`, so everything runs on your one
model. **Gateway requirement**: the proxy MUST pass through interleaved
thinking blocks unmodified - stripping them visibly degrades output quality on
M2-class models. Verify with one long agentic session before rollout.

## 5. Per-project setup

In each repository:

```text
/ff:init
```

This creates `.firefly/config.json` (verifier commands, protected
contexts/namespaces, personas), appends the behavior contract to `CLAUDE.md`
(commit it - subagents read CLAUDE.md too), and leaves `.firefly/` self-ignored.

## 6. Release checklist (for the platform team)

Before promoting a new plugin version internally:

- [ ] `python3 tests/run_tests.py` green on a Linux container
- [ ] `claude plugin validate .` green (where claude CLI exists)
- [ ] diff-review of `scripts/` and `hooks/hooks.json` since last tag
      (these execute on every machine)
- [ ] version bumped in `.claude-plugin/plugin.json` + `marketplace.json`,
      CHANGELOG updated, git tag created
- [ ] previous tag verified still installable (rollback path)
- [ ] announce: what changed, what new lessons/skills shipped

## 7. Verify the install

```text
/ff:onboard          # should respond with the tour
/ff:config show      # should print effective config
```

Then check `.firefly/` appears in the project after the first session and
`bash`-deny works: ask Claude to run `kubectl delete ns test` - the guard must
refuse with an explanation.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `/ff:*` commands missing | plugin not enabled | `/plugin` -> enable ff; check enabledPlugins key spelling |
| hooks never fire | `python3` not on PATH | install python3 / add shim; hooks fail open so sessions still work |
| marketplace gone after restart | startup git pull failed | set `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` |
| lessons never injected | `.firefly/` missing | run `/ff:init`; check `behavior.lessons_injection` |
| guard blocks a legit command | classification too broad | add a scoped regex to `allow_extra` in `.firefly/config.json`; the audit.log shows the matched rule |
