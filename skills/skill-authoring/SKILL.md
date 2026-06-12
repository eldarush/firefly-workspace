---
name: skill-authoring
description: Use when writing or reviewing a Claude Code skill - structure, frontmatter rules, token budgets, and the quality bar that separates useful skills from context pollution.
---

# Skill authoring

A skill is a contract: its description buys attention at match time; its body
must pay that attention back with executable knowledge. Bad skills are worse
than no skills - every description is always in context.

## Anatomy

```
skills/<name>/
  SKILL.md          # required; <= 200 lines
  references/*.md   # optional bulk detail, loaded only when followed
  scripts/*         # optional helpers, invoked via ${CLAUDE_SKILL_DIR}
```

Frontmatter:

```yaml
---
name: <kebab-case, must equal directory name, [a-z0-9-], <= 64 chars>
description: <= ~180 chars. THE most important line - see below.
# optional:
disable-model-invocation: true   # user-only workflow (slash command style)
argument-hint: "<what to pass>"
---
```

## The description decides everything

The model sees ONLY the description when choosing skills. Formula:
**"Use when <concrete trigger situations>"** + what it delivers. Name the
symptoms, tools, and contexts that should trigger it. Never write marketing
("Powerful helper for...") - write matching surface.

Bad:  `Helm utilities and best practices.`
Good: `Use when a helm upgrade/install fails or charts need validation -
covers template rendering, kubeconform checks, rollback, common chart traps.`

## Body rules

1. Imperative voice, numbered steps, real commands with placeholders.
2. Show expected output for key commands - the reader must know what success
   looks like.
3. Failure modes section: symptom -> cause -> fix table for the 3-5 ways this
   workflow actually goes wrong.
4. No filler ("it's important to note"), no theory the executor doesn't need.
5. Over 200 lines? Move bulk to `references/<topic>.md` and link it - the body
   keeps the workflow, references keep the encyclopedia.
6. RFC2119 keywords (MUST/SHOULD/NEVER) for the load-bearing rules.

## Quality gate before shipping

- [ ] name == directory, kebab-case
- [ ] description <= ~180 chars, starts with "Use when"
- [ ] a colleague could execute the steps without asking questions
- [ ] commands tested in this environment (airgapped: no public URLs!)
- [ ] failure modes documented from reality, not imagination
- [ ] no secrets, no policy weakening, no instructions to bypass guards

Route honestly: one fact -> CLAUDE.md or a playbook lesson; a role with tool
boundaries -> an agent; deterministic lifecycle logic -> a hook. A skill is
specifically a REUSABLE MULTI-STEP WORKFLOW.
