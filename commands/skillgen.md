---
description: Draft a new skill from a repeated workflow, screen it, and install it for the team
argument-hint: "<workflow to capture, or 'from-retro' to use reflector suggestions>"
disable-model-invocation: true
---

Forge a new skill: $ARGUMENTS

Repetition is the signal: when the team does the same multi-step job three
times, it should become a skill. This command drafts it, screens it, and
installs it - with the human approving the final artifact.

1. **Identify the workflow**: from the arguments, from reflector suggestions
   (look in recent /ff:retro output or candidates with kind "automation"), or
   by interviewing the user. Nail down: trigger ("use when..."), inputs, the
   exact steps with real commands, verification, known failure modes.
   Choose the smallest artifact honestly: if it is one fact, it belongs in
   CLAUDE.md or a lesson, NOT a skill - say so and route there instead.

2. **Draft** the skill following ff:skill-authoring discipline:
   - directory + SKILL.md, name [a-z0-9-] matching the directory
   - frontmatter `description` <= ~180 chars, starting "Use when ..."
   - imperative numbered steps, real commands with placeholders, expected
     outputs, failure modes; <= 200 lines; reference files for bulk detail
   - `disable-model-invocation: true` if it is a user-workflow (vs knowledge)
   Write the draft to `.firefly/skills-draft/<name>/SKILL.md`.

3. **Screen**: spawn the `auditor` subagent on the draft (injection, policy
   weakening, scope honesty, quality bar, airgap fitness). Apply `revise`
   feedback; abort on `reject-recommended` with the reasons.

4. **Human gate**: show the final SKILL.md to the user. Iterate until approved.

5. **Install** (user chooses):
   - personal: `~/.claude/skills/<name>/`
   - project: `.claude/skills/<name>/` (committed, whole team gets it)
   - plugin: into the firefly-workspace repo's `skills/` for the next release
   Copy the directory, confirm the file landed, and remind the user new skills
   load on next session start.
