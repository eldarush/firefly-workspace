"""Stop hook: verification gate + automatic reflection (auto-retro).

1) Verification gate - blocks a premature "I'm done" ONLY when ALL are true:
   - config behavior.stop_gate is enabled
   - stop_hook_active is False (avoid infinite loops - hard requirement)
   - code files were edited since the last successful verifier run
   - a verifier is known (config verify.commands, or one was seen this session)
   - we have blocked < max_stop_blocks_per_session times already

2) Auto-retro - when the session produced enough learnable signal, block ONCE
   (per session) asking the model to distill fresh candidates into playbook
   delta-ops appended to .firefly/proposals.jsonl. This makes learning
   automatic: no /ff:retro needed. The deterministic curator still validates,
   dedups and quarantines everything the model proposes.

Otherwise exits silently. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REFLECT_SCHEMA = (
    '{"op":"add","scope":"global|sre|qa|dev|research","tags":["tag1","tag2"],'
    '"lesson":"imperative, checkable, <=300 chars","evidence":["<sid>: why"],'
    '"actor":"reflector"}'
)


def _verification_gate(ff, payload, cfg, st):
    """Returns True when it emitted a block (caller must stop)."""
    beh = cfg.get("behavior", {})
    if not beh.get("stop_gate", True):
        return False

    edits = st.get("edits_since_verify", 0)
    if edits <= 0:
        return False

    verifier_cmds = (cfg.get("verify", {}) or {}).get("commands", [])
    verifier_known = bool(verifier_cmds) or st.get("verify_seen", False)
    max_blocks = int(beh.get("max_stop_blocks_per_session", 2))

    if not verifier_known or st.get("stop_blocks", 0) >= max_blocks:
        # soft note instead of a block
        ff.log_event(payload, "stop_soft", edits=edits)
        return False

    st["stop_blocks"] = st.get("stop_blocks", 0) + 1
    ff.save_state(payload, st)
    ff.log_event(payload, "stop_block", edits=edits, n=st["stop_blocks"])

    hint = verifier_cmds[0] if verifier_cmds else "the test/lint command you ran earlier"
    ff.emit({
        "decision": "block",
        "reason": ("Firefly verification gate: %d code edit(s) since the last "
                   "successful verification. Run the project's verifier (%s), show "
                   "its real output, and fix failures before finishing. If "
                   "verification is truly impossible right now, say so explicitly "
                   "and tell the user what evidence is missing." % (edits, hint)),
    })
    return True


def _auto_reflect(ff, payload, cfg, st):
    """Once per session, turn fresh signals into playbook proposals."""
    lcfg = cfg.get("learning", {})
    if not lcfg.get("auto_reflect", True):
        return
    if st.get("reflected"):
        return
    if st.get("turns", 0) < int(lcfg.get("auto_reflect_min_turns", 3)):
        return

    import distill
    # Mine now so Stop sees this session's signals; keyed dedup makes the
    # SessionEnd re-run a no-op for anything already captured here.
    distill.distill_session(payload, st)
    sid = st.get("session_id", "")
    fresh = distill.fresh_candidates(payload, sid)
    if len(fresh) < int(lcfg.get("auto_reflect_min_candidates", 2)):
        return

    st["reflected"] = True
    ff.save_state(payload, st)
    ff.log_event(payload, "auto_reflect", n=len(fresh))

    lines = ["- [%s] %s" % (c.get("kind", "?"), c.get("summary", "")[:160])
             for c in fresh[:4]]
    props = os.path.join(".firefly", "proposals.jsonl")
    ff.emit({
        "decision": "block",
        "reason": (
            "Firefly auto-retro (automatic, once per session - the user did not "
            "ask for this, keep it nearly invisible). This session produced "
            "learnable signals:\n%s\n"
            "Distill AT MOST 3 durable lessons (imperative, checkable, "
            "generalizable beyond this incident, <=300 chars each). Append one "
            "JSON object per line to %s using a single shell append, schema:\n%s\n"
            "Quality bar: skip one-off noise, tool flakes, and anything already "
            "in the playbook lessons you were shown at session start. If "
            "nothing is durable, append nothing. Then stop with at most one "
            "short status line to the user (e.g. 'Captured 2 lessons for the "
            "playbook.')." % ("\n".join(lines), props, REFLECT_SCHEMA)
        ),
    })


def _team_confirm(ff, payload, cfg, st):
    """Once per session: before this session's fresh lessons go anywhere
    near the shared team store, make Claude ask the USER. A 'no' is captured
    as a corrective lesson - the strongest learning signal we can get."""
    tcfg = cfg.get("team", {}) or {}
    if not (tcfg.get("enabled", True) and tcfg.get("confirm_save", True)):
        return
    if st.get("team_confirm_asked") or st.get("team_confirmed"):
        return
    if st.get("turns", 0) < 3:
        return

    import team
    if not team.resolve_team_dir(payload, cfg):
        return
    pending = team.pending_share_ops(payload, limit=3)
    if not pending:
        return

    st["team_confirm_asked"] = True
    ff.save_state(payload, st)
    ff.log_event(payload, "team_confirm", n=len(pending))

    share = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "team_share.py")
    lines = ["- %s" % p.get("lesson", "")[:160] for p in pending]
    ff.emit({
        "decision": "block",
        "reason": (
            "Firefly team-learning checkpoint (once per session). This "
            "session distilled lesson(s) that could be shared with the whole "
            "team:\n%s\n"
            "ASK THE USER now, in one short message: 'Save these lessons to "
            "the team store so they improve Firefly for everyone? (yes / no - "
            "and if no, what should I have done differently?)' Do NOT decide "
            "for them; wait for their answer, then run exactly one of:\n"
            "  py \"%s\" --yes\n"
            "  py \"%s\" --no --correction \"<their words>\"\n"
            "A 'no' with a correction is just as valuable - it becomes the "
            "lesson. Then finish normally." % ("\n".join(lines), share, share)
        ),
    })


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    if payload.get("stop_hook_active"):
        return

    cfg = ff.load_config(payload)
    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)

    if _verification_gate(ff, payload, cfg, st):
        return

    try:
        if st.get("reflected") and not st.get("team_confirm_asked"):
            _team_confirm(ff, payload, cfg, st)
            return
        _auto_reflect(ff, payload, cfg, st)
        if not st.get("reflected"):
            # nothing to reflect on this stop - lessons may already be pending
            # from the deterministic distiller, so still offer the team ask
            _team_confirm(ff, payload, cfg, st)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
