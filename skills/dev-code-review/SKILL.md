---
name: dev-code-review
description: Use when reviewing an MR diff, performing a pre-merge review, or evaluating AI-generated code before it lands. Covers correctness, tests, design, and style.
---
# Dev Code Review

## Before Reading the Diff

1. Read the linked issue or task description.
2. Read the MR description -- does it match the task?
3. A technically perfect diff for the wrong task is a FAIL.
4. Note the files changed -- large scope creep is its own finding.

---

## Severity-Ordered Review Pass

Work in this exact order. File a BLOCKER immediately; do not continue to the next pass.

### Pass 1 -- Correctness

**Edge cases**
- Empty input, nil/null pointer, zero value, negative number, empty collection.
- Unicode and encoding boundaries (are strings decoded before length checks?).
- Timezone and clock: any `time.Now()` in business logic or test assertions? DST-safe?

**Error paths**
- What happens when this call fails? Is the error propagated, wrapped with context, or silently swallowed?
- Any new code path that can panic or throw an unchecked exception?
- Are all return values (including errors) consumed?

**Concurrency**
- Shared mutable state accessed from multiple goroutines or threads without synchronization?
- Is the new operation idempotent? (Critical for k8s operators and retry logic.)
- Any new global or package-level state introduced?

**Security**
- New endpoint or action: is authorization checked before data is accessed or mutated?
- User-controlled input reaches a SQL query, shell command, or template without sanitization?
- Secrets, tokens, or PII in code, log lines, or error messages?

### Pass 2 -- Tests

- Do the tests assert BEHAVIOR, not implementation? (A test that calls a function and only checks no error was returned is not a behavioral test.)
- Would the tests catch a bug-shaped mutation of this diff? (off-by-one, wrong HTTP method, missing nil check)
- Is the error path identified in Pass 1 tested?
- Missing tests for normal paths: SHOULD finding. Missing tests for security or data-integrity paths: BLOCKER.

### Pass 3 -- Design

- Does the code follow existing patterns in the codebase? When flagging a deviation, cite the neighboring file and line number.
- Is the public surface minimal? Exported symbols that do not need to be exported weaken encapsulation.
- Will a new team member understand this in 6 months without the MR context?
- Does it introduce unnecessary coupling or hidden dependencies (implicit global state, init() side effects)?

### Pass 4 -- Style (LAST; only if no linter enforces it)

- Flag style issues only if the repo linter does not already catch them.
- Style findings MUST be "nit" severity -- never block an MR on style alone.

---

## Finding Format

```
<file>:<line>  [BLOCKER|SHOULD|NIT]  <what> -- <why> -- <concrete suggestion>
```

Examples:
```
src/client.go:47   [BLOCKER]  error from Dial() is discarded -- if the connection fails the next line panics -- return err or handle explicitly
src/client.go:82   [SHOULD]   no test for 503 response path -- the retry logic added here is not exercised -- add a table-driven case for 503
src/handler.go:12  [NIT]      variable 'x' is unclear -- rename to 'retryCount' (linter does not enforce naming here)
```

---

## Calibration Rules

- Surface only findings that MATTER. If you cannot articulate the failure mode, it is not a blocker.
- If the diff is correct and well-tested: say **PASS** plainly. Manufactured nitpicks erode trust.
- NEVER approve an MR with unresolved BLOCKER findings.
- Partial approval ("LGTM except for X") is acceptable -- make the condition explicit.

---

## Reviewing AI-Generated Diffs

Apply the same bar as human code, plus these additional checks:

1. **API existence**: AI models hallucinate method names and signatures. Verify every called function exists in the actual library version pinned in the project.
2. **Tests actually run**: AI often generates test files with syntax errors or missing imports. Do not approve until a CI run confirms the tests execute and pass.
3. **Silent scope creep**: AI tends to "improve" adjacent code that was not in scope. Audit every changed line against the task description.
4. **Plausible-but-wrong logic**: The code may look correct and be subtly off (wrong operator precedence, off-by-one, wrong HTTP status code, wrong unit). Read AI-generated code more slowly than human code.
5. **Generated test quality**: Check that assertions in AI-generated tests are not vacuously true (assert True, assert result is not None with no further checks).

---

## Review Checklist (quick reference)

- [ ] Diff matches the task description
- [ ] No unchecked errors on new code paths
- [ ] No secrets, tokens, or PII in code or logs
- [ ] New endpoints/actions have authorization checks
- [ ] Tests assert behavior and cover error paths
- [ ] No unsafe shared mutable state introduced
- [ ] Design consistent with existing codebase patterns
- [ ] For AI-generated code: APIs verified, tests confirmed to execute in CI