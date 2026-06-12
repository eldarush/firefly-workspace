---
description: View or change Firefly Workspace configuration - personas, guard policy, verifier, budgets
argument-hint: "[show | set <dotted.key> <value> | verify | protect]"
disable-model-invocation: true
---

Manage Firefly configuration: $ARGUMENTS

Config lives at `.firefly/config.json`; schema + defaults at
`${CLAUDE_PLUGIN_ROOT}/assets/config.schema.json`. Missing keys fall back to
built-in defaults - the file only needs overrides.

1. **`show`** (default): print the EFFECTIVE config (file merged over
   defaults), annotated: personas, behavior toggles (stop_gate, prompt_frame,
   lessons_injection, auto_allow_read, destroy, mutate_in_protected),
   protected globs, verify commands, lesson budgets, docs endpoints.

2. **`set <key> <value>`**: validate the key against the schema, show
   before/after, write the file. Safety rules:
   - changing `destroy` to "ask" or touching `protected.*`/`allow_extra` is a
     POLICY change: state the risk plainly and require explicit confirmation
   - never set `behavior.auto_allow_read` without explaining it auto-approves
     read-only shell commands on the user's behalf

3. **`verify`**: re-detect the project's verifier commands (Makefile,
   package.json, pyproject, go.mod, .gitlab-ci.yml) and update
   `verify.commands` after confirmation. The stop-gate depends on this.

4. **`protect`**: list current kube contexts (`kubectl config get-contexts`
   if available) and help the user mark the production-like ones into
   `protected.contexts` / `protected.namespaces` globs.

After any change, summarize what now behaves differently. Remind: config is
per-project, takes effect immediately (hooks re-read it every event), and
`.firefly/` is never committed.
