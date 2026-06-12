#!/usr/bin/env python3
"""team_share - record the user's decision about sharing session learnings.

    py <plugin>/scripts/team_share.py --yes
    py <plugin>/scripts/team_share.py --no --correction "<what to do instead>"
    py <plugin>/scripts/team_share.py --status

Claude runs this AFTER asking the user (the Stop hook prompts for it once
per session when fresh learnings exist and a team store is configured).

--yes  shares this session's pending lesson proposals to the team store
       (.firefly-team/ or $FIREFLY_TEAM_DIR), attributed to you, so every
       team member's Firefly benefits.
--no   does NOT share - and the correction you pass becomes the real lesson:
       it is filed as a high-priority corrective proposal in the LOCAL
       playbook (tagged 'correction'), because "what the model should have
       done differently" is the most valuable training signal there is.

Stdlib only, fail-open, exit 0 always (a broken share must never break a
session).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_firefly as ff  # noqa: E402
import team  # noqa: E402


def _payload():
    return {
        "session_id": os.environ.get("FF_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID") or "team-share",
        "cwd": os.getcwd(),
        "hook_event_name": "TeamShare",
    }


def main():
    args = sys.argv[1:]
    payload = _payload()
    cfg = ff.load_config(payload)
    sid = payload["session_id"]
    st = ff.load_state(payload, sid)

    if "--status" in args:
        d = team.resolve_team_dir(payload, cfg)
        data = team.load_team(d) if d else {"lessons": {}, "votes": {}}
        print("team store: %s" % (d or "(not configured - create .firefly-team/ "
                                       "or set FIREFLY_TEAM_DIR)"))
        print("shared lessons: %d" % len(data["lessons"]))
        for lid, rec in sorted(data["lessons"].items())[:20]:
            v = data["votes"].get(lid, {"helpful": 0, "harmful": 0})
            print("- [%s +%d/-%d] (%s) %s" % (rec.get("origin", "?"),
                                              v["helpful"], v["harmful"],
                                              rec.get("author", "?"),
                                              rec.get("lesson", "")[:120]))
        return

    if "--yes" in args:
        pending = team.confirmable_lessons(payload, cfg, limit=6)
        n = team.share_lessons(payload, cfg, pending, origin="confirmed")
        st["team_confirmed"] = "yes"
        ff.save_state(payload, st)
        ff.log_event(payload, "team_share_yes", n=n)
        if n:
            print("Shared %d lesson(s) to the team store. Teammates pick them "
                  "up at their next session start." % n)
        else:
            print("Nothing new to share (already shared or no pending lessons).")
        return

    if "--no" in args:
        correction = ""
        if "--correction" in args:
            i = args.index("--correction")
            correction = " ".join(args[i + 1:]).strip().strip('"')
        st["team_confirmed"] = "no"
        ff.save_state(payload, st)
        ff.log_event(payload, "team_share_no",
                     corrected=bool(correction) or None)
        if correction:
            ff.append_jsonl(
                os.path.join(ff.firefly_dir(payload), "proposals.jsonl"),
                {"op": "add", "scope": "global", "tags": ["correction"],
                 "lesson": correction[:300],
                 "evidence": ["user rejected session learnings %s" % sid[:12]],
                 "actor": "user"})
            print("Not shared. Filed the correction as a high-priority lesson "
                  "proposal - the playbook learns what you actually wanted.")
        else:
            print("Not shared. (Tip: pass --correction \"...\" so Firefly "
                  "learns what it should have done differently.)")
        return

    print(__doc__)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
