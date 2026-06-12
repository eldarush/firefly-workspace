"""SessionEnd hook: distill the finished session into improvement candidates.

Runs the deterministic distiller (no LLM) over session state + events, then
logs a session summary event. Heavyweight reflection happens later via
/ff:retro, with a human in the loop. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import lib_firefly as ff
    import distill

    payload = ff.read_hook_input()
    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)

    new = 0
    try:
        new = distill.distill_session(payload, st)
    except Exception:
        pass

    ff.log_event(payload, "session_end",
                 reason=payload.get("reason", ""),
                 turns=st.get("turns", 0),
                 corrections=st.get("corrections", 0),
                 candidates=new or None)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
