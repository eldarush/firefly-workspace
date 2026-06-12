#!/usr/bin/env python3
"""verify_run - first-class Firefly verification entry point.

    py <plugin>/scripts/verify_run.py "<command>"
    py <plugin>/scripts/verify_run.py            (re-runs the registered verifier)

Runs the given verification command and ALWAYS records the result in
Firefly's session telemetry (a `verify` event + state update), no matter
what the command is called. This is the root fix for "my verifier has an
unusual name so the heuristic missed it": if you verify through this
entry point, it is tracked, registered for future sessions, and the stop
gate sees it.

Exit code mirrors the verification command's exit code. Stdlib only.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_firefly as ff  # noqa: E402


def _payload():
    return {
        "session_id": os.environ.get("FF_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID") or "verify-run",
        "cwd": os.getcwd(),
        "hook_event_name": "VerifyRun",
    }


def main():
    cmd = " ".join(sys.argv[1:]).strip()
    payload = _payload()
    cfg = ff.load_config(payload)

    if not cmd:
        registered = (cfg.get("verify", {}) or {}).get("commands", [])
        if registered:
            cmd = registered[0]
            print("(no command given - using registered verifier: %s)" % cmd)
        else:
            print("usage: verify_run.py \"<verification command>\"")
            print("No verifier registered yet. Pass your project's test/check "
                  "command once and Firefly will remember it.")
            sys.exit(64)

    p = subprocess.run(cmd, shell=True, cwd=ff.project_dir(payload),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=600)
    out = p.stdout.decode("utf-8", "replace")
    sys.stdout.write(out)
    ok = p.returncode == 0

    sid = payload["session_id"]
    st = ff.load_state(payload, sid)
    st["verify_seen"] = True
    st["last_verify"] = "pass" if ok else "fail"
    if ok:
        st["edits_since_verify"] = 0
    ff.save_state(payload, st)
    ff.log_event(payload, "verify", result="pass" if ok else "fail",
                 cmd=cmd[:160], entrypoint=True)
    if ff.register_verifier(payload, cmd):
        ff.log_event(payload, "verifier_registered", cmd=cmd[:160],
                     via="verify_run")

    print("\n[firefly verify: %s | exit %d | tracked]"
          % ("PASS" if ok else "FAIL", p.returncode))
    sys.exit(p.returncode)


if __name__ == "__main__":
    main()
