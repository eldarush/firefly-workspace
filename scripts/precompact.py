"""PreCompact hook: write a handoff snapshot before context is compacted.

The snapshot (.firefly/handoff.md) is re-injected by session_start.py when the
post-compact session starts, preserving task continuity across the reset.
Matcher: manual|auto. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)

    lines = [
        "# Firefly handoff (auto-saved at %s compaction, %s)" % (
            payload.get("trigger", "auto"), ff.now_iso()),
        "",
        "State that survives the context reset:",
        "- Turns so far: %d | corrections: %d" % (
            st.get("turns", 0), st.get("corrections", 0)),
        "- Edits since last successful verify: %d" % st.get("edits_since_verify", 0),
        "- Last verify result: %s" % (st.get("last_verify") or "never ran"),
    ]
    files = st.get("edited_files", [])
    if files:
        lines.append("- Files edited this session:")
        for f in files[-15:]:
            lines.append("  - %s" % f)

    plan = os.path.join(ff.firefly_dir(payload), "plan.md")
    if os.path.exists(plan):
        lines.append("- Active plan: .firefly/plan.md (re-read it before continuing)")

    lines += [
        "",
        "First actions after compaction: re-read .firefly/plan.md if present, run "
        "`git status` + `git diff --stat` to re-ground in reality, then continue "
        "the CURRENT task only. Do not start new work the user did not ask for.",
    ]

    try:
        path = os.path.join(ff.firefly_dir(payload), "handoff.md")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        os.replace(tmp, path)
    except Exception:
        pass
    ff.log_event(payload, "precompact", trigger=payload.get("trigger", ""))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
