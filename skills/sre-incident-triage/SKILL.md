---
name: sre-incident-triage
description: Use when an alert fired, service is degraded, pods are crashlooping, latency spiked, or on-call needs structured triage of a k8s/ArgoCD workload.
---
# SRE Incident Triage

## Step 1 -- Build Incident Context Brief

Before touching any cluster, establish facts in writing.

| Field            | Source                                              |
|------------------|-----------------------------------------------------|
| Service + owner  | alert label / team runbook                          |
| Cluster/namespace| alert label                                         |
| Workload kind    | kubectl get all -n <NS>                             |
| ArgoCD app       | kubectl get applications -n argocd                  |
| Recent changes   | commands below                                      |

```bash
# R0 -- read-only history
argocd app history <APP> --server <ARGOCD_SERVER>
helm history <RELEASE> -n <NS>
git -C <ENV_REPO> log --oneline -20 -- <PATH_TO_ENV_VALUES>
kubectl rollout history deploy/<DEPLOY> -n <NS>
```

Correlate alert start time with the most recent rollout timestamp.
If delta < 10 min: deploy is the prime suspect -- score HIGH confidence.

---

## Step 2 -- Read-Only Evidence Sweep (R0)

Run in order; capture all output for the incident doc.

```bash
# 1. namespace events sorted by time
kubectl get events -n <NS> --sort-by=.lastTimestamp | tail -40

# 2. pod status overview
kubectl get pods -n <NS> -o wide

# 3. describe the failing pod
kubectl describe pod <POD> -n <NS>

# 4. current and previous container logs
kubectl logs <POD> -n <NS> --tail=200
kubectl logs <POD> -n <NS> --previous --tail=200

# 5. resource pressure
kubectl top pods -n <NS>
kubectl top nodes

# 6. full pod spec (limits, probes, image digest, envFrom)
kubectl get pod <POD> -n <NS> -o yaml

# 7. service and endpoint health
kubectl get svc,endpoints -n <NS>

# 8. ArgoCD health and diff (desired vs live)
argocd app get <APP> --server <ARGOCD_SERVER>
argocd app diff <APP> --server <ARGOCD_SERVER>
```

NEVER restart, delete, or scale anything as a diagnosis step.

---

## Step 3 -- Hypothesis Tree

For each candidate: state confidence, run the confirm/refute probe.

### Failure Mode Table

| Symptom / Exit        | Likely Cause                        | Confirm Probe                                              | Fix Path                          |
|-----------------------|-------------------------------------|------------------------------------------------------------|-----------------------------------|
| OOMKilled (exit 137)  | Limit too low vs actual usage       | kubectl top pod + pod yaml (limits section)                | Raise limit via values MR         |
| CrashLoopBackOff      | App error on startup                | kubectl logs --previous                                    | Fix app or config via MR          |
| ImagePullBackOff      | Wrong tag / missing secret / airgapped registry unavailable | kubectl describe pod events   | Fix image ref or imagePullSecret via MR |
| Pending (long)        | Insufficient CPU/mem, taint mismatch, PVC unbound | kubectl describe pod Events; kubectl get pvc -n <NS> | Resource quota MR or node capacity review |
| Readiness probe failing | Probe path wrong or app warmup too slow | kubectl describe pod (probe config); curl from debug pod | Fix probe or initialDelaySeconds via MR |
| Config drift (Degraded but Synced) | Hand-edit or controller fighting ArgoCD | argocd app diff shows live != git | Sync via approval or fix source in MR |

### "Is It the Deploy?" Check

```bash
kubectl rollout history deploy/<DEPLOY> -n <NS> --revision=<N>
# compare printed timestamp with alert start time from Grafana/alertmanager
```

---

## Step 4 -- Blast Radius Statement

Before proposing any remediation, document:
- Services affected and SLO impact (e.g., error rate > 1% for 10 min).
- Downstream consumers at risk.
- Data integrity risk: none / possible / confirmed.
- Is broken traffic currently hitting the pod? (kubectl get endpoints -n <NS>)

---

## Step 5 -- Remediation (MR-only preferred; approval-gated otherwise)

MUST propose an MR-based path before any direct cluster operation.

| Option                | Path                                             | Rollback                                                                 |
|-----------------------|--------------------------------------------------|--------------------------------------------------------------------------|
| Config or image fix   | MR to env repo -> ArgoCD syncs                  | argocd rollback <APP> <REVISION> --server <ARGOCD_SERVER> [REQUIRES HUMAN APPROVAL] |
| Helm values fix       | MR to chart values -> CI validates -> ArgoCD syncs | helm rollback <RELEASE> <REVISION> -n <NS> [REQUIRES HUMAN APPROVAL]  |
| Emergency rollback    | argocd rollback <APP> <PREV_REVISION> [REQUIRES HUMAN APPROVAL] | Re-apply current values via MR |
| Scale down bad pods   | kubectl scale deploy/<D> --replicas=0 -n <NS> [REQUIRES HUMAN APPROVAL] | kubectl scale deploy/<D> --replicas=<N> -n <NS> [REQUIRES HUMAN APPROVAL] |

NEVER bypass ArgoCD with kubectl apply when a GitOps path exists.
NEVER hand-edit a live cluster resource when an MR path is available.

---

## Step 6 -- Incident Timeline (for postmortem)

```
HH:MM  Alert fired -- <alert name>, threshold <value>
HH:MM  Context brief complete
HH:MM  Evidence sweep complete -- top hypothesis: <cause>
HH:MM  Hypothesis confirmed via <probe>
HH:MM  Blast radius: <N> services, SLO impact <detail>
HH:MM  Remediation MR opened: <MR URL>
HH:MM  Fix applied via ArgoCD sync
HH:MM  Alert resolved, recovery confirmed
```

Attach to incident doc: events output, describe output, Grafana dashboard link, argocd diff output.