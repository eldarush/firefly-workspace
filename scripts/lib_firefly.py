"""Firefly Workspace shared hook library.

Python 3.8+ stdlib only. Linux-first (Coder dev containers), Windows-tolerant.
Every hook must FAIL OPEN: an exception here must never break the user's session.

Layout managed under <project>/.firefly/ :
    config.json        user/env configuration (see assets/config.schema.json)
    events.jsonl       compact event capture (rotated)
    candidates.jsonl   distilled improvement candidates (auto-retro + /ff:retro input)
    proposals.jsonl    pending playbook delta-ops (consumed by curator)
    playbook.json      curated lessons - SOURCE OF TRUTH
    PLAYBOOK.md        human-readable render of playbook.json
    audit.log          append-only audit trail for guard denials + playbook ops
    state/<sid>.json   per-session counters (edits-since-verify, streaks, ...)
    handoff.md         context-reset handoff document
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

FIREFLY_DIR_NAME = ".firefly"
EVENTS_MAX_BYTES = 2 * 1024 * 1024  # rotate events.jsonl beyond this
STATE_TTL_SECONDS = 7 * 24 * 3600   # GC session state older than 7 days

# ---------------------------------------------------------------------------
# basic IO
# ---------------------------------------------------------------------------


def read_hook_input():
    """Parse the hook JSON payload from stdin. Returns {} on any failure."""
    try:
        raw = sys.stdin.read()
        if not raw:
            return {}
        return json.loads(raw)
    except Exception:
        return {}


def emit(obj):
    """Write a JSON response for Claude Code to stdout."""
    try:
        sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    except Exception:
        pass


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def project_dir(payload=None):
    """Resolve the project root: $CLAUDE_PROJECT_DIR > payload.cwd > cwd."""
    p = os.environ.get("CLAUDE_PROJECT_DIR")
    if p and os.path.isdir(p):
        return p
    if payload:
        c = payload.get("cwd")
        if c and os.path.isdir(c):
            return c
    return os.getcwd()


def firefly_dir(payload=None, create=True):
    """Path to <project>/.firefly. Created lazily with a self-ignoring .gitignore
    so the directory never pollutes `git status` even in repos without /ff:init."""
    root = os.path.join(project_dir(payload), FIREFLY_DIR_NAME)
    if create:
        try:
            os.makedirs(os.path.join(root, "state"), exist_ok=True)
            gi = os.path.join(root, ".gitignore")
            if not os.path.exists(gi):
                with open(gi, "w", encoding="utf-8") as f:
                    f.write("# Firefly local state - never committed by default.\n*\n")
        except Exception:
            pass
    return root


def _path(payload, *parts):
    return os.path.join(firefly_dir(payload), *parts)


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json_atomic(path, obj):
    try:
        tmp = path + ".tmp.%d" % os.getpid()
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=1)
        os.replace(tmp, path)
        return True
    except Exception:
        return False


def append_jsonl(path, obj):
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        return True
    except Exception:
        return False


def read_jsonl(path, limit=None):
    out = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    continue
    except Exception:
        return out
    if limit is not None and len(out) > limit:
        return out[-limit:]
    return out


def audit(payload, actor, action, detail):
    """Append-only audit trail (guard decisions, playbook mutations)."""
    try:
        line = "%s | %s | %s | %s\n" % (now_iso(), actor, action, detail)
        with open(_path(payload, "audit.log"), "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass


def est_tokens(text):
    return int(len(text) / 3.5) + 1


def digest(text, n=12):
    try:
        return hashlib.sha1(text.encode("utf-8", "replace")).hexdigest()[:n]
    except Exception:
        return "0" * n


def normalize_command(cmd):
    """Normalize a shell command for repetition detection: collapse paths,
    numbers, quoted strings so `kubectl logs pod-abc123` ~= `kubectl logs pod-x9`."""
    c = cmd.strip()
    c = re.sub(r"\"[^\"]*\"|'[^']*'", "S", c)
    c = re.sub(r"(?<=[\s=/])[\w.\-]*\d[\w.\-]*", "N", c)
    c = re.sub(r"\s+", " ", c)
    return c[:160]


# ---------------------------------------------------------------------------
# configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
    "version": 1,
    "personas": ["dev"],
    "behavior": {
        "stop_gate": True,            # block premature "done" after unverified edits
        "prompt_frame": True,         # inject task-frame on new nontrivial tasks
        "lessons_injection": True,    # inject top-K lessons at SessionStart
        "auto_allow_read": False,     # True = guard auto-approves read-only cmds
        "destroy": "deny",            # deny | ask
        "mutate_in_protected": "deny",  # deny | ask
        "max_stop_blocks_per_session": 2,
    },
    "protected": {
        "contexts": ["*prod*"],
        "namespaces": ["*prod*"],
    },
    "verify": {
        # Project verifier commands, e.g. ["make test", "npm test"]; first is default.
        "commands": [],
        # Edits to files matching these suffixes arm the stop-gate.
        "code_suffixes": [
            ".py", ".go", ".js", ".ts", ".tsx", ".jsx", ".java", ".cs", ".rb",
            ".rs", ".c", ".cpp", ".h", ".sh", ".yaml", ".yml", ".tf", ".sql",
        ],
    },
    "lessons": {
        "max_inject": 6,
        "max_inject_tokens": 1200,
        "max_active": 100,
        "max_per_scope": 20,
        "decay_half_life_weeks": 4,
        "trial_slots": 1,             # quarantined lessons injected as (trial)
    },
    "learning": {
        "auto_reflect": True,             # one-time auto-retro at Stop (LLM writes delta-ops)
        "auto_reflect_min_candidates": 2,  # fresh signals needed to trigger it
        "auto_reflect_min_turns": 3,       # don't reflect on trivial sessions
        "auto_lessons": True,              # deterministic proposals from cross-session recurrence
        "auto_feedback": True,             # implicit +helpful for lessons in clean verified sessions
        "min_recurrence": 2,               # sessions a signal must recur in before auto-lesson
    },
    "environment": {
        "spec_path": "",              # explicit spec path; else FIREFLY-ENV.md / .firefly/environment.md
        "inject": True,               # inject pinned facts + section index at SessionStart
        "max_inject_tokens": 500,     # budget for the pinned FF:ALWAYS block
    },
    "docs": {
        "kiwix_url": "",              # e.g. http://wikiall.internal:8090
        "extra_sources": [],
    },
    "deny_extra": [],
    "allow_extra": [],
}


def _deep_merge(base, override):
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(payload=None):
    cfg = load_json(_path(payload, "config.json"), {})
    return _deep_merge(DEFAULT_CONFIG, cfg)


# ---------------------------------------------------------------------------
# per-session state
# ---------------------------------------------------------------------------


def _state_path(payload, sid):
    sid = re.sub(r"[^\w\-]", "_", str(sid or "unknown"))[:64]
    return _path(payload, "state", sid + ".json")


def load_state(payload, sid):
    st = load_json(_state_path(payload, sid), {})
    st.setdefault("session_id", sid)
    st.setdefault("started", now_iso())
    st.setdefault("turns", 0)
    st.setdefault("frames_injected", 0)
    st.setdefault("last_frame_turn", -99)
    st.setdefault("edits_since_verify", 0)
    st.setdefault("edited_files", [])
    st.setdefault("verify_seen", False)
    st.setdefault("last_verify", None)
    st.setdefault("stop_blocks", 0)
    st.setdefault("error_streaks", {})   # digest -> count
    st.setdefault("cmd_counts", {})      # normalized cmd -> count
    st.setdefault("corrections", 0)
    st.setdefault("injected_lessons", [])  # lesson ids injected at SessionStart
    st.setdefault("reflected", False)      # auto-retro already ran this session
    return st


def save_state(payload, st):
    save_json_atomic(_state_path(payload, st.get("session_id")), st)


def gc_state(payload):
    try:
        d = _path(payload, "state")
        cutoff = time.time() - STATE_TTL_SECONDS
        for name in os.listdir(d):
            p = os.path.join(d, name)
            if os.path.isfile(p) and os.path.getmtime(p) < cutoff:
                os.remove(p)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# event capture
# ---------------------------------------------------------------------------


def rotate_events(payload):
    try:
        p = _path(payload, "events.jsonl")
        if os.path.exists(p) and os.path.getsize(p) > EVENTS_MAX_BYTES:
            os.replace(p, p + ".1")
    except Exception:
        pass


def log_event(payload, ev, **fields):
    rec = {"ts": now_iso(), "sid": payload.get("session_id", ""), "ev": ev}
    rec.update({k: v for k, v in fields.items() if v not in (None, "", [], {})})
    append_jsonl(_path(payload, "events.jsonl"), rec)


def tool_response_error(tool_response):
    """Extract an error string from a tool_response of unknown shape.
    Returns '' when the call looks successful."""
    try:
        if tool_response is None:
            return ""
        if isinstance(tool_response, str):
            body = tool_response
            low = body.lower()
            markers = (
                "command failed", "non-zero exit", "exit code", "traceback",
                "error:", "fatal:", "panic:", "exception", "failed with",
                "no such file", "permission denied", "syntax error",
                "string to replace not found", "compilation failed",
            )
            for m in markers:
                if m in low:
                    return body[:400]
            return ""
        if isinstance(tool_response, dict):
            if tool_response.get("is_error") or tool_response.get("isError"):
                return str(tool_response.get("error") or tool_response.get("output") or "error")[:400]
            err = tool_response.get("error") or tool_response.get("stderr")
            if err:
                return str(err)[:400]
            # exit code style responses
            code = tool_response.get("exit_code", tool_response.get("exitCode"))
            if isinstance(code, int) and code != 0:
                return ("exit %d: " % code + str(tool_response.get("output", "")))[:400]
            out = tool_response.get("output")
            if isinstance(out, str):
                return tool_response_error(out)
            return ""
        if isinstance(tool_response, list):
            for item in tool_response:
                e = tool_response_error(item)
                if e:
                    return e
            return ""
        return ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# verifier + correction detection
# ---------------------------------------------------------------------------

VERIFY_RE = re.compile(
    r"\b(pytest|go test|cargo (test|check|build)|npm (test|run (test|lint|build|typecheck))"
    r"|yarn (test|lint|build)|pnpm (test|lint|build)|make (test|lint|build|check)"
    r"|dotnet (test|build)|mvn (test|verify|package)|gradle (test|build|check)"
    r"|tox\b|ruff\b|flake8|mypy|eslint|tsc\b|golangci-lint|shellcheck"
    r"|helm (lint|template)|kubeval|kubeconform|terraform (validate|plan)"
    r"|(python3?|py) -m (pytest|unittest|compileall)|gitlab-ci-local)\b"
)

CORRECTION_RE = re.compile(
    r"^(no[,. ]|not (what|that|like)|that'?s (wrong|not)|wrong\b|undo\b|revert\b"
    r"|stop\b|don'?t\b|incorrect\b|actually[, ]|again\b|still (broken|failing|wrong)"
    r"|you (didn'?t|ignored|missed|broke))",
    re.IGNORECASE,
)


def is_verify_command(cmd, cfg=None):
    if not cmd:
        return False
    for c in ((cfg or {}).get("verify", {}) or {}).get("commands", []):
        if c and c in cmd:
            return True
    return bool(VERIFY_RE.search(cmd))


def is_code_file(path, cfg=None):
    suffixes = ((cfg or DEFAULT_CONFIG).get("verify", {}) or {}).get(
        "code_suffixes", DEFAULT_CONFIG["verify"]["code_suffixes"])
    p = (path or "").lower()
    return any(p.endswith(s) for s in suffixes)


def looks_like_correction(prompt):
    return bool(CORRECTION_RE.search((prompt or "").strip()))


# ---------------------------------------------------------------------------
# environment spec (the org's source-of-truth file)
# ---------------------------------------------------------------------------

ENV_SPEC_NAMES = ("FIREFLY-ENV.md", os.path.join(".firefly", "environment.md"))
_ENV_ALWAYS_RE = re.compile(
    r"<!--\s*FF:ALWAYS\s*-->(.*?)<!--\s*/FF:ALWAYS\s*-->", re.S | re.I)


def env_spec_path(payload=None, cfg=None):
    """Resolve the environment spec - the single source-of-truth markdown file
    describing the org's infra (GitLab URLs, clusters, registries, conventions).
    Chain: $FIREFLY_ENV_SPEC > config environment.spec_path > FIREFLY-ENV.md
    > .firefly/environment.md. Returns None when absent (fully optional)."""
    root = project_dir(payload)
    cands = []
    e = os.environ.get("FIREFLY_ENV_SPEC", "").strip()
    if e:
        cands.append(e if os.path.isabs(e) else os.path.join(root, e))
    c = (((cfg or {}).get("environment", {}) or {}).get("spec_path", "") or "").strip()
    if c:
        cands.append(c if os.path.isabs(c) else os.path.join(root, c))
    for name in ENV_SPEC_NAMES:
        cands.append(os.path.join(root, name))
    for p in cands:
        try:
            if p and os.path.isfile(p):
                return p
        except Exception:
            continue
    return None


def env_spec_summary(payload=None, cfg=None):
    """Budgeted SessionStart injection for the env spec: the pinned FF:ALWAYS
    facts verbatim plus an index of '## ' sections, so the model knows exact
    endpoints without guessing and reads the file for details. '' when no
    spec exists or injection is disabled."""
    env = (cfg or {}).get("environment", {}) or {}
    if not env.get("inject", True):
        return ""
    path = env_spec_path(payload, cfg)
    if not path:
        return ""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read(200000)
    except Exception:
        return ""
    try:
        rel = os.path.relpath(path, project_dir(payload))
        if rel.startswith(".."):
            rel = path
    except Exception:
        rel = path
    budget = int(env.get("max_inject_tokens", 500) or 500)
    pinned = "\n".join(m.strip() for m in _ENV_ALWAYS_RE.findall(text) if m.strip())
    while pinned and est_tokens(pinned) > budget:
        pinned = pinned[: max(1, int(len(pinned) * 0.8))].rstrip()
    heads = [ln.strip()[3:].strip() for ln in text.splitlines()
             if ln.startswith("## ")][:16]
    out = ["## Environment facts (source of truth: %s)" % rel]
    if pinned:
        out.append(pinned)
    if heads:
        out.append("The spec has more sections - READ the file before touching "
                   "infra, never invent URLs/endpoints/cluster names: "
                   + " | ".join(heads))
    if not pinned and not heads:
        out.append("Spec file exists but has no FF:ALWAYS block or ## sections; "
                   "read it directly. Never invent URLs/endpoints.")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# command safety classification (shared by guard + distiller)
# ---------------------------------------------------------------------------

DESTROY_RES = [
    r"\b(curl|wget)\b[^|;]*\|\s*(sudo\s+)?(ba|z|fi|da)?sh\b",
    r"\b(curl|wget)\b[^|;]*\|\s*(sudo\s+)?python3?\b",
    r"\bkubectl\s+(?:[\w/=:.\-]+\s+)*delete\b",
    r"\bkubectl\b.*--all\b",
    r"\bkubectl\s+drain\b",
    r"\bhelm\s+(uninstall|delete)\b",
    r"\bterraform\s+destroy\b",
    r"\bterraform\s+apply\b.*-auto-approve\b",
    r"\bargocd\s+app\s+delete\b",
    r"\bflux\s+(delete|uninstall)\b",
    r"\bkargo\s+delete\b",
    r"\brm\s+(-[a-z]*[rf][a-z]*\s+)+/((etc|usr|var|home|root|bin|opt)\b|\s*$)",
    r"\brm\s+-[a-z]*r[a-z]*f|\brm\s+-[a-z]*f[a-z]*r",
    r"\bgit\s+push\b.*(--force\b|-f\b)",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+clean\s+-[a-z]*f",
    r"\bdd\s+if=",
    r"\bmkfs\b",
    r"\bdrop\s+(table|database|schema)\b",
    r"\btruncate\s+table\b",
    r"\bdocker\s+(system\s+prune|rm\s+-f|rmi\b)",
    r"\bgitlab-rails\s+console\b",
]

MUTATE_RES = [
    r"\bkubectl\s+(apply|create|patch|edit|scale|label|annotate|cordon|uncordon|taint|set|rollout)\b",
    r"\bkubectl\s+exec\b",
    r"\bhelm\s+(install|upgrade|rollback)\b",
    r"\bargocd\s+app\s+(sync|set|rollback|patch)\b",
    r"\bflux\s+(reconcile|suspend|resume)\b",
    r"\bkargo\s+(promote|approve)\b",
    r"\bterraform\s+(apply|import|taint)\b",
    r"\bgit\s+push\b",
    r"\bdocker\s+(push|run)\b",
    r"\bsystemctl\s+(start|stop|restart|disable|enable)\b",
]

READ_RES = [
    r"^\s*(cat|ls|ll|head|tail|less|wc|find|rg|grep|tree|pwd|echo|env|which|file|stat|du|df)\b",
    r"\bkubectl\s+(get|describe|logs|top|explain|api-resources|version|config\s+(view|get-contexts|current-context))\b",
    r"\bhelm\s+(list|ls|status|get|show|search|template|lint|diff)\b",
    r"\bargocd\s+app\s+(get|list|diff|history|manifests)\b",
    r"\bflux\s+(get|logs|tree)\b",
    r"\bkargo\s+(get|list)\b",
    r"\bterraform\s+(plan|show|validate|output|state\s+(list|show))\b",
    r"\bgit\s+(status|log|diff|show|branch|remote|blame|describe)\b",
    r"\bdocker\s+(ps|images|logs|inspect)\b",
    r"\bcurl\s+(-[\w]+\s+)*https?://",
]

_PROTECTED_FLAG_RE = re.compile(
    r"(?:--context|--kube-context|--cluster|--namespace|-n)(?:[=\s]+)([\w.\-:*]+)")


def _glob_match(value, patterns):
    import fnmatch
    v = (value or "").lower()
    return any(fnmatch.fnmatch(v, (p or "").lower()) for p in patterns or [])


def split_shell(cmd):
    """Split a shell line into sub-commands on ; && || | and newlines.
    Conservative: quotes are not tracked; classification treats every fragment."""
    parts = re.split(r"(?:&&|\|\||[;|\n])", cmd or "")
    return [p.strip() for p in parts if p.strip()]


def classify_command(cmd, cfg=None):
    """Return (klass, reason) where klass in read|mutate|destroy|other.
    The MOST dangerous classification across sub-commands wins."""
    cfg = cfg or DEFAULT_CONFIG
    klass, reason = "other", ""
    rank = {"other": 0, "read": 0, "mutate": 1, "destroy": 2}
    for frag in split_shell(cmd):
        frag_klass, frag_reason = "other", ""
        for rx in cfg.get("deny_extra", []) or []:
            try:
                if re.search(rx, frag):
                    frag_klass, frag_reason = "destroy", "matched deny_extra: %s" % rx
                    break
            except re.error:
                continue
        if frag_klass == "other":
            for rx in DESTROY_RES:
                if re.search(rx, frag):
                    frag_klass, frag_reason = "destroy", "matched: %s" % rx
                    break
        if frag_klass == "other":
            for rx in MUTATE_RES:
                if re.search(rx, frag):
                    frag_klass, frag_reason = "mutate", "matched: %s" % rx
                    break
        if frag_klass == "other":
            allow_hit = False
            for rx in cfg.get("allow_extra", []) or []:
                try:
                    if re.search(rx, frag):
                        allow_hit = True
                        break
                except re.error:
                    continue
            if allow_hit or any(re.search(rx, frag) for rx in READ_RES):
                frag_klass = "read"
        if rank[frag_klass] > rank[klass] or (klass == "other" and frag_klass == "read"):
            klass, reason = frag_klass, frag_reason
    return klass, reason


def targets_protected(cmd, cfg=None):
    """True when the command explicitly targets a protected context/namespace."""
    cfg = cfg or DEFAULT_CONFIG
    prot = cfg.get("protected", {}) or {}
    for m in _PROTECTED_FLAG_RE.finditer(cmd or ""):
        val = m.group(1)
        if _glob_match(val, prot.get("contexts", [])) or _glob_match(val, prot.get("namespaces", [])):
            return True
    return False
