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


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    if payload.get("tool_name") != "Bash":
        return
    cmd = (payload.get("tool_input") or {}).get("command", "") or ""
    if not cmd.strip():
        return
    cfg = ff.load_config(payload)
    beh = cfg.get("behavior", {})

    klass, reason = ff.classify_command(cmd, cfg)
    protected = ff.targets_protected(cmd, cfg)

    # every consultation is visible in (rotated) events.jsonl: gives teams
    # an audit of what was screened, not only what was blocked
    ff.log_event(payload, "guard_check", klass=klass, cmd=cmd[:160])

    decision = None
    why = ""

    if klass == "destroy":
        decision = "ask" if beh.get("destroy") == "ask" else "deny"
        why = ("Firefly guard: destructive command blocked (%s). If genuinely needed, "
               "the USER must run it themselves or adjust .firefly/config.json "
               "(behavior.destroy / allow_extra)." % (reason or "destroy class"))
    elif klass == "mutate" and protected:
        decision = "ask" if beh.get("mutate_in_protected") == "ask" else "deny"
        why = ("Firefly guard: mutating command targets a PROTECTED context/namespace "
               "(see .firefly/config.json protected.*). Production-like environments "
               "are read-only for the agent; the user must perform this change.")
    elif klass == "read" and beh.get("auto_allow_read"):
        decision = "allow"
        why = "Firefly guard: read-only command auto-approved (config auto_allow_read)."

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
        main()
    except Exception:
        pass
    sys.exit(0)
