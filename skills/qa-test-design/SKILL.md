---
name: qa-test-design
description: Use when designing tests for a new feature or change, building a test matrix, deciding what to automate, or planning QaaS test cases for a sprint.
---
# QA Test Design

## Step 1 -- Risk-Based Scope: What Changed and What Can Break

Before writing any test, enumerate:
1. The code or config that CHANGED (diff + list of dependent modules).
2. The behaviors that DEPEND on it (callers, consumers, SLOs at risk).
3. The error paths: what happens when the changed code fails?
4. Pre-existing tests: do not re-test what is already covered unless the change broke that assumption.

Test the CONTRACT (observable behavior), not the implementation (internals).
A test that mirrors implementation details passes through refactors and misses real regressions.

---

## Step 2 -- Test Matrix Dimensions

| Layer          | What it covers                                | When to add                              | When to skip                              |
|----------------|-----------------------------------------------|------------------------------------------|-------------------------------------------|
| Unit           | Pure logic, algorithms, edge cases            | Always for non-trivial functions         | Trivial getters/setters                   |
| Integration    | Component seams, DB round-trips, API wiring   | When unit tests cannot cover the join    | Already covered by e2e                    |
| Contract       | API schema, message shapes, protocol rules    | Any service boundary (internal or Flink) | Internal-only types with no external consumers |
| E2E            | Critical user paths end-to-end                | Top 3-5 user journeys only               | Happy-path duplicates of integration tests |
| Property-based | Parsers, codecs, math invariants, serialization | When input space is too large to enumerate | Simple deterministic one-to-one transforms |
| Regression     | Every fixed bug                               | Always -- pin the exact failure condition | Never skip                                |

---

## Step 3 -- Test Quality Rules

Each test MUST:
- Assert one behavior (one conceptual outcome per test function).
- Have a name that reads as a spec: `test_retry_skips_4xx_responses`.
- Follow Arrange-Act-Assert with no branching logic inside Assert.
- Fail BEFORE the fix and pass AFTER (verify this for bug regression tests).

NEVER:
- Assert implementation details (private method called, internal log line emitted unless it IS the contract).
- Use production data or uncontrolled external state (no live cluster state in unit tests).
- Share mutable state between tests without explicit per-test setup and teardown.
- Write a test that asserts nothing (a test that always passes is a false certificate).

---

## Step 4 -- Test Data Strategy

- Use builders or factories, not static fixtures: `RequestBuilder().with_timeout(0).build()`.
- Minimum data: only the fields that exercise the specific code path under test.
- Freeze time (`freezegun`, `faketime`) and seed randomness explicitly for determinism.
- For k8s operator tests: use `envtest` or a dedicated test namespace with cleanup; never use production namespaces.
- For Flink operator tests: use the QaaS framework's test harness with isolated job namespaces.

---

## Step 5 -- What NOT to Automate

| Category                            | Why to skip                                 | Alternative                                |
|-------------------------------------|---------------------------------------------|--------------------------------------------|
| One-off exploratory checks          | Maintenance cost exceeds value              | Document findings in an ADR                |
| UI pixel-perfect comparisons        | Brittle without dedicated visual tooling    | Manual visual review gate in the MR        |
| Tests requiring production data     | Security, privacy, nondeterminism           | Build anonymized fixture data              |
| Tests slower than the decision cycle| Feedback loop broken; devs skip them        | Move to nightly or scheduled pipeline      |

---

## Step 6 -- Coverage Honesty

Coverage % is a search-light, not a goal.
- 80% coverage with weak assertions is worse than 50% with behavioral assertions.
- Uncovered error paths are where incidents live -- actively hunt them.
- Use coverage output to find gaps in CHANGED files, not to chase a repo-wide number.

```bash
# run with coverage and inspect changed files only
<TEST_RUNNER> --coverage -- <CHANGED_PACKAGE>
# review uncovered branches in the diff
```

---

## Step 7 -- QaaS Framework Integration

When writing tests using the QaaS framework:
- Express intent as declarative test specs where the framework supports it.
- Assign runner labels to control shard placement (heavy integration tests -> dedicated runner label).
- Declare artifact capture per run: logs, JUnit XML, coverage reports, screenshots.
- Tests are code: they go through MR review at the same bar as production code.

```yaml
# Illustrative QaaS test declaration
name: http-client-retry-on-503
runner_labels: [integration, medium]
artifacts: [junit, coverage]
tags: [retry, http-client]
```

---

## Worked Example: "Add Retry Logic to HTTP Client"

| Test                                        | Layer       | What it checks                                     | Pass condition                                             |
|---------------------------------------------|-------------|----------------------------------------------------|------------------------------------------------------------|
| test_backoff_doubles_each_attempt           | Unit        | Backoff math: 1s, 2s, 4s                           | Computed delays match exponential formula exactly          |
| test_retry_fires_on_503_not_400             | Integration | Retry only on retryable status codes               | Mock server: 503 retried 3x; 400 not retried at all        |
| test_idempotency_header_set_on_retry        | Contract    | Idempotency-Key header present on all retry attempts | Header present and same value across all retry requests  |
| test_no_retry_on_non_idempotent_post        | Unit        | POST without idempotency key: no retry             | Exactly one request sent, no retry loop entered            |
| test_original_timeout_regression            | Regression  | Original timeout bug does not recur               | Request with 1ms timeout fails fast with TimeoutError, no hang |