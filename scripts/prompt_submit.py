"""UserPromptSubmit hook: lightweight prompt coaching + correction tracking.

- counts turns; detects user corrections (signal for the distiller)
- applies any pending playbook proposals (so auto-retro and /ff:retro output lands fast)
- injects a ~120-token task frame when the prompt opens a new nontrivial task
  (rate-limited: at most once per 8 turns, skippable via config)
Fail-open always; never blocks a prompt.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FRAME = """Before acting on this task: (1) restate it in one sentence and list \
unstated assumptions; (2) define what DONE looks like (acceptance criteria + the \
verifier command you will run); (3) pick the single objective for this turn; \
(4) prefer the smallest correct change. If requirements are ambiguous, ask the \
one most important clarifying question instead of guessing."""

FRAME_SHORT = """New phase: confirm your .firefly/plan.md still matches (update it \
if scope changed), state this turn's single objective, and name the verifier \
you will run before claiming done."""

CORRECTION_NUDGE = """The user is correcting you. Stop, re-read their last two \
messages, state in one sentence what you got wrong, and fix THAT - do not defend \
the previous approach or repeat it."""

_TRIVIAL_PREFIXES = (
    "y", "yes", "no", "ok", "okay", "sure", "thanks", "thank you", "continue",
    "go", "go ahead", "do it", "proceed", "next", "lgtm", "good", "nice", "great",
)


def _nontrivial_task(prompt):
    p = (prompt or "").strip().lower()
    if len(p) < 60:
        return False
    if p.startswith("/"):
        return False
    if any(p == t or p.startswith(t + " ") or p.startswith(t + ",") for t in _TRIVIAL_PREFIXES):
        return False
    action_words = ("implement", "create", "build", "add", "fix", "refactor", "write",
                    "debug", "investigate", "migrate", "deploy", "design", "set up",
                    "setup", "configure", "convert", "optimize", "upgrade", "make")
    return any(w in p for w in action_words)


def main():
    import lib_firefly as ff
    import curator

    payload = ff.read_hook_input()
    cfg = ff.load_config(payload)
    prompt = payload.get("prompt", "") or ""
    sid = payload.get("session_id", "unknown")

    st = ff.load_state(payload, sid)
    st["turns"] = st.get("turns", 0) + 1

    try:
        curator.consume_proposals(payload, cfg)
    except Exception:
        pass

    extra = []
    corrected = ff.looks_like_correction(prompt)
    if corrected:
        st["corrections"] = st.get("corrections", 0) + 1
        ff.log_event(payload, "correction", digest=ff.digest(prompt[:200]))
        if st["corrections"] <= 3:
            extra.append(CORRECTION_NUDGE)

    if (not corrected
            and cfg.get("behavior", {}).get("prompt_frame", True)
            and _nontrivial_task(prompt)
            and st["turns"] - st.get("last_frame_turn", -99) >= 8):
        st["last_frame_turn"] = st["turns"]
        st["frames_injected"] = st.get("frames_injected", 0) + 1
        # once a plan exists and the full drill ran, later phases get a
        # short nudge instead of the whole restate ceremony (wave-2 finding:
        # the full frame re-firing mid-task reads as redundant ritual)
        plan_path = os.path.join(ff.firefly_dir(payload), "plan.md")
        if st["frames_injected"] > 1 and os.path.exists(plan_path):
            extra.append(FRAME_SHORT)
        else:
            extra.append(FRAME)

    ff.log_event(payload, "prompt", n=st["turns"],
                 digest=ff.digest(prompt[:200]), corr=corrected or None)
    ff.save_state(payload, st)

    if extra:
        ff.emit({
            "suppressOutput": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": "\n\n".join(extra),
            },
        })


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
