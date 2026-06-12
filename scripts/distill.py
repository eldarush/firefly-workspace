"""Firefly distiller: turn raw session events into improvement CANDIDATES
and AUTOMATIC playbook proposals.

Runs at SessionEnd and at the Stop auto-retro (cheap, deterministic - no LLM).
Candidates land in .firefly/candidates.jsonl. Three automatic paths consume
them with zero user action:
  1. Stop-hook auto-retro: the model is asked (once per session) to distill
     fresh candidates into delta-ops -> proposals.jsonl.
  2. auto_propose(): signals recurring across >= min_recurrence sessions are
     converted into quarantined lessons deterministically (template text).
  3. implicit_feedback(): lessons injected into a session that ends verified
     and correction-free earn +1 helpful automatically.
/ff:retro remains as the manual DEEP pass with a human in the loop.

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


def _props_path(payload):
    return os.path.join(ff.firefly_dir(payload), "proposals.jsonl")


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


def fresh_candidates(payload, sid):
    """Candidates produced by THIS session, still unprocessed."""
    return [c for c in ff.read_jsonl(_cand_path(payload))
            if c.get("status") == "new" and c.get("sid") == sid]


def _set_status(payload, keys, status):
    p = _cand_path(payload)
    cands = ff.read_jsonl(p)
    keys = set(keys)
    changed = False
    for c in cands:
        if c.get("key") in keys and c.get("status") == "new":
            c["status"] = status
            changed = True
    if not changed:
        return
    try:
        import json as _json
        tmp = p + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            for c in cands:
                f.write(_json.dumps(c, ensure_ascii=False) + "\n")
        os.replace(tmp, p)
    except Exception:
        pass


def mark_processed(payload, keys):
    """Called by /ff:retro flow (via curator CLI) after reflector reviewed them."""
    _set_status(payload, keys, "processed")


# ---------------------------------------------------------------------------
# automatic learning (no LLM, no user action)
# ---------------------------------------------------------------------------


def auto_propose(payload, cfg=None):
    """Deterministic cross-session learning: a signal that recurs in
    >= learning.min_recurrence distinct sessions becomes a quarantined lesson
    proposal with templated text. Repeats after promotion dedup into +helpful
    via the curator, reinforcing the lesson toward activation. Returns count."""
    cfg = cfg or ff.load_config(payload)
    lcfg = cfg.get("learning", {})
    if not lcfg.get("auto_lessons", True):
        return 0
    min_rec = max(2, int(lcfg.get("min_recurrence", 2)))

    new = [c for c in ff.read_jsonl(_cand_path(payload))
           if c.get("status") == "new"]
    by_key, by_kind = {}, {}
    for c in new:
        k = c.get("key") or ""
        if k.startswith(("err:", "cmd:")):
            by_key.setdefault(k, []).append(c)
        elif k.startswith(("corr:", "deny:")):
            by_kind.setdefault(c.get("kind", ""), []).append(c)

    emitted, promoted = 0, set()

    def emit(lesson, tags, group):
        evidence = [(str(c.get("sid", ""))[:12] + ": "
                     + str(c.get("summary", "")))[:120] for c in group[:2]]
        ok = ff.append_jsonl(_props_path(payload), {
            "op": "add", "scope": "global", "tags": tags,
            "lesson": lesson[:300], "evidence": evidence,
            "actor": "auto", "origin": "auto",
        })
        if ok:
            promoted.update(c.get("key") for c in group)
            return 1
        return 0

    for key, group in sorted(by_key.items()):
        if len({c.get("sid") for c in group}) < min_rec:
            continue
        first = group[0]
        ev = (first.get("evidence") or [""])[0][:110] or first.get("summary", "")[:110]
        if key.startswith("err:"):
            emitted += emit(
                "Known recurring failure here: %s - check this failure mode "
                "and fix the root cause before retrying." % ev,
                ["friction", "auto"], group)
        else:
            emitted += emit(
                "Recurring workflow across sessions: `%s` - reuse the "
                "established pattern; strong candidate for a skill "
                "(/ff:skillgen)." % ev,
                ["automation", "auto"], group)

    for kind, group in sorted(by_kind.items()):
        if len({c.get("sid") for c in group}) < min_rec:
            continue
        if kind == "behavior":
            emitted += emit(
                "User corrections recur across sessions in this repo. Restate "
                "the request and confirm the approach BEFORE multi-step "
                "changes; re-read the last user message when corrected.",
                ["behavior", "auto"], group)
        elif kind == "safety":
            emitted += emit(
                "Destructive/protected commands are repeatedly denied here. "
                "Default to read-only diagnosis and Git-based change "
                "proposals; if denials were legitimate work, tune "
                ".firefly/config.json allow_extra.",
                ["safety", "auto"], group)

    if promoted:
        _set_status(payload, promoted, "promoted")
    return emitted


def implicit_feedback(payload, st, cfg=None):
    """Sessions that end verified-green with zero corrections count as evidence
    that the injected lessons helped. +1 helpful each (curator applies next
    session; quarantined trials auto-activate at >=2 helpful, 0 harmful)."""
    cfg = cfg or ff.load_config(payload)
    if not cfg.get("learning", {}).get("auto_feedback", True):
        return 0
    if st.get("corrections", 0) != 0:
        return 0
    if not (st.get("verify_seen") and st.get("last_verify") == "pass"):
        return 0
    if st.get("turns", 0) < 3:
        return 0
    n = 0
    for lid in (st.get("injected_lessons") or [])[:6]:
        if ff.append_jsonl(_props_path(payload), {
                "op": "feedback", "id": lid, "helpful": 1,
                "evidence": "implicit: clean verified session %s"
                            % str(st.get("session_id", ""))[:12],
                "actor": "auto"}):
            n += 1
    return n


if __name__ == "__main__":
    payload = {"cwd": os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())}
    if len(sys.argv) > 2 and sys.argv[1] == "mark":
        mark_processed(payload, sys.argv[2].split(","))
        print("marked")
    else:
        print("pending candidates: %d" % pending_count(payload))
