---
description: Set up Firefly Workspace in this project - config, CLAUDE.md contract, verifier detection
argument-hint: "[persona: sre|qa|dev|research]"
disable-model-invocation: true
---

Initialize Firefly Workspace in the current project. Persona argument (may be empty): $ARGUMENTS

Follow these steps exactly:

1. **Detect state**: check whether `.firefly/config.json` and a `CLAUDE.md` with
   `<!-- FIREFLY:BEGIN -->` markers already exist. If both exist, report
   "already initialized", show the current config summary, and stop.

2. **Create config**: copy `${CLAUDE_PLUGIN_ROOT}/assets/config.example.json`
   to `.firefly/config.json` (create the directory if needed) unless it exists.
   Set `personas` from the argument if given, else infer from the repo
   (helm charts/k8s manifests -> sre, test framework-heavy -> qa, default dev)
   and confirm the guess with the user.

3. **Detect the verifier**: inspect the repo (Makefile, package.json scripts,
   pyproject/tox, go.mod, .gitlab-ci.yml, *.csproj) and propose the project's
   canonical test/lint commands. Write the confirmed ones into config
   `verify.commands`. This powers the verification stop-gate - explain that in
   one sentence.

4. **Install the contract**: append the full contents of
   `${CLAUDE_PLUGIN_ROOT}/assets/CLAUDE.snippet.md` to the project's `CLAUDE.md`
   (create the file if missing). If markers already exist, replace the block
   between them instead of duplicating.

5. **Protect production**: show the default `protected.contexts/namespaces`
   globs from config and ask the user to name their real production
   contexts/namespaces. Update config accordingly.

6. **Environment spec**: check for an env spec along the resolution order
   ($FIREFLY_ENV_SPEC, config `environment.spec_path`, `FIREFLY-ENV.md`,
   `.firefly/environment.md`). If none exists, explain in one sentence that
   the spec is the source-of-truth file for org URLs/clusters that gets
   injected into every session, and offer to create it now via /ff:env
   (skippable - everything works without it).

7. **Report**: summarize what was created, then suggest the next steps:
   `/ff:onboard` for a tour, `/ff:plan <task>` to start working.

Do NOT commit anything. `.firefly/` keeps a self-ignoring .gitignore; only
CLAUDE.md belongs in version control - tell the user to commit it.
