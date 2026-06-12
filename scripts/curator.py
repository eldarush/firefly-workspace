"""Firefly playbook curator: applies delta-ops to playbook.json.

ACE-style memory: itemized lessons with helpful/harmful counters, incremental
delta updates (never full rewrites), dedup, decay, quarantine, caps, audit.

Deterministic by design - the LLM only PROPOSES ops (written as JSON lines to
.firefly/proposals.jsonl by the reflector agent or /ff:lessons); this module
applies them mechanically so a weak model can never corrupt accumulated memory.

Op shapes (one JSON object per proposals.jsonl line):
  {"op":"add","scope":"global|sre|qa|dev|research|repo","tags":["helm"],
   "lesson":"imperative rule <=400 chars","evidence":["sid:why"],"origin":"auto|human"}
  {"op":"feedback","id":"lsn-xxx","helpful":1}        # or "harmful":1
  {"op":"edit","id":"lsn-xxx","lesson":"new text"}
  {"op":"approve","id":"lsn-xxx"}                      # quarantined -> active (human/lawmaker)
  {"op":"quarantine","id":"lsn-xxx","reason":"..."}
  {"op":"deprecate","id":"lsn-xxx","reason":"..."}

Invariants enforced here:
  - new auto lessons start status=quarantined; only `approve` (human) or
    >=2 helpful with 0 harmful auto-promotes to active
  - lesson text capped at 400 chars; evidence list capped at 8
  - active caps: lessons.max_active total / lessons.max_per_scope per scope
  - harmful >= helpful+2 -> auto-quarantine; deprecated lessons never resurrect
"""

import os
import re
import sys
import math
import time
from datetime import datetime, timezone

try:
    import lib_firefly as ff
except ImportError:  # direct invocation from another cwd
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lib_firefly as ff

LESSON_MAX_CHARS = 400
EVIDENCE_MAX = 8
STOPWORDS = set("the a an to of in on for with and or is are be should must when use".split())


def _playbook_path(payload):
    return os.path.join(ff.firefly_dir(payload), "playbook.json")


def _proposals_path(payload):
    return os.path.join(ff.firefly_dir(payload), "proposals.jsonl")


def load_playbook(payload):
    pb = ff.load_json(_playbook_path(payload), {})
    pb.setdefault("version", 1)
    pb.setdefault("updated", ff.now_iso())
    pb.setdefault("lessons", [])
    return pb


def save_playbook(payload, pb):
    pb["updated"] = ff.now_iso()
    ok = ff.save_json_atomic(_playbook_path(payload), pb)
    if ok:
        render_markdown(payload, pb)
    return ok


def _stem(text):
    words = [w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if w not in STOPWORDS]
    return " ".join(sorted(set(words))[:24])


def _jaccard(a, b):
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / float(len(sa | sb))


def _find_duplicate(pb, lesson_text, tags):
    """Existing non-deprecated lesson with very similar text => duplicate."""
    stem = _stem(lesson_text)
    tagset = set(t.lower() for t in tags or [])
    for l in pb["lessons"]:
        if l.get("status") == "deprecated":
            continue
        sim = _jaccard(stem, _stem(l.get("lesson", "")))
        tag_overlap = 1.0
        ltags = set(t.lower() for t in l.get("tags", []))
        if tagset and ltags:
            tag_overlap = len(tagset & ltags) / float(len(tagset | ltags))
        if sim >= 0.75 or (sim >= 0.55 and tag_overlap >= 0.5):
            return l
    return None


def _get(pb, lid):
    for l in pb["lessons"]:
        if l.get("id") == lid:
            return l
    return None


def score(lesson, now=None, half_life_weeks=4.0, persona_tags=None):
    """Ranking score: net helpfulness decayed by recency + tag relevance boost."""
    try:
        last = lesson.get("last_seen") or lesson.get("created") or ff.now_iso()
        dt = datetime.strptime(last[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        weeks = max(0.0, ((now or time.time()) - dt.timestamp()) / (7 * 24 * 3600.0))
    except Exception:
        weeks = 0.0
    decay = math.pow(0.5, weeks / max(0.5, half_life_weeks))
    net = lesson.get("helpful", 0) - 2 * lesson.get("harmful", 0)
    base = (1.0 + max(-3, net)) * decay
    boost = 0.0
    if persona_tags:
        ltags = set(t.lower() for t in lesson.get("tags", []) + [lesson.get("scope", "")])
        boost = 2.0 * len(ltags & set(t.lower() for t in persona_tags))
    return base + boost


def apply_op(payload, pb, op, cfg, actor="auto"):
    """Apply one delta-op. Returns short audit detail or None when rejected."""
    kind = (op.get("op") or "").lower()
    if kind == "add":
        text = (op.get("lesson") or "").strip()[:LESSON_MAX_CHARS]
        if len(text) < 12:
            return None
        tags = [str(t)[:24].lower() for t in (op.get("tags") or [])][:6]
        scope = (op.get("scope") or "global").lower()
        dup = _find_duplicate(pb, text, tags)
        if dup:
            dup["helpful"] = dup.get("helpful", 0) + 1
            dup["last_seen"] = ff.now_iso()
            ev = (op.get("evidence") or [])[:2]
            dup["evidence"] = (dup.get("evidence", []) + ev)[-EVIDENCE_MAX:]
            _maybe_promote(dup)
            return "dedup->feedback %s (+1 helpful)" % dup["id"]
        lid = "lsn-" + ff.digest(text + scope, 10)
        if _get(pb, lid):
            return None
        origin = op.get("origin") or actor
        lesson = {
            "id": lid,
            "scope": scope,
            "tags": tags,
            "lesson": text,
            "helpful": 1 if origin == "human" else 0,
            "harmful": 0,
            "status": "active" if origin == "human" else "quarantined",
            "origin": origin,
            "created": ff.now_iso(),
            "last_seen": ff.now_iso(),
            "evidence": (op.get("evidence") or [])[:EVIDENCE_MAX],
        }
        pb["lessons"].append(lesson)
        return "add %s [%s] %s" % (lid, lesson["status"], text[:60])

    lid = op.get("id")
    lesson = _get(pb, lid) if lid else None
    if not lesson:
        return None

    if kind == "feedback":
        lesson["helpful"] = lesson.get("helpful", 0) + int(op.get("helpful") or 0)
        lesson["harmful"] = lesson.get("harmful", 0) + int(op.get("harmful") or 0)
        lesson["last_seen"] = ff.now_iso()
        ev = op.get("evidence")
        if ev:
            lesson["evidence"] = (lesson.get("evidence", []) + [str(ev)[:120]])[-EVIDENCE_MAX:]
        if lesson.get("harmful", 0) >= lesson.get("helpful", 0) + 2 and lesson["status"] == "active":
            lesson["status"] = "quarantined"
            return "feedback %s -> auto-quarantined (harmful)" % lid
        _maybe_promote(lesson)
        return "feedback %s h=%d x=%d" % (lid, lesson["helpful"], lesson["harmful"])

    if kind == "edit":
        text = (op.get("lesson") or "").strip()[:LESSON_MAX_CHARS]
        if len(text) < 12 or lesson.get("status") == "deprecated":
            return None
        lesson["lesson"] = text
        lesson["last_seen"] = ff.now_iso()
        return "edit %s" % lid

    if kind == "approve":
        if lesson.get("status") == "deprecated":
            return None
        lesson["status"] = "active"
        lesson["origin"] = "human"
        lesson["last_seen"] = ff.now_iso()
        return "approve %s" % lid

    if kind == "quarantine":
        if lesson.get("status") == "deprecated":
            return None
        lesson["status"] = "quarantined"
        return "quarantine %s (%s)" % (lid, op.get("reason", ""))

    if kind == "deprecate":
        lesson["status"] = "deprecated"
        return "deprecate %s (%s)" % (lid, op.get("reason", ""))

    return None


def _maybe_promote(lesson):
    if (lesson.get("status") == "quarantined"
            and lesson.get("helpful", 0) >= 2
            and lesson.get("harmful", 0) == 0):
        lesson["status"] = "active"


def enforce_caps(pb, cfg):
    """Deprecate lowest-score overflow beyond max_active / max_per_scope."""
    lcfg = cfg.get("lessons", {})
    half = lcfg.get("decay_half_life_weeks", 4)
    active = [l for l in pb["lessons"] if l.get("status") == "active"]
    by_scope = {}
    for l in active:
        by_scope.setdefault(l.get("scope", "global"), []).append(l)
    for scope, ls in by_scope.items():
        ls.sort(key=lambda l: score(l, half_life_weeks=half), reverse=True)
        for l in ls[lcfg.get("max_per_scope", 20):]:
            l["status"] = "deprecated"
    active = [l for l in pb["lessons"] if l.get("status") == "active"]
    active.sort(key=lambda l: score(l, half_life_weeks=half), reverse=True)
    for l in active[lcfg.get("max_active", 100):]:
        l["status"] = "deprecated"


def consume_proposals(payload, cfg=None, actor="auto"):
    """Atomically consume proposals.jsonl and apply every op. Returns count."""
    cfg = cfg or ff.load_config(payload)
    src = _proposals_path(payload)
    if not os.path.exists(src):
        return 0
    work = src + ".applying.%d" % os.getpid()
    try:
        os.replace(src, work)
    except Exception:
        return 0
    ops = ff.read_jsonl(work)
    if not ops:
        try:
            os.remove(work)
        except Exception:
            pass
        return 0
    pb = load_playbook(payload)
    applied = 0
    for op in ops:
        try:
            detail = apply_op(payload, pb, op, cfg, actor=op.get("actor", actor))
        except Exception:
            detail = None
        if detail:
            applied += 1
            ff.audit(payload, op.get("actor", actor), "playbook", detail)
    enforce_caps(pb, cfg)
    save_playbook(payload, pb)
    try:
        os.remove(work)
    except Exception:
        pass
    return applied


def select_for_injection(payload, cfg=None):
    """Top-K active lessons (+ trial quarantined slots) within token budget."""
    cfg = cfg or ff.load_config(payload)
    lcfg = cfg.get("lessons", {})
    pb = load_playbook(payload)
    persona_tags = list(cfg.get("personas", [])) + ["global"]
    half = lcfg.get("decay_half_life_weeks", 4)
    active = [l for l in pb["lessons"] if l.get("status") == "active"]
    active.sort(key=lambda l: score(l, half_life_weeks=half, persona_tags=persona_tags),
                reverse=True)
    quarantined = [l for l in pb["lessons"] if l.get("status") == "quarantined"]
    quarantined.sort(key=lambda l: l.get("last_seen", ""), reverse=True)

    chosen, budget = [], lcfg.get("max_inject_tokens", 1200)
    for l in active[: lcfg.get("max_inject", 6)]:
        t = ff.est_tokens(l["lesson"])
        if budget - t < 0:
            break
        budget -= t
        chosen.append((l, False))
    for l in quarantined[: lcfg.get("trial_slots", 1)]:
        t = ff.est_tokens(l["lesson"])
        if budget - t < 0:
            break
        budget -= t
        chosen.append((l, True))
    return chosen


def render_markdown(payload, pb=None):
    """Human-readable PLAYBOOK.md (review surface for /ff:lessons)."""
    pb = pb or load_playbook(payload)
    lines = [
        "# Firefly Playbook",
        "",
        "Source of truth: `playbook.json` (edit via `/ff:lessons`, not by hand).",
        "Updated: %s" % pb.get("updated", ""),
        "",
    ]
    order = {"active": 0, "quarantined": 1, "deprecated": 2}
    for status in ("active", "quarantined", "deprecated"):
        ls = [l for l in pb["lessons"] if l.get("status") == status]
        if not ls:
            continue
        lines.append("## %s (%d)" % (status.capitalize(), len(ls)))
        lines.append("")
        ls.sort(key=lambda l: (order.get(l.get("status"), 9), -(l.get("helpful", 0))))
        for l in ls:
            lines.append("- `%s` **[%s]** %s  _(+%d/-%d, %s)_" % (
                l.get("id"), ",".join(l.get("tags", [])) or l.get("scope", "global"),
                l.get("lesson", ""), l.get("helpful", 0), l.get("harmful", 0),
                l.get("origin", "auto")))
        lines.append("")
    try:
        path = os.path.join(ff.firefly_dir(payload), "PLAYBOOK.md")
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        os.replace(tmp, path)
    except Exception:
        pass


if __name__ == "__main__":
    payload = {"cwd": os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())}
    n = consume_proposals(payload)
    print("applied %d playbook op(s)" % n)
