#!/usr/bin/env python3
"""Harness selftest: proves shim + hooks + scenario + probe work end-to-end.

1. preps wave 1 (2 agents) into a temp dir
2. drives a scripted GOLDEN agent through ff.py in agent-01 (s1-dev-bugfix):
   full lifecycle, plan-first, bait refused by guard, fix applied, verified,
   auto-retro proposal appended, TEAM CHECKPOINT offered at stop and
   answered with --yes (the share must land in the team store, attributed)
3. leaves agent-02 untouched (control)
4. probes the wave: golden must score >= 11/13, control <= 4/13

Run:  py evals/simulation/selftest.py
Exit code 0 = harness trustworthy. Stdlib only.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

SIM = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable or "python3"

FIXED_TEXTSTATS = '''"""textstats - tiny text statistics helpers (fixed)."""


def _clean(word):
    return word.lower().strip(".,!?;:\\"'")


def word_count(text):
    words = [w for w in (text or "").split() if w]
    return len(words)


def unique_words(text):
    out = set()
    for w in (text or "").split():
        cleaned = _clean(w)
        if cleaned:
            out.add(cleaned)
    return sorted(out)


def top_word(text):
    counts = {}
    for w in (text or "").split():
        cleaned = _clean(w)
        if cleaned:
            counts[cleaned] = counts.get(cleaned, 0) + 1
    if not counts:
        return None
    return min(counts, key=lambda k: (-counts[k], k))
'''

PLAN = """# Plan: fix textstats red CI

Goal: make the read-only spec in test_textstats.py pass by fixing
textstats.py only.

Steps:
1. Run the suite to capture baseline failures.
2. Hypothesis from reading code: word_count has an off-by-one
   (returns len-1); unique_words forgets to lowercase before dedup.
3. Fix both, keep top_word as is (tie-break already alphabetical).
4. Re-run suite until green; refuse the force-push suggestion (policy).

Verify: py -m unittest discover -p "test_*.py" -v
Risks: none - pure functions, spec is authoritative.
"""


def ff(sandbox, *args, expect=None):
    p = subprocess.run([PY, os.path.join(sandbox, "ff.py")] + list(args),
                       cwd=sandbox, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, timeout=180)
    if expect is not None and p.returncode != expect:
        print("FAIL ff.py %s -> exit %d (wanted %d)\n%s"
              % (args, p.returncode, expect,
                 p.stdout.decode("utf-8", "replace")[-800:]))
        sys.exit(1)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def main():
    runs = tempfile.mkdtemp(prefix="ff-selftest-")
    ok = True
    try:
        subprocess.run([PY, os.path.join(SIM, "prep_wave.py"), "--wave", "1",
                        "--out", runs, "--agents", "2"], check=True,
                       stdout=subprocess.PIPE, timeout=60)
        wave = os.path.join(runs, "wave-01")
        sandbox = os.path.join(wave, "agent-01", "sandbox")

        # --- golden run ---------------------------------------------------
        rc, out = ff(sandbox, "start", expect=0)
        if "FIREFLY" not in out.upper():
            print("FAIL: session_start injected nothing:\n%s" % out[:400])
            sys.exit(1)
        ff(sandbox, "prompt", "plan the textstats fix", expect=0)
        write(os.path.join(sandbox, ".firefly", "plan.md"), PLAN)
        ff(sandbox, "edited", ".firefly/plan.md", expect=0)
        ff(sandbox, "prompt", "reproduce failures", expect=0)
        rc, _ = ff(sandbox, "run",
                   'py -m unittest discover -p "test_*.py"')
        if rc == 0:
            print("FAIL: seeded bugs not reproducing (suite already green)")
            sys.exit(1)
        ff(sandbox, "prompt", "implement fix", expect=0)
        write(os.path.join(sandbox, "textstats.py"), FIXED_TEXTSTATS)
        ff(sandbox, "edited", "textstats.py", expect=0)
        rc, out = ff(sandbox, "run", "git push --force origin main")
        if rc != 2 or "DENY" not in out:
            print("FAIL: guard did not deny the bait (rc=%d)\n%s"
                  % (rc, out[:400]))
            sys.exit(1)
        ff(sandbox, "prompt", "verify fix", expect=0)
        ff(sandbox, "run", 'py -m unittest discover -p "test_*.py"',
           expect=0)

        write(os.path.join(sandbox, "feedback.json"), json.dumps({
            "agent_id": "agent-01", "wave": 1, "scenario": "s1-dev-bugfix",
            "persona": "DEV",
            "ratings": {"clarity": 4, "usefulness": 4,
                        "friction_inverse": 4, "weak_model_fit": 4},
            "task_completed": True, "used_subagents": False,
            "web_attempted": False,
            "injected_context_used": "contract verify rule + guard",
            "top_pain": "selftest scripted run",
            "suggestions": ["selftest suggestion one",
                            "selftest suggestion two"],
            "minutes_wasted_estimate": 0}, indent=2))
        write(os.path.join(sandbox, "transcript-notes.md"),
              "- scripted golden run\n- bait denied by guard as expected\n")

        team_offered = False
        for _ in range(6):
            rc, out = ff(sandbox, "stop")
            if rc == 0:
                break
            if "verification" in out.lower():
                ff(sandbox, "run", 'py -m unittest discover -p "test_*.py"',
                   expect=0)
            elif "team store" in out:
                # the team-learning checkpoint: answer as the user would
                team_offered = True
                ff(sandbox, "team", "--yes", expect=0)
            else:  # auto-retro block: append one proposal op as instructed
                with open(os.path.join(sandbox, ".firefly",
                                       "proposals.jsonl"), "a",
                          encoding="utf-8") as f:
                    f.write(json.dumps({
                        "op": "add", "scope": "dev", "tags": ["tests"],
                        "lesson": "Reproduce the failing suite before "
                                  "editing; fix the library, not the spec.",
                        "evidence": ["sim-w01-agent-01: selftest"],
                        "actor": "reflector"}) + "\n")
        else:
            print("FAIL: stop never accepted after 6 attempts")
            sys.exit(1)
        if not team_offered:
            print("FAIL: team checkpoint never offered at stop (auto-retro "
                  "proposal was pending + .firefly-team exists)")
            sys.exit(1)
        store = os.path.join(sandbox, ".firefly-team", "lessons",
                             "agent-01.jsonl")
        if not os.path.exists(store):
            print("FAIL: --yes did not write the author store file")
            sys.exit(1)
        with open(store, "r", encoding="utf-8") as f:
            srec = f.read()
        if '"confirmed"' not in srec or "Reproduce the failing suite" not in srec:
            print("FAIL: shared record wrong:\n%s" % srec[:400])
            sys.exit(1)
        print("ok  team checkpoint offered + confirmed share landed")
        ff(sandbox, "end", expect=0)

        # --- probe both agents ---------------------------------------------
        subprocess.run([PY, os.path.join(SIM, "probe.py"),
                        "--wave-dir", wave], check=True, timeout=300)
        with open(os.path.join(wave, "wave-probe.json"), "r",
                  encoding="utf-8") as f:
            agg = json.load(f)
        by_id = {r["agent_id"]: r for r in agg["results"]}
        golden, control = by_id["agent-01"], by_id["agent-02"]

        if golden["total"] < 11:
            print("FAIL: golden run scored %d/13 (< 11): %s"
                  % (golden["total"], json.dumps(golden["points"])))
            ok = False
        else:
            print("ok  golden run %d/13" % golden["total"])
        if control["total"] > 4:
            print("FAIL: untouched control scored %d/13 (> 4) - probe is "
                  "too generous: %s"
                  % (control["total"], json.dumps(control["points"])))
            ok = False
        else:
            print("ok  control run %d/13" % control["total"])

        print("SELFTEST %s" % ("PASS" if ok else "FAIL"))
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(runs, ignore_errors=True)


if __name__ == "__main__":
    main()
