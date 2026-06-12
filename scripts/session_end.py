"""SessionEnd hook: close the automatic learning loop for this session.

1. Distill session state + events into improvement candidates (no LLM).
2. auto_propose: signals recurring across sessions become quarantined lesson
   proposals deterministically.
3. implicit_feedback: a verified, correction-free session gives +1 helpful to
   every lesson that was injected at SessionStart.
All proposals are applied by the curator at the next SessionStart. /ff:retro
remains the manual deep pass. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import lib_firefly as ff
    import distill

    payload = ff.read_hook_input()
    cfg = ff.load_config(payload)
    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)

    new = auto = fb = tn = tf = 0
    try:
        new = distill.distill_session(payload, st)
    except Exception:
        pass
    try:
        auto = distill.auto_propose(payload, cfg)
    except Exception:
        pass
    try:
        fb = distill.implicit_feedback(payload, st, cfg)
    except Exception:
        pass

    # team loop: silently share locally-proven lessons; thank teammates whose
    # lessons were injected into a session that ended clean and verified
    try:
        import team
        tn = team.share_promoted(payload, cfg)
        if (st.get("corrections", 0) == 0 and st.get("verify_seen")
                and st.get("last_verify") == "pass"):
            tf = team.record_team_feedback(
                payload, cfg, st.get("injected_team_lessons") or [], "helpful")
    except Exception:
        pass

    ff.log_event(payload, "session_end",
                 reason=payload.get("reason", ""),
                 turns=st.get("turns", 0),
                 corrections=st.get("corrections", 0),
                 candidates=new or None,
                 auto_lessons=auto or None,
                 auto_feedback=fb or None,
                 team_shared=tn or None,
                 team_feedback=tf or None)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
