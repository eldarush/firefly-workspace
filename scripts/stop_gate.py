"""Stop hook: the verification gate.

Blocks a premature "I'm done" ONLY when ALL are true:
  - config behavior.stop_gate is enabled
  - stop_hook_active is False (avoid infinite loops - hard requirement)
  - code files were edited since the last successful verifier run
  - a verifier is known (config verify.commands, or one was seen this session)
  - we have blocked < max_stop_blocks_per_session times already
Otherwise exits silently. Fail-open always.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import lib_firefly as ff

    payload = ff.read_hook_input()
    if payload.get("stop_hook_active"):
        return

    cfg = ff.load_config(payload)
    beh = cfg.get("behavior", {})
    if not beh.get("stop_gate", True):
        return

    sid = payload.get("session_id", "unknown")
    st = ff.load_state(payload, sid)

    edits = st.get("edits_since_verify", 0)
    if edits <= 0:
        return

    verifier_cmds = (cfg.get("verify", {}) or {}).get("commands", [])
    verifier_known = bool(verifier_cmds) or st.get("verify_seen", False)
    max_blocks = int(beh.get("max_stop_blocks_per_session", 2))

    if not verifier_known or st.get("stop_blocks", 0) >= max_blocks:
        # soft note instead of a block
        ff.log_event(payload, "stop_soft", edits=edits)
        return

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


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
