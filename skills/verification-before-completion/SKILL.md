---
name: verification-before-completion
description: Use when about to claim a task is done, tests pass, or a fix works - defines what counts as evidence of completion.
---
# Verification Before Completion

**"Should work" is a confession, not a status. Replace it with evidence or with "unverified because X".**

## Evidence Hierarchy (strongest first)

1. Test / CI output - paste real output, trimmed to signal.
2. Type-check / lint / static analysis output.
3. Rendered manifests / dry-runs / diffs (`helm template`, `kubectl --dry-run=server`, `terraform plan`).
4. Logs or metrics from a running system.
5. Manual reasoning - weakest; always label as such.

Downgrade your claim to match the evidence you actually have.

## Claims-to-Evidence Mapping

Before saying "done", list every claim and attach evidence:

| Claim | Evidence Type | Command Run | Output (trimmed) | Status |
|---|---|---|---|---|
| Tests pass | Test output | `go test ./...` | `ok all packages` | PASSED |
| No lint errors | Lint output | `golangci-lint run` | `(empty)` | PASSED |
| CLI flag works | Manual + test | `./bin/app --timeout 5` | exit 0 | PASSED |
| Docs updated | Diff review | `git diff docs/` | shows new section | PASSED |

## Completion Checklist

- [ ] Verifier run AFTER the last edit (not before - re-run it).
- [ ] New files included in build / committed.
- [ ] Diff reviewed hunk-by-hunk (`git diff HEAD` or `git diff --staged`).
- [ ] Every acceptance criterion from the plan checked individually.
- [ ] No TODO / FIXME left in changed files (unless intentional and noted).
- [ ] For infra changes: `helm template | kubeconform`, `kubectl --dry-run=server`, or `terraform plan` run and output reviewed.

## Infra Verification Commands

```bash
# Helm
helm template <release> ./chart -f values.yaml | kubeconform -strict -

# Kubernetes manifest dry-run
kubectl apply --dry-run=server -f manifest.yaml

# Terraform
terraform plan -out=plan.tfplan
terraform show plan.tfplan | head -80
```

## Check Classifications

Every check is one of:
- **PASSED** - ran, output confirms claim.
- **FAILED** - ran, output refutes claim. Do not say done.
- **SKIPPED(reason)** - not applicable; state why.
- **NOT-RUN** - honest admission; downgrade claim accordingly.

## Rules

- MUST run the verifier yourself; never trust remembered or imagined output.
- NEVER use "should work", "probably fine", or "looks good" as completion evidence.
- MUST re-run verifiers after the last edit, not before.
- SHOULD paste real output (trimmed) alongside each claim.
- For infra: rendered output and dry-run ARE the evidence; no rendered output = unverified.
