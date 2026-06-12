# Firefly simulation campaign harness

Stress-tests the plugin with fleets of weak-model agents role-playing the
Firefly team (SRE / QA / DEV / RESEARCH) in airgapped conditions, then feeds
dense objective evidence to a strong-model evaluator that proposes plugin
improvements between waves.

## How a run works

The simulated "team member" is an agent that is NOT running Claude Code, so
a shim (`ff_sim.py`, copied into each sandbox as `ff.py`) feeds the REAL
plugin hooks the same JSON payloads Claude Code would send:

    py ff.py start        -> session_start.py   (context injection)
    py ff.py prompt "..." -> prompt_submit.py   (turn accounting)
    py ff.py run "cmd"    -> pre_tool_guard.py, then executes the command
                             ONLY if allowed, then tool_event.py
    py ff.py edited path  -> tool_event.py      (edit accounting)
    py ff.py stop         -> stop_gate.py       (verification gate/auto-retro)
    py ff.py end          -> session_end.py     (distillation)

Everything lands in the sandbox's `.firefly/`, which `probe.py` scores
afterwards against ground truth (see `rubric.md`).

## Scenarios

8 scenarios under `scenarios/`, one per persona pain: red tests, TDD,
flaky test triage, test design (graded by mutation testing), incident
triage, GitOps drift audit, literature synthesis (fact-checked), and a
misleading CI failure. Each plants one destructive "teammate suggestion"
(bait) that the guard must catch, and each has a cheat-proof
`pristine/verify.py` (pristine spec tests, SHA-pinned read-only files,
recomputed ground truth).

Half the scenarios pre-seed `.firefly/playbook.json` with team lessons so
session-start injection has something to offer; the other half start cold.

## Running a wave

    py evals/simulation/prep_wave.py --wave 1 --out /tmp/sim-runs
    # for each agent-NN: give an agent the generated prompt.md
    # (weak model, no web access, subagents allowed)
    py evals/simulation/probe.py --wave-dir /tmp/sim-runs/wave-01
    # give a strong model evaluate_wave.md + the wave dir
    # apply its Ranked improvements to the plugin, re-run plugin tests,
    # commit, next wave

Wave rotation shifts scenario assignments so all 8 scenarios appear every
wave (10 agents = 8 + 2 repeats).

## Files

| file | role |
|------|------|
| `ff_sim.py` | Claude Code lifecycle shim (copied into sandboxes as `ff.py`) |
| `prep_wave.py` | builds per-agent sandboxes + prompts for a wave |
| `probe.py` | objective scoring, per-agent `probe.json` + `wave-probe.json` |
| `agent_prompt.md` | template the simulated team member receives |
| `evaluate_wave.md` | briefing for the strong-model wave evaluator |
| `rubric.md` | scoring weights, quality bars, campaign success criteria |
| `selftest.py` | end-to-end harness check (golden run + empty run) |
| `scenarios/*` | task seeds, baits, pristine verifiers |

`selftest.py` drives a scripted "perfect agent" through ff.py against the
real hooks and expects a near-perfect probe score, then probes an untouched
sandbox and expects a near-zero score - validating shim, hooks, scenario
and probe in one pass:

    py evals/simulation/selftest.py
