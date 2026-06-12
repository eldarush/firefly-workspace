---
name: sre-gitops-operations
description: Use when an ArgoCD app is OutOfSync or Degraded, a Kargo promotion is stuck, a helm release has drift, or you need to validate and land a GitOps environment change.
---
# SRE GitOps Operations

## GitOps Mental Model

1. Desired state lives in git (env repo or chart repo values).
2. ArgoCD continuously reconciles live cluster state to git.
3. Kargo orchestrates promotion of freight between stages (dev -> staging -> prod).
4. NEVER hand-edit live cluster resources when a GitOps path exists.
5. Drift means something fought the reconciler -- find and fix the source, not the symptom.

---

## Step 1 -- Diagnose ArgoCD App Status (R0)

```bash
# list all apps with sync and health status
kubectl get applications -n argocd -o wide

# detailed status for one app
argocd app get <APP> --server <ARGOCD_SERVER>

# what differs between live cluster and git HEAD
argocd app diff <APP> --server <ARGOCD_SERVER>

# deployment history
argocd app history <APP> --server <ARGOCD_SERVER>
```

### Sync Status vs Health Status

| Sync Status | Health Status | Meaning                                                     |
|-------------|---------------|-------------------------------------------------------------|
| Synced      | Healthy       | All good                                                    |
| Synced      | Degraded      | App is live but unhealthy -- go to sre-incident-triage      |
| OutOfSync   | Healthy       | Git changed and not yet applied, or drift present           |
| OutOfSync   | Degraded      | Bad state AND not aligned to git -- highest priority        |
| Synced      | Progressing   | Rollout in flight; wait or inspect hooks                    |
| Unknown     | Any           | Argo cannot assess health; check CRD registration or RBAC   |

---

## Step 2 -- Drift Investigation (R0)

```bash
argocd app diff <APP> --server <ARGOCD_SERVER>
```

- Drift with no recent git change: someone hand-edited or a controller modified the resource.
- Drift with recent git change: sync not yet triggered or sync is failing.
- Persistent drift (re-appears after sync): an external controller is fighting Argo.
  Identify it:
  ```bash
  kubectl get events -n <NS> --sort-by=.lastTimestamp | tail -30
  kubectl describe <RESOURCE_KIND> <NAME> -n <NS>
  ```

---

## Step 3 -- Helm Release Inspection (R0)

```bash
# list releases in namespace
helm list -n <NS>

# current release status and last operation result
helm status <RELEASE> -n <NS>

# full revision history
helm history <RELEASE> -n <NS>

# deployed values vs chart defaults
helm get values <RELEASE> -n <NS>
helm get values <RELEASE> -n <NS> --all

# MUST validate rendering before any change
helm template <RELEASE> <CHART_PATH_OR_REF> -f <VALUES_FILE> | kubeconform -strict -
```

MUST run `helm template | kubeconform -strict` before proposing any helm values change.

---

## Step 4 -- Kargo Stage and Promotion Inspection (R0)

```bash
# list all stages and their status
kubectl get stages -n <KARGO_NS>
kubectl describe stage <STAGE> -n <KARGO_NS>

# inspect available freight (candidate artifact sets)
kubectl get freight -n <KARGO_NS>
kubectl describe freight <FREIGHT_ID> -n <KARGO_NS>

# list promotions and their status
kubectl get promotions -n <KARGO_NS>
kubectl describe promotion <PROMOTION_NAME> -n <KARGO_NS>
```

### Stuck Promotion Checklist

- [ ] Approval gate: does the stage require human approval? Check promotion spec `approvalRequired`.
- [ ] Verification: did an AnalysisRun fail? `kubectl get analysisruns -n <KARGO_NS>`.
- [ ] Freight health: is the freight itself marked as verified? `kubectl describe freight <ID>`.
- [ ] ArgoCD downstream: is the target app in SyncFailed or Degraded state?
- [ ] Controller errors: `kubectl logs -n <KARGO_NS> -l app=kargo-controller --tail=100`.

---

## Step 5 -- Making Changes (MR-Only Workflow)

```
1. Edit values or manifests in the env or chart repo locally (R1).
2. helm template ... | kubeconform -strict -     (validate locally, R1)
3. Open MR with the rendered diff in the description (R2).
4. CI validates rendering and schema.
5. After merge, ArgoCD syncs or Kargo promotes -- no manual cluster intervention needed.
```

Direct `helm upgrade` against a live cluster = R3, requires explicit human approval.
If a direct upgrade is performed, you MUST immediately open an MR to realign git to what was applied.
Risk classes: R0 read-only / R1 local edits+tests / R2 shared CI-config / R3 cluster-deploy-secrets / R4 destructive-irreversible (denied).

---

## Step 6 -- Rollback Paths (all require human approval)

| Method                        | Command                                                                              | Undo the rollback                                |
|-------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------|
| ArgoCD rollback               | argocd rollback <APP> <REVISION> --server <ARGOCD_SERVER> [REQUIRES HUMAN APPROVAL] | argocd app sync <APP> to re-apply git HEAD       |
| Kargo: re-promote prior freight | Use Kargo UI or kubectl patch the promotion [REQUIRES HUMAN APPROVAL]              | Promote current freight again                    |
| Helm rollback                 | helm rollback <RELEASE> <REVISION> -n <NS> [REQUIRES HUMAN APPROVAL]               | helm upgrade to desired version; align git via MR |

---

## Failure Table

| Symptom                   | Cause                                           | Fix Path                                                        |
|---------------------------|-------------------------------------------------|-----------------------------------------------------------------|
| App stuck Progressing     | Hook job not completing; health check not passing | Inspect hook pod logs; check argocd app resources view        |
| SyncFailed: Forbidden     | Argo service account missing RBAC               | MR to add ClusterRole or RoleBinding                           |
| SyncFailed: CRD not found | CRD applied after the resource that uses it     | Use Argo sync waves (annotation `argocd.argoproj.io/sync-wave`) via MR |
| SyncFailed: field conflict | Server-side apply field manager conflict        | Identify the other manager; use --force-conflicts only with human approval |
| Degraded but Synced       | App-level failure, not a GitOps failure         | Go to sre-incident-triage                                      |
| Kargo verification failed | AnalysisRun metric threshold not met            | Inspect metrics in Grafana; determine regression vs false positive |