---
name: dev-ci-debugging
description: Use when a GitLab pipeline is red, a job fails in CI but works locally, k3s runners are misbehaving, or a custom CI library job fails unexpectedly.
---
# Dev CI Debugging

## Step 1 -- Read the Job Log (R0)

Open the failing job. Read BOTTOM-UP first:
- The final `exit code N` or `ERROR` line is almost always a cascade.
- Scroll UP to the FIRST red or unexpected line -- that is the real error.

Identify the failing stage to narrow the cause:

| Stage               | Typical real error                                             |
|---------------------|----------------------------------------------------------------|
| compile / build     | Syntax error, missing dependency, wrong tool version           |
| test                | Test assertion failure or test harness crash                   |
| lint / format       | Style violation (fix in code, not in CI config)                |
| package / push      | Registry auth failure, image tag conflict                      |
| deploy              | k8s / helm / ArgoCD failure -- go to sre-gitops-operations     |

---

## Step 2 -- Classify: Code Failure vs Environment Failure

Run the same steps locally first. If it fails locally too: fix the code, not CI.

| Failure Type       | Symptoms                                             | Action                                              |
|--------------------|------------------------------------------------------|-----------------------------------------------------|
| Code failure       | Fails locally with the same steps                    | Fix the code; CI is working correctly               |
| Environment failure| Passes locally; fails in CI                          | Diff the environments (see checklist below)         |
| Flaky test         | Passes on rerun without code change                  | Go to qa-flaky-test-triage; NEVER add retry without root cause |
| Auth failure       | 401, 403, token error in log                         | Check CI variable scope (protected branch? fork?)   |
| Network failure    | DNS error, connection refused, pull timeout          | Check registry mirror config; airgapped k3s runners have no public internet |

### Environment Diff Checklist (for env failures)

```bash
# 1. What image does the job use? Find in .gitlab-ci.yml or CI library job definition
image: <JOB_IMAGE>

# 2. What tool versions does that image contain?
docker run --rm <INTERNAL_REGISTRY>/<JOB_IMAGE>:<TAG> <tool> --version

# 3. What env vars does the job need? Are they set?
#    Check .gitlab-ci.yml variables: section and CI library job documentation.
#    Protected variables are not injected on feature branches or forks.

# 4. Are runner cache or artifacts from a previous job stale?
#    Clear the runner cache for this project in GitLab CI/CD settings.
```

---

## Step 3 -- Reproduce Locally with the Same Image

```bash
# pull from the internal registry (no public registry on airgapped runners)
docker pull <INTERNAL_REGISTRY>/<JOB_IMAGE>:<TAG>

# run interactively
docker run --rm -it <INTERNAL_REGISTRY>/<JOB_IMAGE>:<TAG> bash

# inside: paste the script steps from the job log verbatim
```

If `gitlab-ci-local` is available in the dev environment:
```bash
gitlab-ci-local --job <JOB_NAME>
```

---

## Step 4 -- Airgapped k3s Runner Specifics

k3s runners have NO public internet. Common failure patterns:

| Symptom                              | Cause                                       | Fix                                                     |
|--------------------------------------|---------------------------------------------|---------------------------------------------------------|
| pull access denied / image not found | Image pulled from public hub                | Update image ref to internal registry mirror in CI config |
| npm install / pip install fails      | Public registry unreachable                 | Configure internal Nexus/Artifactory mirror; check proxy env vars |
| go get fails                         | GOPROXY not pointing to internal proxy      | Set GOPROXY=<INTERNAL_GOPROXY> in CI variables          |
| DNS resolution failure               | CoreDNS misconfiguration in k3s             | Escalate to SRE; do not attempt to fix DNS in job config |
| curl to external URL fails           | Airgapped by design; expected behavior      | Use Kiwix/WikiAll for docs; use internal API endpoints only |

---

## Step 5 -- Custom CI Library Jobs

```yaml
# Find the pinned library ref in .gitlab-ci.yml
include:
  - project: '<CI_LIBRARY_REPO>'
    ref: '<REF>'
    file: '<JOB_FILE>'
```

1. Check out that exact ref of the CI library repo.
2. Read the job definition: required variables, expected input artifacts, script logic, tags.
3. Verify all required variables are configured in the project's CI/CD variable settings.
4. If the library job itself is incorrect: open an MR against the CI library repo (R2, needs library owners' approval).

---

## Step 6 -- Fix in the Right Layer

| Root Cause                | Fix Layer                              | Risk Class                          |
|---------------------------|----------------------------------------|-------------------------------------|
| Code bug                  | Application source                     | R1 -- local edit, then MR           |
| Wrong tool version in image | Dockerfile for the job container image | R1 -> R2 MR to image repo          |
| Missing CI variable       | GitLab project CI/CD settings          | R2 -- needs project maintainer      |
| .gitlab-ci.yml change     | MR to the application repo             | R2                                  |
| CI library job bug        | MR to CI library repo                  | R2 -- library owners must approve   |
| Runner resource limits    | k3s runner node or pod resource config | R3 -- SRE approval required         |

Risk classes: R0 read-only / R1 local edits+tests / R2 shared CI-config / R3 cluster-deploy-secrets / R4 destructive-irreversible (denied).

---

## Failure Table

| Symptom                            | Likely Cause                                       | First Check                                           |
|------------------------------------|----------------------------------------------------|-------------------------------------------------------|
| Works locally, fails in CI         | Uncommitted file; dirty workspace; version skew    | git status; compare tool versions with docker run     |
| exit 137 in CI job container       | OOM in runner container                            | Check k3s runner resource limits; reduce test parallelism |
| Protected variable not injected    | Feature branch or fork scope restriction           | Set variable as non-protected if safe to do so        |
| DAG job never starts               | Upstream needs: job failed or was skipped          | Check status of all dependency jobs in the pipeline   |
| Job stuck at pending               | No runner with matching tags available             | Check tags: in job definition vs registered runner tags |

NEVER fix a failing test by adding `retry: 2` to the CI job without identifying the root cause.
NEVER add `allow_failure: true` without a linked issue and a documented expiry plan.