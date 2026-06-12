---
name: research-experiment-design
description: Use when designing a benchmark, POC, or A/B config test to answer a technical question, validate a hypothesis, or measure capacity on the airgapped k8s platform.
---
# Research Experiment Design

## Core Principle

A hypothesis MUST be falsifiable and measurable.
"If we X, then Y (measured by Z) will change by at least W" -- if no measurement can refute it, it is not an experiment, it is an opinion.
Define the success threshold BEFORE running. Post-hoc goalpost moves invalidate the experiment.

---

## Step 1 -- Hypothesis and Decision (write before touching any infrastructure)

```
Hypothesis: If we [change], then [metric] will [direction] by at least [threshold],
            measured by [instrument] over [duration/window].

Decision:   This experiment informs [decision].
            If supported: we will [action A].
            If refuted: we will [action B].
            If inconclusive: we will [action C].

Success threshold (MUST be set before running):
            [metric] [comparison] [value] at [percentile], over [N] runs.
```

Example:
```
Hypothesis: If Flink job parallelism is increased from 4 to 8,
            then job throughput (events/sec at p95) will increase by >= 40%,
            measured by flink_taskmanager_job_task_numRecordsOutPerSecond in Grafana
            over a 10-minute sustained load window per run.
Decision:   Informs horizontal scaling policy for stream jobs.
```

---

## Step 2 -- Variables

| Variable Type      | What It Is                              | How to Control It                                         |
|--------------------|-----------------------------------------|-----------------------------------------------------------|
| Independent        | The one thing being changed             | Change ONLY this; document the exact values               |
| Dependent          | The measured outcome                    | Set up the instrument (Grafana query, benchmark output) before starting |
| Controlled         | Everything else (versions, resources, data, seeds) | Pin images by digest; fix requests/limits; record exact values |
| Nuisance           | Things you cannot fully control         | Isolate namespace/node pool; note in results; avoid peak-traffic windows |

In k8s experiments:
```bash
# pin images by digest to prevent version drift mid-experiment (R0 read; R3 to apply)
kubectl get deploy <NAME> -n <NS> -o jsonpath='{.spec.template.spec.containers[0].image}'

# record exact resource requests and limits
kubectl get deploy <NAME> -n <NS> -o yaml | grep -A 8 resources:

# isolate to a dedicated node pool via nodeSelector (apply via MR, R2/R3)
# record which nodes ran each variant: kubectl get pods -n <NS> -o wide
```

Any change to the test namespace requires an MR or explicit human approval (R2/R3).

---

## Step 3 -- Baseline First (MUST)

Measure the status quo with the SAME harness BEFORE introducing the candidate.
A result without a baseline is uninterpretable.

```bash
# export metric from Grafana (internal API, airgapped)
curl -s "http://<GRAFANA_HOST>/api/datasources/proxy/<DS_ID>/api/v1/query_range" \
  --data-urlencode 'query=<PROMQL_METRIC>{job="<JOB>"}' \
  --data-urlencode "start=<UNIX_START>" \
  --data-urlencode "end=<UNIX_END>" \
  --data-urlencode "step=15" \
  -H "Authorization: Bearer <GRAFANA_TOKEN>" \
  > experiment-baseline-raw.json
```

Save raw output to a file in the experiment directory, not in a temp location.

---

## Step 4 -- Runs

- N >= 5 per variant for any timing-based metric.
- Discard the first 1-2 warmup runs and document that you did so (note the count in the results).
- Report MEDIAN and P95 -- not mean (mean is distorted by outliers).
- Interleave variants when possible (A, B, A, B, ...) to reduce time-of-day bias.
- Record wall-clock timestamps and node/load conditions for every run.

```bash
# example run loop -- adapt command and cooldown to your harness
for run in $(seq 1 7); do
  echo "=== Run $run $(date -Iseconds) ===" | tee -a experiment-results.log
  <LOAD_GENERATOR_CMD> 2>&1 | tee -a experiment-results.log
  sleep 60  # cooldown to let the system return to steady state
done
```

---

## Step 5 -- Results

Present raw data first; interpretation second. Never omit the raw numbers.

| Run | Variant   | Metric p95 | Notes              |
|-----|-----------|------------|--------------------|
| 1   | Baseline  | 12,400     | warmup, discarded  |
| 2   | Baseline  | 14,200     |                    |
| 3   | Baseline  | 13,800     |                    |
| ... | ...       | ...        | ...                |

Compute and report:
- Median and p95 per variant.
- Whether the pre-defined success threshold was met.
- Variance (p95 - p5 range) -- if variance > effect size, declare inconclusive.

"No significant difference" is a VALID and publishable result. Report it honestly.
Do not re-slice the data until something "wins" -- that is p-hacking.

---

## Step 6 -- Conclusion

```
Result:          [supported / refuted / inconclusive]
Metric:          Baseline median X; Candidate median Y; delta Z%.
Threshold:       [met / not met] (threshold was set as [value] before running)
Decision:        We will / will not proceed with [action].
What would change this result: [more runs / larger effect size / different metric / better isolation]
Follow-up experiments: [list or "none"]
```

---

## Failure Table

| Failure Mode                        | Symptom                                              | Fix                                                                 |
|-------------------------------------|------------------------------------------------------|---------------------------------------------------------------------|
| Measuring the harness, not the system | Harness CPU is the bottleneck; system is idle      | Profile the harness; increase harness resources or use a lighter one |
| Variance > effect size              | Wide spread across runs; small mean difference       | Run more iterations; check for noisy neighbors; test a larger change |
| Config drift mid-experiment         | Environment changed between baseline and candidate   | Pin all versions by digest; re-run baseline from scratch            |
| Different hardware per variant      | Baseline on node class A, candidate on node class B  | Use nodeAffinity to pin both variants to the same node class        |
| Post-hoc re-slicing                 | "If we only look at Tuesday runs the result is positive" | Pre-register the analysis plan; reject any re-slicing after unblinding |
| Decision not defined upfront        | Threshold set after seeing results                   | Discard results; re-run with pre-registered threshold               |

---

## Experiment Template

A structured template is available at:
${CLAUDE_PLUGIN_ROOT}/assets/templates/experiment.md

Use it for every experiment to ensure consistent provenance, variable recording, and result structure.