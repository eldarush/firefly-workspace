"""Team learning store: lessons shared across Firefly team members.

Design (airgapped, stdlib-only, fail-open):
- The store is a DIRECTORY shared between members - a git-committed
  `.firefly-team/` in the repo (merge via append-only files) or any shared
  filesystem path (NFS/SMB) via config `team.dir` or $FIREFLY_TEAM_DIR.
- Append-only, per-author files: `lessons/<author>.jsonl`. Each member writes
  ONLY to their own file, so git merges and concurrent NFS writes never
  conflict. Readers fold all files.
- Records are content-addressed (id = tl-<digest of normalized text>), so the
  same lesson shared by two members dedups to one entry with combined votes.
- Two record kinds per line:
    {"kind":"lesson","id":...,"lesson":...,"scope":...,"tags":[...],
     "author":...,"ts":...,"origin":"confirmed|promoted|correction"}
    {"kind":"feedback","id":<lesson id>,"vote":"helpful|harmful",
     "author":...,"ts":...}
- Sharing is gated: fresh session learnings are shared only after the USER
  confirms (stop-hook ask, see stop_gate.py + team_share.py); locally PROVEN
  lessons (helpful >= team.share_threshold, active, 0 harmful) auto-share at
  SessionEnd because they already earned trust.
- Consumption: SessionStart injects top-K teammate lessons (deduped against
  the local playbook); clean verified sessions append +helpful feedback for
  the team lessons they saw (implicit, mirrors local auto_feedback).
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import lib_firefly as ff


# ---------------------------------------------------------------- resolution

def resolve_team_dir(payload=None, cfg=None, create=False):
    """Shared store dir or None when the team loop is dormant.

    Order: config team.dir > $FIREFLY_TEAM_DIR > <project>/.firefly-team
    (the last only when the directory already exists - creating it is the
    team's explicit opt-in, e.g. `mkdir .firefly-team && git add`).
    """
    cfg = cfg or ff.load_config(payload)
    t = cfg.get("team", {}) or {}
    if not t.get("enabled", True):
        return None
    d = (t.get("dir") or "").strip() or os.environ.get("FIREFLY_TEAM_DIR", "").strip()
    if d:
        if not os.path.isabs(d):
            d = os.path.join(ff.project_dir(payload), d)
        if create:
            try:
                os.makedirs(os.path.join(d, "lessons"), exist_ok=True)
            except OSError:
                return None
        return d
    d = os.path.join(ff.project_dir(payload), ".firefly-team")
    if os.path.isdir(d):
        if create:
            try:
                os.makedirs(os.path.join(d, "lessons"), exist_ok=True)
            except OSError:
                return None
        return d
    return None


def resolve_author(cfg=None):
    """Attribution for shared records. Config > env > git > OS user."""
    cfg = cfg or {}
    a = ((cfg.get("team", {}) or {}).get("author") or "").strip()
    if a:
        return a
    a = os.environ.get("FIREFLY_AUTHOR", "").strip()
    if a:
        return a
    try:
        out = subprocess.run(["git", "config", "user.name"],
                             capture_output=True, text=True, timeout=3)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _author_slug(author):
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", author.strip()).strip("-").lower()
    return s or "unknown"


def _author_file(team_dir, author):
    return os.path.join(team_dir, "lessons", "%s.jsonl" % _author_slug(author))


def lesson_id(text):
    norm = re.sub(r"\s+", " ", (text or "").strip().lower())
    return "tl-" + ff.digest(norm, 10)


# ----------------------------------------------------------------- write API

def share_lessons(payload, cfg, lessons, origin):
    """Append lesson records to the caller's own team file. Returns count."""
    team_dir = resolve_team_dir(payload, cfg, create=True)
    if not team_dir or not lessons:
        return 0
    author = resolve_author(cfg)
    path = _author_file(team_dir, author)
    n = 0
    seen = {r.get("id") for r in load_team(team_dir)["lessons"].values()}
    for l in lessons[:6]:
        text = (l.get("lesson") or "").strip()
        if not text:
            continue
        lid = lesson_id(text)
        if lid in seen:
            continue
        rec = {"kind": "lesson", "id": lid, "lesson": text[:400],
               "scope": l.get("scope", "global"),
               "tags": list(l.get("tags", []))[:5],
               "author": author, "ts": ff.now_iso(),
               "origin": origin}
        if ff.append_jsonl(path, rec):
            seen.add(lid)
            n += 1
    if n:
        ff.log_event(payload, "team_share", n=n, origin=origin)
    return n


def record_team_feedback(payload, cfg, lesson_ids, vote="helpful"):
    """Append feedback votes (to MY author file - append-only discipline)."""
    team_dir = resolve_team_dir(payload, cfg, create=True)
    if not team_dir or not lesson_ids:
        return 0
    author = resolve_author(cfg)
    path = _author_file(team_dir, author)
    n = 0
    for lid in lesson_ids[:6]:
        if ff.append_jsonl(path, {"kind": "feedback", "id": lid, "vote": vote,
                                  "author": author, "ts": ff.now_iso()}):
            n += 1
    return n


# ------------------------------------------------------------------ read API

def load_team(team_dir):
    """Fold every author file into {'lessons': {id: rec}, 'votes': {id: {...}}}."""
    out = {"lessons": {}, "votes": {}}
    ldir = os.path.join(team_dir or "", "lessons")
    if not team_dir or not os.path.isdir(ldir):
        return out
    try:
        names = sorted(os.listdir(ldir))
    except OSError:
        return out
    for name in names:
        if not name.endswith(".jsonl"):
            continue
        for rec in ff.read_jsonl(os.path.join(ldir, name), limit=2000):
            if not isinstance(rec, dict):
                continue
            lid = rec.get("id")
            if not lid:
                continue
            kind = rec.get("kind")
            if kind == "lesson" and lid not in out["lessons"]:
                out["lessons"][lid] = rec
            elif kind == "feedback":
                v = out["votes"].setdefault(lid, {"helpful": 0, "harmful": 0})
                if rec.get("vote") == "harmful":
                    v["harmful"] += 1
                else:
                    v["helpful"] += 1
    return out


def select_team_for_injection(payload, cfg=None):
    """Top-K teammate lessons worth injecting: not duplicated by the local
    playbook, not voted harmful, best (votes, recency) first."""
    cfg = cfg or ff.load_config(payload)
    team_dir = resolve_team_dir(payload, cfg)
    if not team_dir:
        return []
    data = load_team(team_dir)
    if not data["lessons"]:
        return []

    import curator
    try:
        pb = curator.load_playbook(payload)
        local = [l.get("lesson", "") for l in pb.get("lessons", [])
                 if l.get("status") in ("active", "quarantined")]
    except Exception:
        local = []

    k = int((cfg.get("team", {}) or {}).get("max_inject", 3))
    scored = []
    for lid, rec in data["lessons"].items():
        votes = data["votes"].get(lid, {"helpful": 0, "harmful": 0})
        if votes["harmful"] >= votes["helpful"] + 2:
            continue
        text = rec.get("lesson", "")
        if any(curator._jaccard(curator._stem(text), curator._stem(t)) >= 0.75
               for t in local):
            continue  # already known locally
        base = 2.0 if rec.get("origin") in ("promoted", "correction") else 1.0
        scored.append((base + votes["helpful"] - 2.0 * votes["harmful"],
                       rec.get("ts", ""), lid, rec))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [rec for _, _, _, rec in scored[:max(0, k)]]


# ------------------------------------------------- session-boundary plumbing

def pending_share_ops(payload, limit=3):
    """Fresh op:add proposals awaiting the user's share decision."""
    path = os.path.join(ff.firefly_dir(payload), "proposals.jsonl")
    out = []
    for rec in ff.read_jsonl(path, limit=200):
        if isinstance(rec, dict) and rec.get("op") == "add" and rec.get("lesson"):
            out.append({"lesson": rec.get("lesson", ""),
                        "scope": rec.get("scope", "global"),
                        "tags": rec.get("tags", [])})
    return out[-limit:]


def share_promoted(payload, cfg=None):
    """SessionEnd auto-share: locally PROVEN lessons go to the team silently.
    A lesson qualifies once active with helpful >= team.share_threshold and
    zero harmful - it earned trust through the local curator gauntlet."""
    cfg = cfg or ff.load_config(payload)
    team_dir = resolve_team_dir(payload, cfg)
    if not team_dir:
        return 0
    thr = int((cfg.get("team", {}) or {}).get("share_threshold", 2))
    import curator
    try:
        pb = curator.load_playbook(payload)
    except Exception:
        return 0
    ripe = [l for l in pb.get("lessons", [])
            if l.get("status") == "active"
            and l.get("helpful", 0) >= thr and l.get("harmful", 0) == 0]
    known = set(load_team(team_dir)["lessons"])
    ripe = [l for l in ripe if lesson_id(l.get("lesson", "")) not in known]
    return share_lessons(payload, cfg, ripe, origin="promoted")
