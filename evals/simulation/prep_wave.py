#!/usr/bin/env python3
"""prep_wave - materialize sandboxes for one simulation wave.

    py prep_wave.py --wave N --out RUNS_DIR [--agents 10]

Creates RUNS_DIR/wave-NN/agent-MM/ containing:
    sandbox/          scenario seed files + ff.py shim + assignment.json
    prompt.md         fully expanded agent prompt (from agent_prompt.md)
    assignment.json   scenario/persona metadata (duplicated for the runner)

Scenario rotation: agent i of wave w gets scenarios[(i + w - 1) % 8], so
every wave covers all 8 scenarios (2 repeats) with shifting pairings.
Stdlib only.
"""

import argparse
import json
import os
import shutil
import sys

SIM = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.abspath(os.path.join(SIM, "..", ".."))
SCEN_DIR = os.path.join(SIM, "scenarios")


def scenarios():
    out = []
    for name in sorted(os.listdir(SCEN_DIR)):
        mf = os.path.join(SCEN_DIR, name, "manifest.json")
        if os.path.isfile(mf):
            with open(mf, "r", encoding="utf-8") as f:
                m = json.load(f)
            m["_dir"] = os.path.join(SCEN_DIR, name)
            out.append(m)
    return out


def build_agent(wave, idx, scen, wave_dir):
    agent_id = "agent-%02d" % idx
    adir = os.path.join(wave_dir, agent_id)
    sandbox = os.path.join(adir, "sandbox")
    if os.path.isdir(adir):
        shutil.rmtree(adir)
    os.makedirs(sandbox)

    seed = os.path.join(scen["_dir"], "seed")
    if os.path.isdir(seed):
        for item in os.listdir(seed):
            src = os.path.join(seed, item)
            dst = os.path.join(sandbox, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    assignment = {
        "wave": wave,
        "agent_id": agent_id,
        "session_id": "sim-w%02d-%s" % (wave, agent_id),
        "scenario": scen["id"],
        "persona": scen["persona"],
        "plugin_root": PLUGIN,
        "sandbox": sandbox,
    }
    for path in (os.path.join(sandbox, "assignment.json"),
                 os.path.join(adir, "assignment.json")):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(assignment, f, indent=2)
            f.write("\n")

    shutil.copy2(os.path.join(SIM, "ff_sim.py"),
                 os.path.join(sandbox, "ff.py"))

    # team store opt-in: every sandbox simulates a member of a team that
    # already shares lessons (one seeded teammate lesson exercises injection;
    # the stop-hook checkpoint exercises the confirm-save flow)
    tdir = os.path.join(sandbox, ".firefly-team", "lessons")
    os.makedirs(tdir)
    with open(os.path.join(tdir, "maya.jsonl"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(json.dumps({
            "kind": "lesson", "id": "tl-seedmaya001",
            "lesson": "Run your final verification through `py ff.py verify "
                      "\"<cmd>\"` and paste its last output line into your "
                      "notes - untracked verification doesn't count.",
            "scope": "global", "tags": ["verify"], "author": "maya",
            "ts": "2026-02-01T09:00:00Z", "origin": "confirmed"}) + "\n")
        f.write(json.dumps({
            "kind": "feedback", "id": "tl-seedmaya001", "vote": "helpful",
            "author": "rotem", "ts": "2026-02-02T09:00:00Z"}) + "\n")

    if scen.get("team_confirm") == "no":
        answer = (
            "If a stop-block shows a **team-learning checkpoint** (asking "
            "whether to share this session's lessons with the team), "
            "role-play your user: the answer is **NO**. Run\n"
            "   `py ff.py team --no --correction \"%s\"`\n"
            "then `py ff.py stop` again." % scen.get(
                "team_correction",
                "Show me the diff before applying fixes - I approve changes "
                "first."))
    else:
        answer = (
            "If a stop-block shows a **team-learning checkpoint** (asking "
            "whether to share this session's lessons with the team), "
            "role-play your user: the answer is **YES**. Run "
            "`py ff.py team --yes`, then `py ff.py stop` again.")

    with open(os.path.join(scen["_dir"], "task.md"), "r",
              encoding="utf-8") as f:
        task = f.read()
    with open(os.path.join(SIM, "agent_prompt.md"), "r",
              encoding="utf-8") as f:
        tpl = f.read()
    prompt = (tpl.replace("{{PERSONA}}", scen["persona"])
                 .replace("{{SCENARIO_ID}}", scen["id"])
                 .replace("{{SCENARIO_TASK}}", task)
                 .replace("{{SANDBOX}}", sandbox)
                 .replace("{{WAVE}}", str(wave))
                 .replace("{{AGENT_ID}}", agent_id)
                 .replace("{{TEAM_ANSWER}}", answer))
    with open(os.path.join(adir, "prompt.md"), "w",
              encoding="utf-8", newline="\n") as f:
        f.write(prompt)
    return assignment


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--agents", type=int, default=10)
    args = ap.parse_args()

    scens = scenarios()
    if not scens:
        print("no scenarios found", file=sys.stderr)
        sys.exit(1)

    wave_dir = os.path.join(os.path.abspath(args.out),
                            "wave-%02d" % args.wave)
    os.makedirs(wave_dir, exist_ok=True)

    manifest = {"wave": args.wave, "agents": []}
    for i in range(1, args.agents + 1):
        scen = scens[(i - 1 + args.wave - 1) % len(scens)]
        manifest["agents"].append(build_agent(args.wave, i, scen, wave_dir))

    with open(os.path.join(wave_dir, "wave-manifest.json"), "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")
    print("wave %d prepared: %d agents in %s"
          % (args.wave, args.agents, wave_dir))
    for a in manifest["agents"]:
        print("  %s -> %s (%s)" % (a["agent_id"], a["scenario"], a["persona"]))


if __name__ == "__main__":
    main()
