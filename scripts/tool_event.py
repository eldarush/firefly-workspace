"""PostToolUse(*) + SubagentStop hook: the session's flight recorder.

Tracks, in per-session state:
  - code edits since last successful verify (arms the stop-gate)
  - verifier runs and their pass/fail
  - error streaks by digest -> injects a strategy-switch nudge at >= 2 repeats
  - repeated command patterns (automation candidates)
Appends compact events to events.jsonl for the distiller. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}

STRATEGY_NUDGE = """Firefly: the same error has now occurred %d times (%s...). Do NOT \
retry the same approach. State a new hypothesis about the root cause, gather one \
piece of disconfirming evidence (read the code/log), and only then try a different \
fix. Consider the ff:systematic-debugging skill."""


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    event = payload.get("hook_event_name", "PostToolUse")
    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)
    cfg = ff.load_config(payload)

    if event == "SubagentStop":
        ff.log_event(payload, "subagent_stop")
        ff.save_state(payload, st)
        return

    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input") or {}
    tresp = payload.get("tool_response")
    nudge = None

    if tool in EDIT_TOOLS:
        fp = tin.get("file_path") or tin.get("notebook_path") or ""
        if ff.is_code_file(fp, cfg):
            st["edits_since_verify"] = st.get("edits_since_verify", 0) + 1
            files = st.get("edited_files", [])
            if fp and fp not in files:
                files.append(fp)
                st["edited_files"] = files[-50:]
        ff.log_event(payload, "edit", path=os.path.basename(fp or "")[:80])

    elif tool == "Bash":
        cmd = tin.get("command", "") or ""
        err = ff.tool_response_error(tresp)
        norm = ff.normalize_command(cmd)
        counts = st.get("cmd_counts", {})
        counts[norm] = counts.get(norm, 0) + 1
        if len(counts) > 200:  # bound state size
            counts = dict(sorted(counts.items(), key=lambda kv: -kv[1])[:100])
        st["cmd_counts"] = counts

        if ff.is_verify_command(cmd, cfg):
            st["verify_seen"] = True
            if err:
                st["last_verify"] = "fail"
                ff.log_event(payload, "verify", result="fail", cmd=cmd[:160])
            else:
                st["last_verify"] = "pass"
                st["edits_since_verify"] = 0
                ff.log_event(payload, "verify", result="pass", cmd=cmd[:160])
            # custom verifier (not a standard runner): remember it for the
            # project so every future session tracks it without setup
            if not ff.VERIFY_RE.search(cmd) and ff.VERIFY_HEUR_RE.search(cmd):
                if ff.register_verifier(payload, cmd):
                    ff.log_event(payload, "verifier_registered", cmd=cmd[:160])

        if err:
            dg = ff.digest(err[:200])
            streaks = st.get("error_streaks", {})
            streaks[dg] = streaks.get(dg, 0) + 1
            if len(streaks) > 50:
                streaks = dict(sorted(streaks.items(), key=lambda kv: -kv[1])[:25])
            st["error_streaks"] = streaks
            ff.log_event(payload, "tool_error", digest=dg, cmd=cmd[:160],
                         err=err[:200])
            if streaks[dg] == 2 or streaks[dg] == 4:
                nudge = STRATEGY_NUDGE % (streaks[dg], dg[:8])

    else:
        err = ff.tool_response_error(tresp)
        if err:
            ff.log_event(payload, "tool_error", tool=tool, err=err[:200])

    ff.save_state(payload, st)

    if nudge:
        ff.emit({
            "suppressOutput": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": nudge,
            },
        })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
