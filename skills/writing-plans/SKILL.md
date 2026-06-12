---
name: writing-plans
description: Use when writing or reviewing an implementation plan for multi-file or risky work before execution starts.
---
# Writing Plans

A plan is for EXECUTION by a possibly-fresh context. It must be self-contained.

## Plan Structure (required sections)

1. **Goal** - one sentence, observable outcome.
2. **Acceptance Criteria** - bullet list, each criterion independently testable. No vague words ("works", "better").
3. **Files to Touch** - table: file path | change type (add/modify/delete) | what changes and why.
4. **Steps** - numbered, dependency-ordered, each <= ~30 min of work.
   - Each step: what to do + exact verifier command + expected output.
5. **Final Verifier** - the single command that confirms all criteria met.
6. **Risks and Mitigations** - table: risk | likelihood | mitigation.
7. **Non-Goals** - explicit list of what this plan does NOT do.

Template: `${CLAUDE_PLUGIN_ROOT}/assets/templates/plan.md`

## Quality Gates (check before handing plan to executor)

- [ ] Every acceptance criterion is testable by running a command or reading a file - no subjective criteria.
- [ ] Steps are ordered by dependency - no step requires output from a later step.
- [ ] A colleague could execute this plan without asking a question.
- [ ] No step is bigger than ~30 min (if so, split it).
- [ ] Each step has its own verifier command, not just the final.
- [ ] Non-goals prevent scope creep during execution.

## Files-to-Touch Table Template

| File | Change Type | Notes |
|------|-------------|-------|
| `src/cmd/root.go` | modify | add `--timeout` flag, wire to config struct |
| `src/config/config.go` | modify | add Timeout field, default 30s |
| `config/default.yaml` | modify | add `timeout: 30` |
| `src/cmd/root_test.go` | modify | add test for flag parsing |
| `docs/cli.md` | modify | document new flag |

## Micro-Example: Adding a CLI Flag

```
Goal: Add --timeout flag to the CLI with a 30s default.

Criteria:
- `./bin/app --timeout 5` runs without error
- `./bin/app --timeout abc` exits non-zero with a useful message
- Unit test for flag parsing passes

Steps:
1. Add Timeout field to config struct
   Verify: `go build ./...` exits 0
2. Register --timeout flag in root command
   Verify: `./bin/app --help | grep timeout`
3. Add unit test for valid and invalid input
   Verify: `go test ./src/cmd/... -run TestTimeout` RED first, then GREEN
4. Document flag in docs/cli.md
   Verify: `grep '\-\-timeout' docs/cli.md`

Final: go test ./... && ./bin/app --timeout 5

Risks: flag name collision with existing flags | low | grep codebase first
Non-goals: persist timeout to config file
```

## Rules

- MUST write the plan before touching code on any multi-file or risky change.
- NEVER include a step without a verifier command.
- MUST list non-goals to prevent scope creep.
- Plans are living documents - update them when steps change, do not execute a stale plan silently.
