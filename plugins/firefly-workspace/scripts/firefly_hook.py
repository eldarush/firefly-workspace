#!/usr/bin/env python3
"""Firefly Workspace Claude Code hook engine.

This module is intentionally dependency-free so the plugin can run in strict
airgapped environments. It records local evidence, injects approved context, and
creates proposals for later human review. It never rewrites plugin behavior by
itself.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import pathlib
import re
import sys
from typing import Any


MAX_CONTEXT_CHARS = 5000
MAX_LEDGER_FIELD_CHARS = 4000
DANGEROUS_BASH_PATTERNS = (
    (
        re.compile(r"\b(curl|wget)\b.+\|\s*(sh|bash|zsh|python|python3)\b", re.IGNORECASE),
        "Blocked network pipe-to-shell pattern. Download, inspect, pin, and run reviewed artifacts instead.",
    ),
    (
        re.compile(r"\brm\s+-[^\n]*r[^\n]*f\s+(/|~|\$HOME)\b", re.IGNORECASE),
        "Blocked destructive recursive delete outside an explicit workspace path.",
    ),
    (
        re.compile(r"\bkubectl\s+delete\s+(namespace|ns)\b", re.IGNORECASE),
        "Blocked namespace deletion. Ask the architect for an explicit environment and rollback plan.",
    ),
    (
        re.compile(r"\bhelm\s+uninstall\b.+\s+--no-hooks\b", re.IGNORECASE),
        "Blocked Helm uninstall without hooks. Use a reviewed rollback workflow.",
    ),
)


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")


def data_root() -> pathlib.Path:
    configured = os.environ.get("CLAUDE_PLUGIN_DATA")
    if configured:
        return pathlib.Path(configured).expanduser()
    return pathlib.Path.home() / ".claude" / "plugins" / "data" / "firefly-workspace"


def ensure_dirs(root: pathlib.Path) -> None:
    for name in ("ledger", "memory", "proposals", "snapshots"):
        (root / name).mkdir(parents=True, exist_ok=True)
    ledger = root / "ledger" / "events.jsonl"
    if not ledger.exists():
        ledger.touch()


def truncate(value: Any, limit: int = MAX_LEDGER_FIELD_CHARS) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "...[truncated]"
    if isinstance(value, dict):
        return {str(k): truncate(v, limit) for k, v in value.items()}
    if isinstance(value, list):
        return [truncate(v, limit) for v in value[:50]]
    return value


def event_digest(event: dict[str, Any]) -> str:
    encoded = json.dumps(event, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def append_jsonl(path: pathlib.Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n")


def record_event(root: pathlib.Path, event: dict[str, Any]) -> None:
    selected = {
        "timestamp": now_iso(),
        "digest": event_digest(event),
        "event": event.get("hook_event_name"),
        "session_id": event.get("session_id"),
        "cwd": event.get("cwd"),
        "permission_mode": event.get("permission_mode"),
        "prompt": event.get("prompt"),
        "tool_name": event.get("tool_name"),
        "tool_input": event.get("tool_input"),
        "error": event.get("error"),
        "last_assistant_message": event.get("last_assistant_message"),
    }
    append_jsonl(root / "ledger" / "events.jsonl", truncate(selected))


def load_approved_memory(root: pathlib.Path, max_items: int = 8) -> list[dict[str, Any]]:
    memory_path = root / "memory" / "approved_memory.jsonl"
    if not memory_path.exists():
        return []
    items: list[dict[str, Any]] = []
    for line in memory_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict) and item.get("summary"):
            items.append(item)
    return items[-max_items:]


def load_project_context(cwd: str | None) -> str:
    if not cwd:
        return ""
    context_path = pathlib.Path(cwd) / ".firefly" / "context.md"
    if not context_path.exists():
        return ""
    text = context_path.read_text(encoding="utf-8").strip()
    return text[:MAX_CONTEXT_CHARS]


def render_context(root: pathlib.Path, cwd: str | None, include_project: bool = True) -> str:
    memory = load_approved_memory(root)
    project_context = load_project_context(cwd) if include_project else ""
    lines = [
        "Firefly Workspace operating context:",
        "- The human is the architect and final decision maker.",
        "- Use staged workflows: understand, localize, plan, implement, verify, review, reflect.",
        "- Prefer local evidence, repository files, tests, offline docs, and approved MCP tools over assumptions.",
        "- Record verification gaps explicitly: what passed, what failed, and what was not run.",
    ]
    if project_context:
        lines.extend(["", "Project Firefly context:", project_context])
    if memory:
        lines.append("")
        lines.append("Approved durable memory:")
        for item in memory:
            prefix = item.get("kind", "memory")
            confidence = item.get("confidence", "unspecified")
            lines.append(f"- [{prefix}; confidence={confidence}] {item.get('summary')}")
    return "\n".join(lines)[:MAX_CONTEXT_CHARS]


def deny_dangerous_bash(event: dict[str, Any]) -> dict[str, Any] | None:
    if event.get("tool_name") != "Bash":
        return None
    tool_input = event.get("tool_input") or {}
    command = str(tool_input.get("command", ""))
    for pattern, reason in DANGEROUS_BASH_PATTERNS:
        if pattern.search(command):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
    return None


def create_retrospective_proposal(root: pathlib.Path, event: dict[str, Any]) -> None:
    message = str(event.get("last_assistant_message") or "").strip()
    if not message:
        return
    lower = message.lower()
    verification_gap = ""
    if "not run" in lower or "wasn't run" in lower or "could not run" in lower:
        verification_gap = next(
            (line.strip() for line in message.splitlines() if "not run" in line.lower() or "could not run" in line.lower()),
            "Verification gap mentioned by assistant.",
        )
    proposal = {
        "type": "retrospective",
        "created_at": now_iso(),
        "session_id": event.get("session_id"),
        "source_digest": event_digest(event),
        "status": "needs-human-review",
        "signals": {
            "verification_gap": verification_gap,
            "summary_candidate": message[:1200],
        },
        "recommendations": [
            "If this reflects a repeated workflow, ask /firefly-workspace:mine-skill to draft a skill.",
            "If this contains a durable team preference, promote it to memory/approved_memory.jsonl after review.",
            "If this exposed a missing check, add it to the local eval or CI gate before changing default behavior.",
        ],
    }
    name = f"retrospective-{now_iso().replace(':', '').replace('+', 'Z')}-{proposal['source_digest']}.json"
    (root / "proposals" / name).write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")


def handle_event(event: dict[str, Any]) -> dict[str, Any]:
    root = data_root()
    ensure_dirs(root)
    record_event(root, event)

    name = event.get("hook_event_name")
    cwd = event.get("cwd")

    if name == "SessionStart":
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": render_context(root, cwd, include_project=True),
            }
        }

    if name == "UserPromptSubmit":
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": render_context(root, cwd, include_project=True),
            }
        }

    if name == "PreToolUse":
        denied = deny_dangerous_bash(event)
        if denied:
            return denied
        return {}

    if name == "PostToolUseFailure":
        tool_name = event.get("tool_name", "tool")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUseFailure",
                "additionalContext": (
                    f"Firefly observed a {tool_name} failure. Summarize the failure, "
                    "identify the smallest next diagnostic step, and avoid repeating the same command blindly."
                ),
            }
        }

    if name == "Stop":
        create_retrospective_proposal(root, event)
        return {}

    return {}


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as exc:
        print(f"Firefly hook received invalid JSON: {exc}", file=sys.stderr)
        return 0
    output = handle_event(event)
    if output:
        print(json.dumps(output, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
