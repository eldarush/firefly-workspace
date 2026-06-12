---
name: tdd
description: Use when implementing behavior changes, bug fixes, or new features in code that has or should have tests.
---
# Test-Driven Development

## Red-Green-Refactor (one behavior per cycle)

1. **Write the failing test.** One behavior. Run it. It MUST fail.
   - If it passes immediately: you misunderstood the task or the behavior already exists. Stop. Clarify.
   - If it fails for the WRONG reason (wrong error message, wrong assertion): fix the test first.
2. **Write the minimal code to make it pass.** No extras. Run. Must be GREEN.
3. **Refactor on green only.** Extract, rename, simplify. Run after each change. Stay green.
4. **Repeat** for the next behavior.

## Bug Fix Protocol

MUST reproduce the bug with a failing test BEFORE touching production code.
The test IS the repro. If you cannot write a test that fails, you do not yet understand the bug.

```
# Workflow
git checkout -b fix/<ticket>
# Write test that reproduces the bug - run it - confirm it FAILS
# Fix the code - run the test - confirm it PASSES
# Run the full suite - confirm no regression
git commit -m "fix: <description>\n\nTest added: <test name>"
```

## When Tests Do Not Exist

Write characterization tests first:
1. Run the code with known inputs; capture current outputs (even if wrong).
2. Write tests that assert the CURRENT behavior.
3. Run suite - all green.
4. Now change the behavior via TDD. Characterization tests catch regressions.

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Test passes immediately after writing | Wrong assertion, or feature already exists | Read the assertion. Check if feature was already implemented. |
| Test asserts implementation detail (method called) | Testing the wrong layer | Assert observable behavior: output, state, side-effect |
| Every dependency mocked | Testing nothing real | Only mock at process boundaries (network, disk, time) |
| One test covers 10 behaviors | Fear of test count | Split: one `it/test` per behavior. Parameterize if inputs vary. |
| Deleted failing assertion to get green | Pressure to show progress | NEVER. Requires explicit human approval with written reason. |
| Slow test suite ignored | Tests not running in CI | Fix speed first (parallelize, use fake clocks). A suite no one runs is worthless. |

## Rules

- MUST run the test and see it fail BEFORE writing implementation code.
- NEVER weaken or delete a failing assertion without explicit human approval.
- NEVER refactor on red; wait for green.
- Each test cycle MUST cover exactly one behavior.
- SHOULD commit after each green (checkpoint).
