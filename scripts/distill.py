"""Firefly distiller: turn raw session events into improvement CANDIDATES.

Runs at SessionEnd (cheap, deterministic - no LLM). Candidates land in
.firefly/candidates.jsonl and are reviewed by the reflector agent during
/ff:retro, which converts the worthy ones into playbook proposals.

Signals mined from events.jsonl + session state:
  error_streak    same error digest >= 2 times       -> candidate(friction)
  repeated_cmd    same normalized command >= 3 times  -> candidate(automation)
  corrections     user corrected the model >= 2 times -> candidate(behavior)
  guard_denials   guard denied >= 1 destructive cmd   -> candidate(safety)
  win             verify pass after >=3 edits         -> candidate(win)
"""

import os
import sys

try:
    import lib_firefly as ff
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lib_firefly as ff

CANDIDATE_CAP = 200


def _cand_path(payload):
    return os.path.join(ff.firefly_dir(payload), "candidates.jsonl")


def _existing_keys(payload):
    return {c.get("key") for c in ff.read_jsonl(_cand_path(payload))}


def _mk(payload, kind, key, summary, evidence, seen):
    if not key or key in seen:
        return None
    seen.add(key)
    return {
        "ts": ff.now_iso(),
        "sid": payload.get("session_id", ""),
        "kind": kind,
        "key": key,
        "summary": summary[:300],
        "evidence": evidence[:3],
        "status": "new",
    }


def distill_session(payload, state):
    """Mine one session's state + recent events. Returns count of new candidates."""
    seen = _existing_keys(payload)
    out = []

    for dg, count in (state.get("error_streaks") or {}).items():
        if count >= 2:
            out.append(_mk(payload, "friction", "err:" + dg,
                           "Same error repeated %dx (digest %s). A lesson or fix "
                           "recipe could prevent the retry loop." % (count, dg),
                           [e for e in _recent_events(payload, "tool_error", dg)], seen))

    for cmd, count in (state.get("cmd_counts") or {}).items():
        if count >= 3:
            key = "cmd:" + ff.digest(cmd, 10)
            out.append(_mk(payload, "automation", key,
                           "Command pattern ran %dx this session: `%s`. Candidate "
                           "for a skill, alias, or checklist step." % (count, cmd),
                           [cmd], seen))

    if state.get("corrections", 0) >= 2:
        out.append(_mk(payload, "behavior",
                       "corr:" + str(state.get("session_id", ""))[:12],
                       "User corrected the assistant %d times this session. Review "
                       "what instruction was repeatedly violated." % state["corrections"],
                       [], seen))

    denials = _recent_events(payload, "guard_deny", None, sid=state.get("session_id"))
    if denials:
        out.append(_mk(payload, "safety",
                       "deny:" + str(state.get("session_id", ""))[:12],
                       "Safety guard denied %d command(s). If these were legitimate, "
                       "config allow_extra or protected lists may need tuning." % len(denials),
                       denials[:3], seen))

    if state.get("verify_seen") and state.get("last_verify") == "pass" \
            and len(state.get("edited_files", [])) >= 3:
        out.append(_mk(payload, "win",
                       "win:" + str(state.get("session_id", ""))[:12],
                       "Verified multi-file change landed (%d files, tests pass). The "
                       "approach used may be worth a reusable lesson."
                       % len(state.get("edited_files", [])),
                       state.get("edited_files", [])[:3], seen))

    new = [c for c in out if c]
    for c in new:
        ff.append_jsonl(_cand_path(payload), c)
    _trim(payload)
    return len(new)


def _recent_events(payload, ev, dg, sid=None, limit=3):
    evs = ff.read_jsonl(os.path.join(ff.firefly_dir(payload), "events.jsonl"), limit=400)
    hits = []
    for e in evs:
        if e.get("ev") != ev:
            continue
        if dg and e.get("digest") != dg:
            continue
        if sid and e.get("sid") != sid:
            continue
        hits.append((e.get("detail") or e.get("cmd") or e.get("err") or "")[:160])
    return hits[-limit:]


def _trim(payload):
    """Keep candidates.jsonl bounded; drop oldest resolved/duplicates first."""
    p = _cand_path(payload)
    cands = ff.read_jsonl(p)
    if len(cands) <= CANDIDATE_CAP:
        return
    keep = [c for c in cands if c.get("status") == "new"][-CANDIDATE_CAP:]
    try:
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for c in keep:
                f.write(__import__("json").dumps(c, ensure_ascii=False) + "\n")
        os.replace(tmp, p)
    except Exception:
        pass


def pending_count(payload):
    return sum(1 for c in ff.read_jsonl(_cand_path(payload))
               if c.get("status") == "new")


def mark_processed(payload, keys):
    """Called by /ff:retro flow (via curator CLI) after reflector reviewed them."""
    p = _cand_path(payload)
    cands = ff.read_jsonl(p)
    keys = set(keys)
    for c in cands:
        if c.get("key") in keys:
            c["status"] = "processed"
    try:
        import json as _json
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for c in cands:
                f.write(_json.dumps(c, ensure_ascii=False) + "\n")
        os.replace(tmp, p)
    except Exception:
        pass


if __name__ == "__main__":
    payload = {"cwd": os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())}
    if len(sys.argv) > 2 and sys.argv[1] == "mark":
        mark_processed(payload, sys.argv[2].split(","))
        print("marked")
    else:
        print("pending candidates: %d" % pending_count(payload))
