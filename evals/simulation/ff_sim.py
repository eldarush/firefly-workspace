#!/usr/bin/env python3
"""ff_sim - simulated Claude Code runtime shim for Firefly simulation agents.

A copy of this file is placed in every simulation sandbox as `ff.py`.
It feeds the REAL plugin hooks the same JSON payloads Claude Code would,
so a non-Claude-Code agent (or a human) can exercise the full Firefly
lifecycle: context injection, guard, event capture, stop gate, distill.

Usage (always run from the sandbox directory):
    py ff.py start                  SessionStart  -> prints injected context
    py ff.py prompt "text"          UserPromptSubmit (counts a turn)
    py ff.py run "shell command"    PreToolUse guard -> execute -> PostToolUse
    py ff.py guard "shell command"  DRY-RUN policy check (never executes)
    py ff.py edited <path>          PostToolUse Edit (after editing a file)
    py ff.py stop                   Stop (verification gate / auto-retro)
    py ff.py stop --again           Stop with stop_hook_active=true
    py ff.py end                    SessionEnd (distill + rollup)

`run` is the important one: it refuses to execute anything the Firefly
guard denies (exit 2), exactly like Claude Code would. All activity lands
in .firefly/ artifacts that probe.py later scores. Stdlib only.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _assignment():
    try:
        with open(os.path.join(HERE, "assignment.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


ASSIGN = _assignment()
PLUGIN = ASSIGN.get("plugin_root") or os.environ.get("CLAUDE_PLUGIN_ROOT", "")
SID = ASSIGN.get("session_id", "sim-local")
PY = sys.executable or "python3"


def hook(script, payload):
    """Invoke a real plugin hook with a Claude-Code-shaped payload."""
    base = {"session_id": SID, "transcript_path": "", "cwd": HERE}
    base.update(payload)
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = HERE
    env["CLAUDE_PLUGIN_ROOT"] = PLUGIN
    p = subprocess.run(
        [PY, os.path.join(PLUGIN, "scripts", script)],
        input=json.dumps(base).encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60)
    out = p.stdout.decode("utf-8", "replace").strip()
    if out:
        try:
            return json.loads(out)
        except Exception:
            return {"_raw": out}
    return {}


def cmd_start():
    res = hook("session_start.py", {"hook_event_name": "SessionStart",
                                    "source": "startup"})
    ctx = ""
    if isinstance(res, dict):
        ctx = ((res.get("hookSpecificOutput") or {}).get("additionalContext")
               or res.get("_raw") or "")
    print("=== FIREFLY SESSION CONTEXT (obey this) ===")
    print(ctx if ctx else "(no injected context)")
    print("=== END CONTEXT ===")


def cmd_prompt(text):
    res = hook("prompt_submit.py", {"hook_event_name": "UserPromptSubmit",
                                    "prompt": text})
    ctx = ""
    if isinstance(res, dict):
        ctx = ((res.get("hookSpecificOutput") or {}).get("additionalContext")
               or "")
    if ctx:
        print("[firefly prompt-frame]")
        print(ctx)
    else:
        print("(turn recorded)")


def cmd_run(command):
    res = hook("pre_tool_guard.py", {"hook_event_name": "PreToolUse",
                                     "tool_name": "Bash",
                                     "tool_input": {"command": command}})
    decision, reason = "", ""
    if isinstance(res, dict):
        hso = res.get("hookSpecificOutput") or {}
        decision = hso.get("permissionDecision", "")
        reason = hso.get("permissionDecisionReason", "")
    if decision == "deny":
        print("FIREFLY GUARD: DENY - command NOT executed.")
        print("reason: %s" % reason)
        sys.exit(2)
    if decision == "ask":
        print("FIREFLY GUARD: ASK - %s" % reason)
        print("(simulation policy: treat ASK as 'explain to user first'; "
              "command NOT executed. Re-run with --force after you have "
              "written your justification into your plan.)")
        if "--force" not in sys.argv:
            sys.exit(3)

    p = subprocess.run(command, shell=True, cwd=HERE,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       timeout=120)
    out = p.stdout.decode("utf-8", "replace")
    tail = out[-4000:]
    if p.returncode == 0:
        tresp = tail or "ok"
    else:
        tresp = "command failed with exit code %d\n%s" % (p.returncode, tail)
    hook("tool_event.py", {"hook_event_name": "PostToolUse",
                           "tool_name": "Bash",
                           "tool_input": {"command": command},
                           "tool_response": tresp})
    sys.stdout.write(out)
    print("\n[exit %d]" % p.returncode)
    sys.exit(p.returncode)


def cmd_guard(command):
    """Dry-run a command against the Firefly guard without executing it."""
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = HERE
    env["CLAUDE_PLUGIN_ROOT"] = PLUGIN
    env["FF_SESSION_ID"] = SID
    p = subprocess.run(
        [PY, os.path.join(PLUGIN, "scripts", "pre_tool_guard.py"),
         "--check", command],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
        cwd=HERE, timeout=60)
    sys.stdout.write(p.stdout.decode("utf-8", "replace"))


def cmd_edited(path):
    hook("tool_event.py", {"hook_event_name": "PostToolUse",
                           "tool_name": "Edit",
                           "tool_input": {"file_path": path},
                           "tool_response": "ok"})
    print("(edit recorded: %s)" % path)


def cmd_stop(again=False):
    res = hook("stop_gate.py", {"hook_event_name": "Stop",
                                "stop_hook_active": bool(again)})
    if isinstance(res, dict) and res.get("decision") == "block":
        print("FIREFLY STOP-BLOCK (you must address this, then run "
              "`py ff.py stop` again):")
        print(res.get("reason", ""))
        sys.exit(2)
    print("(stop accepted - session may finish)")


def cmd_end():
    hook("session_end.py", {"hook_event_name": "SessionEnd", "reason": "exit"})
    print("(session ended - distillation done)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    op = args[0]
    if op == "start":
        cmd_start()
    elif op == "prompt":
        cmd_prompt(args[1] if len(args) > 1 else "")
    elif op == "run":
        if len(args) < 2:
            print("usage: py ff.py run \"<command>\"")
            sys.exit(1)
        cmd_run(args[1])
    elif op == "guard":
        if len(args) < 2:
            print("usage: py ff.py guard \"<command>\"")
            sys.exit(1)
        cmd_guard(args[1])
    elif op == "edited":
        cmd_edited(args[1] if len(args) > 1 else "")
    elif op == "stop":
        cmd_stop(again="--again" in args)
    elif op == "end":
        cmd_end()
    else:
        print("unknown op: %s" % op)
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
