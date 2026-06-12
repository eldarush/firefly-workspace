"""PreToolUse(Bash) hook: the safety guard.

Policy (configurable via .firefly/config.json):
  destroy class               -> deny (or ask), always audited
  mutate class in protected   -> deny/ask (protected.contexts/namespaces globs)
  mutate elsewhere            -> neutral (Claude Code's own permission flow rules)
  read class                  -> neutral by default; allow only if auto_allow_read
                                 (never silently LOOSENS the user's permission setup)
Fail-open: any internal error => exit 0 with no output (normal permission flow).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def evaluate(cmd, cfg):
    """Pure policy evaluation: returns (klass, decision-or-None, why)."""
    import lib_firefly as ff

    beh = cfg.get("behavior", {})
    klass, reason = ff.classify_command(cmd, cfg)
    protected = ff.targets_protected(cmd, cfg)
    decision = None
    why = ""
    if klass == "destroy":
        decision = "ask" if beh.get("destroy") == "ask" else "deny"
        why = ("Firefly guard: destructive command blocked (%s). Record this "
               "verdict where you document the decision and proceed with a "
               "safer alternative. If genuinely needed, the USER must run it "
               "themselves or adjust .firefly/config.json "
               "(behavior.destroy / allow_extra)." % (reason or "destroy class"))
    elif klass == "mutate" and protected:
        decision = "ask" if beh.get("mutate_in_protected") == "ask" else "deny"
        why = ("Firefly guard: mutating command targets a PROTECTED context/namespace "
               "(see .firefly/config.json protected.*). Production-like environments "
               "are read-only for the agent; the user must perform this change.")
    elif klass == "read" and beh.get("auto_allow_read"):
        decision = "allow"
        why = "Firefly guard: read-only command auto-approved (config auto_allow_read)."
    return klass, decision, why


def check_mode(argv):
    """`pre_tool_guard.py --check "<cmd>"`: dry-run policy consultation.
    Prints the verdict, logs a guard_check event with dry_run=true, never
    executes anything. Lets anyone test a risky command against policy
    BEFORE running it."""
    import lib_firefly as ff

    cmd = " ".join(argv).strip()
    payload = {
        "session_id": os.environ.get("FF_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID") or "guard-check",
        "cwd": os.getcwd(),
        "hook_event_name": "GuardCheck",
    }
    if not cmd:
        print("usage: pre_tool_guard.py --check \"<command>\"")
        return
    cfg = ff.load_config(payload)
    klass, decision, why = evaluate(cmd, cfg)
    verdict = decision or "neutral"
    ff.log_event(payload, "guard_check", klass=klass, cmd=cmd[:160],
                 dry_run=True, decision=verdict)
    if decision in ("deny", "ask"):
        ff.audit(payload, "guard", decision + "(dry-run)",
                 "%s | %s" % (klass, cmd[:200]))
    print("guard verdict: %s (class=%s)" % (verdict.upper(), klass))
    if why:
        print(why)
    elif verdict == "neutral":
        print("No Firefly policy applies; Claude Code's own permission "
              "flow decides.")
    # paste-ready audit line: one line to drop into the doc/postmortem/PR
    # where the decision is recorded - removes all formatting friction
    print("audit line: [guard %s] class=%s cmd=%s"
          % (verdict.upper(), klass,
             cmd if len(cmd) <= 100 else cmd[:97] + "..."))


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    if payload.get("tool_name") != "Bash":
        return
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd.strip():
        return
    cfg = ff.load_config(payload)

    klass, decision, why = evaluate(cmd, cfg)

    # every consultation is visible in (rotated) events.jsonl: gives teams
    # an audit of what was screened, not only what was blocked
    ff.log_event(payload, "guard_check", klass=klass, cmd=cmd[:160],
                 decision=decision or "neutral")

    if decision in ("deny", "ask"):
        ff.audit(payload, "guard", decision, "%s | %s" % (klass, cmd[:200]))
        ff.log_event(payload, "guard_deny" if decision == "deny" else "guard_ask",
                     klass=klass, cmd=cmd[:200])

    if decision:
        ff.emit({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": why,
            }
        })


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--check":
            check_mode(sys.argv[2:])
        else:
            main()
    except Exception:
        pass
    sys.exit(0)
