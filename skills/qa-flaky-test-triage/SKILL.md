---
name: qa-flaky-test-triage
description: Use when a test passes and fails intermittently, CI is red then green on rerun, or deciding whether to quarantine a test and under what conditions.
---
# QA Flaky Test Triage

## DOCTRINE

A rerun-pass does NOT clear the flake. It confirms nondeterminism.
Retries are evidence collection, not proof of health.
NEVER add `retry:` to a CI job or `@flaky` to a test as a "fix" -- it is deferral of a bug.
Every quarantine MUST have an owner, a reason, an expiry date, and a linked issue.

---

## Step 1 -- Gather History (R0)

Collect before touching any code:
- Last 20 CI run results for the test: pass/fail, timestamps, runner IDs.
- First commit where it appeared flaky: `git log --oneline -- <TEST_FILE>`.
- Environment correlation: which runner? time of day? parallel job count? container image version?

```bash
# check git history for the test file and the source file it exercises
git log --oneline -20 -- <TEST_FILE>
git log --oneline -20 -- <SOURCE_FILE>

# search CI artifact reports for the test name (adapt path to your report storage)
grep -r "<TEST_NAME>" <CI_REPORT_DIR> | awk '{print $1, $2}'
```

Failure rate >= 5% over 20 runs: flaky.
Failure rate < 1% over 100 runs: probably infrastructure noise; check runner health first.

---

## Step 2 -- Classify Root Cause

Work down this table; stop at the first category with supporting evidence.

| Category              | Symptoms                                                   | How to Confirm                                                         |
|-----------------------|------------------------------------------------------------|------------------------------------------------------------------------|
| Race / async          | Fails under load; passes when run alone; timing-sensitive assertion | Add timestamps to log; check for missing await or condition wait  |
| Order dependence      | Fails in full suite; passes in isolation                   | `pytest <file>::<test> -x` alone; then with full suite                 |
| Resource contention   | Fails on busy runners; passes on idle                      | Check runner CPU/mem metrics at the time of the failing run             |
| External dependency   | Network or registry error in job log                       | Inspect job log for DNS/connection failures (airgapped: registry mirror?) |
| Data nondeterminism   | Assertion fails on UUID, map key order, or timestamp value | Search test for uncontrolled `random`, `time.Now()`, map iteration in assertion |
| Genuine product race  | Flake reproduces in production metrics too                 | ESCALATE -- this is a real bug, not a test problem; open a bug issue   |

---

## Step 3 -- Reproduce

```bash
# run the single test N=20 times; stop on first failure to capture state
for i in $(seq 1 20); do
  echo "=== Run $i ==="
  pytest <PATH>::<TEST_NAME> -x -s 2>&1 | tail -20
done

# run without random ordering to isolate order dependence
pytest <PATH>::<TEST_NAME> -p no:randomly -x

# run the full suite to check if it only fails in context
pytest <SUITE_PATH> -x --tb=short
```

Containerized reproduction (for environment failures -- use the same image as the CI job):
```bash
docker run --rm -it <JOB_IMAGE> bash
# paste test commands verbatim inside the container
```

---

## Step 4 -- Fix at the Cause

| Root Cause              | Fix                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------|
| Missing async wait      | Replace `time.sleep(N)` with a condition poll or event.wait() with timeout          |
| Shared mutable state    | Add per-test setup/teardown; use test-scoped fixtures                               |
| Clock nondeterminism    | Freeze clock with freezegun or faketime; use a fixed timestamp in test data         |
| RNG nondeterminism      | Seed the RNG explicitly in test setup                                               |
| Registry / network      | Pre-pull images in CI setup stage; do not pull at test runtime (airgapped runners)  |
| Genuine product race    | Fix in the product code; the test is correct; open a separate bug issue             |

Fix goes through MR. Do not push directly to the test suite.

---

## Step 5 -- Quarantine (last resort, strict conditions)

MUST have ALL of the following before adding a quarantine annotation:
- [ ] Owner named (team or individual responsible for the fix).
- [ ] Root cause category documented (even if unconfirmed: "suspected async race in scheduler").
- [ ] Linked issue with acceptance criteria for the fix.
- [ ] Expiry date (MUST be set; default: next sprint end date).
- [ ] Release-risk note: state what behavior this test covers and the risk of skipping it in a release.

```python
@pytest.mark.skip(
    reason="Flaky: suspected async race. Issue: #123. Owner: qa-team. "
           "Expires: 2025-09-12. Risk: covers HTTP retry idempotency."
)
def test_example():
    ...
```

Quarantine without expiry = deletion with extra steps. MUST rule: review all quarantined tests at expiry.
NEVER quarantine a test that covers a security or data-integrity path without explicit lead approval.

---

## Step 6 -- Track Flake Debt

- Maintain a count of quarantined tests per suite (CI can emit a warning metric).
- Alert (CI warning, not failure) when quarantined count exceeds threshold (suggested: 3 per suite).
- Review the quarantine list at each sprint retrospective.
- A growing quarantine list is a quality signal; escalate to the engineering lead when trend is upward.