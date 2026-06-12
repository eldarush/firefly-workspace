---
description: Create, inspect, or update the environment spec - the source-of-truth file about your infra (URLs, clusters, registries, conventions)
argument-hint: "[show | edit | check | <fact to add/update>]"
disable-model-invocation: true
---

Manage the Firefly environment spec: $ARGUMENTS

The spec is the SINGLE SOURCE OF TRUTH about the org's environment. Its
FF:ALWAYS block is injected into every session; section names are indexed so
you read the rest on demand. Resolution order: $FIREFLY_ENV_SPEC env var ->
config `environment.spec_path` -> `FIREFLY-ENV.md` (repo root) ->
`.firefly/environment.md`.

1. **Locate**: find the active spec along the resolution order above. Report
   which path is active (or that none exists).

2. **If none exists - create**: ask whether it should be committed
   (`FIREFLY-ENV.md`, recommended for shared repos) or local
   (`.firefly/environment.md`). Copy
   `${CLAUDE_PLUGIN_ROOT}/assets/environment.template.md` there, then
   interview the user for the FF:ALWAYS facts FIRST (org name, GitLab URL,
   registry, docs/Kiwix URL, cluster contexts, GitOps endpoints) - replace
   every REPLACE-ME you have answers for, delete lines they say don't apply.
   Fill the detail sections only as far as the user wants right now; the rest
   can stay as placeholders.

3. **If it exists**:
   - `show` (default): print the FF:ALWAYS block verbatim and the section
     index; note any REPLACE/REPLACE-ME placeholders still unfilled.
   - `edit` or a concrete fact in the arguments: apply the smallest edit that
     records the fact in the right section (FF:ALWAYS only for facts needed in
     EVERY session). Show the diff.
   - `check`: validate structure - has FF:ALWAYS markers, pinned block under
     ~25 lines, has `## ` sections, no obviously stale placeholders. Estimate
     the pinned block's token cost (chars/3.5) vs the configured
     `environment.max_inject_tokens` budget (default 500) and warn if over.

4. **Hygiene reminders** (mention once): the spec is law for agents - never
   put secrets in it (it lands in every prompt); keep facts short and exact;
   review it like code. Changes take effect at the next session start.
