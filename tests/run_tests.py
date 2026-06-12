#!/usr/bin/env python3
"""Firefly Workspace test harness - stdlib only.

Exercises every hook script as Claude Code would (JSON on stdin, JSON/exit-code
out), plus curator/distiller unit flows, in a throwaway project dir.

Run:  python3 tests/run_tests.py   (or `py tests\\run_tests.py` on Windows)
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
PY = sys.executable

PASS, FAIL = 0, []


def check(name, cond, detail=""):
    global PASS
    if cond:
        PASS += 1
        print("  ok  %s" % name)
    else:
        FAIL.append("%s %s" % (name, detail))
        print("  FAIL %s  %s" % (name, detail))


def run_hook(script, payload, project):
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = project
    env["CLAUDE_PLUGIN_ROOT"] = ROOT
    p = subprocess.run(
        [PY, os.path.join(SCRIPTS, script)],
        input=json.dumps(payload).encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=30)
    out = p.stdout.decode("utf-8", "replace").strip()
    parsed = None
    if out:
        try:
            parsed = json.loads(out)
        except Exception:
            parsed = {"_raw": out}
    return p.returncode, parsed, p.stderr.decode("utf-8", "replace")


def base(project, sid="sess-test-1", **kw):
    d = {"session_id": sid, "transcript_path": "/tmp/t.jsonl", "cwd": project}
    d.update(kw)
    return d


def read_state(project, sid="sess-test-1"):
    p = os.path.join(project, ".firefly", "state", sid + ".json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def frontmatter(path):
    """Parse simple single-line `key: value` YAML frontmatter. Returns dict or None."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end < 0:
        return None, text
    fm = {}
    for line in text[3:end].strip().splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, text[end + 4:]


def structure_lint():
    # manifests
    with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        plug = json.load(f)
    with open(os.path.join(ROOT, ".claude-plugin", "marketplace.json"), encoding="utf-8") as f:
        mkt = json.load(f)
    check("plugin.json name is ff", plug.get("name") == "ff")
    check("plugin.json has version", bool(plug.get("version")))
    check("marketplace plugin entry matches", any(
        p.get("name") == "ff" for p in mkt.get("plugins", [])))
    mv = [p.get("version") for p in mkt.get("plugins", []) if p.get("name") == "ff"]
    check("versions in sync", mv and mv[0] == plug.get("version"),
          "plugin=%s marketplace=%s" % (plug.get("version"), mv))

    # hooks.json wiring -> scripts exist
    with open(os.path.join(ROOT, "hooks", "hooks.json"), encoding="utf-8") as f:
        hooks = json.load(f)
    missing = []
    n_cmds = 0
    for matchers in hooks.get("hooks", {}).values():
        for m in matchers:
            for h in m.get("hooks", []):
                n_cmds += 1
                cmd = h.get("command", "")
                for part in cmd.split():
                    if part.endswith('.py"') or part.endswith(".py"):
                        rel = part.strip('"').replace("${CLAUDE_PLUGIN_ROOT}/", "")
                        if not os.path.exists(os.path.join(ROOT, rel)):
                            missing.append(rel)
    check("hooks.json references >=8 commands", n_cmds >= 8, str(n_cmds))
    check("all hook scripts exist", not missing, str(missing))

    # commands
    cmd_files = sorted(os.listdir(os.path.join(ROOT, "commands")))
    check("14 commands present", len(cmd_files) == 14, str(len(cmd_files)))
    bad = []
    for c in cmd_files:
        fm, _ = frontmatter(os.path.join(ROOT, "commands", c))
        if not fm or not fm.get("description"):
            bad.append(c + ":no-desc")
        elif fm.get("disable-model-invocation") != "true":
            bad.append(c + ":model-invocable")
    check("commands frontmatter ok", not bad, str(bad))

    # agents
    ag_files = sorted(f for f in os.listdir(os.path.join(ROOT, "agents"))
                      if f.endswith(".md"))
    check("7 agents present", len(ag_files) == 7, str(len(ag_files)))
    bad = []
    for a in ag_files:
        fm, _ = frontmatter(os.path.join(ROOT, "agents", a))
        stem = a[:-3]
        if not fm:
            bad.append(a + ":no-fm")
            continue
        if fm.get("name") != stem:
            bad.append(a + ":name!=" + str(fm.get("name")))
        if not fm.get("description"):
            bad.append(a + ":no-desc")
        if fm.get("model") != "inherit":
            bad.append(a + ":model=" + str(fm.get("model")))
    check("agents frontmatter ok", not bad, str(bad))

    # skills
    skill_dirs = sorted(d for d in os.listdir(os.path.join(ROOT, "skills"))
                        if os.path.isdir(os.path.join(ROOT, "skills", d)))
    check("25 skills present", len(skill_dirs) == 25, str(len(skill_dirs)))
    bad = []
    for d in skill_dirs:
        p = os.path.join(ROOT, "skills", d, "SKILL.md")
        if not os.path.exists(p):
            bad.append(d + ":missing-SKILL.md")
            continue
        fm, body = frontmatter(p)
        if not fm:
            bad.append(d + ":no-fm")
            continue
        if fm.get("name") != d:
            bad.append(d + ":name!=" + str(fm.get("name")))
        desc = fm.get("description", "")
        if not desc.startswith("Use when"):
            bad.append(d + ":desc-style")
        if len(desc) > 200:
            bad.append(d + ":desc-len=%d" % len(desc))
        with open(p, encoding="utf-8") as f:
            lines = f.read().splitlines()
        if len(lines) > 200:
            bad.append(d + ":lines=%d" % len(lines))
        try:
            "".join(lines).encode("ascii")
        except UnicodeEncodeError:
            bad.append(d + ":non-ascii")
    check("skills structure ok", not bad, str(bad))

    # evals corpus parses
    ev = os.path.join(ROOT, "evals", "prompt-injection-corpus.jsonl")
    rows = []
    with open(ev, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    check("eval corpus >=8 scenarios", len(rows) >= 8, str(len(rows)))
    check("eval rows well-formed", all(
        r.get("id") and r.get("expected") and r.get("must_not") for r in rows))

    # assets sanity
    for rel in ("assets/CLAUDE.snippet.md", "assets/config.schema.json",
                "assets/config.example.json", "README.md", "CHANGELOG.md",
                "LICENSE"):
        check("exists: " + rel, os.path.exists(os.path.join(ROOT, rel)))


def main():
    project = tempfile.mkdtemp(prefix="ff-test-")
    print("project: %s" % project)
    print("python : %s" % PY)

    # Disable Stop-hook auto-retro for the legacy gate tests; the dedicated
    # [auto-learning] section re-enables it explicitly.
    os.makedirs(os.path.join(project, ".firefly"), exist_ok=True)
    cfg_path = os.path.join(project, ".firefly", "config.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump({"learning": {"auto_reflect": False}}, f)

    try:
        # ---------------- session_start -------------------------------
        print("\n[session_start]")
        rc, out, err = run_hook("session_start.py", base(project, source="startup",
                                hook_event_name="SessionStart"), project)
        check("exit 0", rc == 0, "rc=%s err=%s" % (rc, err[:200]))
        check("emits additionalContext", bool(out)
              and "additionalContext" in (out.get("hookSpecificOutput") or {}),
              json.dumps(out)[:200] if out else "no output")
        ctx = (out.get("hookSpecificOutput") or {}).get("additionalContext", "")
        check("contract injected", "operating contract" in ctx)
        check("budget <= ~1600 tok", len(ctx) / 3.5 <= 1700, "len=%d" % len(ctx))
        check(".firefly created", os.path.isdir(os.path.join(project, ".firefly")))
        check(".firefly self-gitignored",
              os.path.exists(os.path.join(project, ".firefly", ".gitignore")))

        # ---------------- prompt_submit -------------------------------
        print("\n[prompt_submit]")
        rc, out, err = run_hook("prompt_submit.py", base(project,
                                hook_event_name="UserPromptSubmit",
                                prompt="Please implement a retry mechanism for the flink "
                                       "operator deployment script and add tests for it"),
                                project)
        check("exit 0", rc == 0, err[:200])
        ctx = ((out or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")
        check("frame injected on nontrivial task", "restate it in one sentence" in ctx,
              ctx[:120])
        st = read_state(project)
        check("turn counted", st["turns"] == 1)

        rc, out, _ = run_hook("prompt_submit.py", base(project,
                              hook_event_name="UserPromptSubmit", prompt="ok go ahead"),
                              project)
        check("no frame on trivial prompt", not out or "restate" not in json.dumps(out))

        rc, out, _ = run_hook("prompt_submit.py", base(project,
                              hook_event_name="UserPromptSubmit",
                              prompt="no, that's wrong - you broke the import"), project)
        ctx = ((out or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")
        check("correction nudge", "correcting you" in ctx, ctx[:120])
        check("correction counted", read_state(project)["corrections"] == 1)

        # ---------------- pre_tool_guard ------------------------------
        print("\n[pre_tool_guard]")
        cases = [
            ("kubectl get pods -A", None),
            ("kubectl delete namespace staging", "deny"),
            ("helm uninstall myapp -n apps", "deny"),
            ("rm -rf /etc/kubernetes", "deny"),
            ("git push --force origin main", "deny"),
            ("terraform destroy -auto-approve", "deny"),
            ("kubectl apply -f app.yaml -n dev-team", None),
            ("kubectl apply -f app.yaml --namespace prod-eu1", "deny"),
            ("helm upgrade web ./chart --kube-context prod-cluster", "deny"),
            ("ls -la && kubectl delete pod x", "deny"),
            ("echo 'kubectl delete' is a string", "deny"),  # conservative: still flagged
            ("git status", None),
        ]
        for cmd, expected in cases:
            rc, out, err = run_hook("pre_tool_guard.py", base(project,
                                    hook_event_name="PreToolUse", tool_name="Bash",
                                    tool_input={"command": cmd}), project)
            got = ((out or {}).get("hookSpecificOutput") or {}).get("permissionDecision")
            check("guard %-50s -> %s" % (cmd[:50], expected), got == expected,
                  "got=%s rc=%s" % (got, rc))
        # non-Bash tool passes through
        rc, out, _ = run_hook("pre_tool_guard.py", base(project,
                              hook_event_name="PreToolUse", tool_name="Write",
                              tool_input={"file_path": "x.py"}), project)
        check("non-Bash ignored", rc == 0 and not out)
        # malformed stdin fails open
        env = dict(os.environ); env["CLAUDE_PROJECT_DIR"] = project
        p = subprocess.run([PY, os.path.join(SCRIPTS, "pre_tool_guard.py")],
                           input=b"NOT JSON{{{", stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, env=env, timeout=30)
        check("malformed stdin fails open", p.returncode == 0)

        # ---------------- tool_event ----------------------------------
        print("\n[tool_event]")
        rc, out, _ = run_hook("tool_event.py", base(project,
                              hook_event_name="PostToolUse", tool_name="Edit",
                              tool_input={"file_path": "/app/svc/main.py"},
                              tool_response={}), project)
        st = read_state(project)
        check("edit armed stop-gate", st["edits_since_verify"] == 1, str(st)[:200])

        err_resp = "Command failed with exit code 1\nFileNotFoundError: config.yaml"
        for i in range(2):
            rc, out, _ = run_hook("tool_event.py", base(project,
                                  hook_event_name="PostToolUse", tool_name="Bash",
                                  tool_input={"command": "python3 svc/main.py"},
                                  tool_response=err_resp), project)
        ctx = ((out or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")
        check("strategy nudge on 2nd identical error", "Do NOT retry" in ctx, ctx[:120])

        rc, out, _ = run_hook("tool_event.py", base(project,
                              hook_event_name="PostToolUse", tool_name="Bash",
                              tool_input={"command": "pytest -q"},
                              tool_response="2 passed in 0.1s"), project)
        st = read_state(project)
        check("verify pass resets gate", st["edits_since_verify"] == 0
              and st["last_verify"] == "pass", str(st)[:200])

        # ---------------- stop_gate -----------------------------------
        print("\n[stop_gate]")
        rc, out, _ = run_hook("stop_gate.py", base(project,
                              hook_event_name="Stop", stop_hook_active=False), project)
        check("no block when verified", not out or out.get("decision") != "block")

        run_hook("tool_event.py", base(project, hook_event_name="PostToolUse",
                 tool_name="Edit", tool_input={"file_path": "/app/svc/api.py"},
                 tool_response={}), project)
        rc, out, _ = run_hook("stop_gate.py", base(project,
                              hook_event_name="Stop", stop_hook_active=False), project)
        check("blocks after unverified edit", out and out.get("decision") == "block",
              json.dumps(out)[:200] if out else "none")
        rc, out, _ = run_hook("stop_gate.py", base(project,
                              hook_event_name="Stop", stop_hook_active=True), project)
        check("respects stop_hook_active", not out or out.get("decision") != "block")
        rc, out, _ = run_hook("stop_gate.py", base(project,
                              hook_event_name="Stop", stop_hook_active=False), project)
        rc, out, _ = run_hook("stop_gate.py", base(project,
                              hook_event_name="Stop", stop_hook_active=False), project)
        check("max 2 blocks per session", not out or out.get("decision") != "block",
              json.dumps(out)[:160] if out else "")

        # ---------------- precompact + handoff round-trip --------------
        print("\n[precompact]")
        rc, out, _ = run_hook("precompact.py", base(project,
                              hook_event_name="PreCompact", trigger="auto"), project)
        hpath = os.path.join(project, ".firefly", "handoff.md")
        check("handoff written", os.path.exists(hpath))
        rc, out, _ = run_hook("session_start.py", base(project, source="compact",
                              hook_event_name="SessionStart"), project)
        ctx = ((out or {}).get("hookSpecificOutput") or {}).get("additionalContext", "")
        check("handoff re-injected post-compact", "Handoff from previous context" in ctx)

        # ---------------- session_end + distiller ----------------------
        print("\n[session_end]")
        rc, out, err = run_hook("session_end.py", base(project,
                                hook_event_name="SessionEnd", reason="exit"), project)
        check("exit 0", rc == 0, err[:200])
        cands = []
        cpath = os.path.join(project, ".firefly", "candidates.jsonl")
        if os.path.exists(cpath):
            with open(cpath, encoding="utf-8") as f:
                cands = [json.loads(l) for l in f if l.strip()]
        kinds = {c["kind"] for c in cands}
        check("error-streak candidate distilled", "friction" in kinds, str(kinds))

        # ---------------- curator: proposals lifecycle -----------------
        print("\n[curator]")
        sys.path.insert(0, SCRIPTS)
        os.environ["CLAUDE_PROJECT_DIR"] = project
        import lib_firefly as ff  # noqa: E402
        import curator  # noqa: E402
        payload = {"cwd": project, "session_id": "sess-test-1"}

        props = os.path.join(project, ".firefly", "proposals.jsonl")
        with open(props, "w", encoding="utf-8") as f:
            f.write(json.dumps({"op": "add", "scope": "sre", "tags": ["helm"],
                                "lesson": "Always run `helm template | kubeconform` before helm upgrade in any cluster.",
                                "evidence": ["sess-test-1: failed upgrade"]}) + "\n")
            f.write(json.dumps({"op": "add", "scope": "dev", "tags": ["python"],
                                "lesson": "Pin Python dependencies with exact versions in airgapped builds; resolver has no index access.",
                                "origin": "human"}) + "\n")
        n = curator.consume_proposals(payload)
        check("proposals applied", n == 2, "n=%s" % n)
        check("proposals consumed (file gone)", not os.path.exists(props))
        pb = curator.load_playbook(payload)
        auto = [l for l in pb["lessons"] if l["origin"] == "auto"][0]
        human = [l for l in pb["lessons"] if l["origin"] == "human"][0]
        check("auto lesson quarantined", auto["status"] == "quarantined")
        check("human lesson active", human["status"] == "active")

        # dedup: re-adding similar lesson must merge, not duplicate (x2 -> promote)
        for _ in range(2):
            with open(props, "w", encoding="utf-8") as f:
                f.write(json.dumps({"op": "add", "scope": "sre", "tags": ["helm"],
                                    "lesson": "Always run helm template | kubeconform before a helm upgrade in any cluster!"}) + "\n")
            curator.consume_proposals(payload)
        pb = curator.load_playbook(payload)
        check("dedup merged (still 2 lessons)", len(pb["lessons"]) == 2,
              "n=%d" % len(pb["lessons"]))
        merged = [l for l in pb["lessons"] if l["id"] == auto["id"]][0]
        check("dedup bumped helpful + promoted", merged["helpful"] >= 2
              and merged["status"] == "active", str(merged)[:160])

        # feedback: harmful auto-quarantines
        with open(props, "w", encoding="utf-8") as f:
            f.write(json.dumps({"op": "feedback", "id": merged["id"], "harmful": 4}) + "\n")
        curator.consume_proposals(payload)
        pb = curator.load_playbook(payload)
        merged = [l for l in pb["lessons"] if l["id"] == auto["id"]][0]
        check("harmful feedback quarantines", merged["status"] == "quarantined")

        check("PLAYBOOK.md rendered",
              os.path.exists(os.path.join(project, ".firefly", "PLAYBOOK.md")))
        check("audit log written",
              os.path.exists(os.path.join(project, ".firefly", "audit.log")))

        # injection selection respects budget & status
        chosen = curator.select_for_injection(payload)
        ids = [l["id"] for l, _ in chosen]
        check("injection includes active human lesson", human["id"] in ids, str(ids))

        # ---------------- automatic learning ---------------------------
        print("\n[auto-learning]")
        import distill  # noqa: E402
        cand_path = os.path.join(project, ".firefly", "candidates.jsonl")

        # (a) cross-session recurrence -> deterministic proposals
        with open(cand_path, "a", encoding="utf-8") as f:
            for sid_n in ("sess-a", "sess-b"):
                f.write(json.dumps({
                    "ts": "2026-01-01T00:00:00Z", "sid": sid_n, "kind": "friction",
                    "key": "err:deadbeef01", "status": "new",
                    "summary": "Same error repeated 2x (digest deadbeef01).",
                    "evidence": ["ImagePullBackOff: registry.internal timeout"],
                }) + "\n")
                f.write(json.dumps({
                    "ts": "2026-01-01T00:00:00Z", "sid": sid_n, "kind": "behavior",
                    "key": "corr:" + sid_n, "status": "new",
                    "summary": "User corrected the assistant 2 times.",
                    "evidence": [],
                }) + "\n")
        n_auto = distill.auto_propose(payload)
        check("auto_propose emits 2 ops (err + behavior)", n_auto == 2, "n=%s" % n_auto)
        props_rows = [json.loads(l) for l in open(props, encoding="utf-8") if l.strip()]
        check("auto ops are adds with origin auto", all(
            r["op"] == "add" and r.get("origin") == "auto" for r in props_rows),
            str(props_rows)[:200])
        check("recurring candidates marked promoted", not [
            c for c in distill.fresh_candidates(payload, "sess-a")
            if c["key"].startswith(("err:", "corr:"))])
        n_again = distill.auto_propose(payload)
        check("auto_propose idempotent", n_again == 0, "n=%s" % n_again)
        curator.consume_proposals(payload)
        pb = curator.load_playbook(payload)
        autos = [l for l in pb["lessons"] if "auto" in l.get("tags", [])]
        check("auto lessons land quarantined", autos
              and all(l["status"] == "quarantined" for l in autos),
              str([(l["id"], l["status"]) for l in autos]))

        # (b) implicit feedback from clean verified sessions
        st_fb = {"session_id": "sess-fb", "turns": 5, "corrections": 0,
                 "verify_seen": True, "last_verify": "pass",
                 "injected_lessons": [human["id"]]}
        n_fb = distill.implicit_feedback(payload, st_fb)
        check("implicit feedback on clean session", n_fb == 1, "n=%s" % n_fb)
        st_fb["corrections"] = 2
        check("no implicit feedback when corrected",
              distill.implicit_feedback(payload, st_fb) == 0)
        before = [l for l in curator.load_playbook(payload)["lessons"]
                  if l["id"] == human["id"]][0]["helpful"]
        curator.consume_proposals(payload)
        after = [l for l in curator.load_playbook(payload)["lessons"]
                 if l["id"] == human["id"]][0]["helpful"]
        check("feedback op applied (+1 helpful)", after == before + 1,
              "%s -> %s" % (before, after))

        # (c) Stop-hook auto-retro fires once per session
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"learning": {"auto_reflect": True}}, f)
        st_r = {"session_id": "sess-reflect", "turns": 5, "corrections": 0,
                "edits_since_verify": 0,
                "error_streaks": {"d1aaaaaaaaaa": 2, "d2bbbbbbbbbb": 2}}
        ff.save_state({"cwd": project}, st_r)
        rc, out, err = run_hook("stop_gate.py", base(project, sid="sess-reflect",
                                hook_event_name="Stop", stop_hook_active=False),
                                project)
        check("auto-retro blocks with instructions", out
              and out.get("decision") == "block"
              and "auto-retro" in out.get("reason", "")
              and "proposals.jsonl" in out.get("reason", ""),
              (json.dumps(out)[:200] if out else "no output, err=" + err[:120]))
        check("reflected flag persisted",
              read_state(project, "sess-reflect").get("reflected") is True)
        rc, out, _ = run_hook("stop_gate.py", base(project, sid="sess-reflect",
                              hook_event_name="Stop", stop_hook_active=False),
                              project)
        check("auto-retro fires only once", not out or out.get("decision") != "block",
              json.dumps(out)[:160] if out else "")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"learning": {"auto_reflect": False}}, f)

        # (d) session_start records injected lesson ids for implicit feedback
        rc, out, _ = run_hook("session_start.py", base(project, source="startup",
                              hook_event_name="SessionStart"), project)
        check("injected lessons recorded in state",
              read_state(project).get("injected_lessons"),
              str(read_state(project).get("injected_lessons")))

        # ---------------- lib unit checks ------------------------------
        print("\n[lib]")
        check("classify read", ff.classify_command("kubectl get pods")[0] == "read")
        check("classify mutate", ff.classify_command("kubectl scale deploy x --replicas=3")[0] == "mutate")
        check("classify destroy chained",
              ff.classify_command("ls; helm uninstall x")[0] == "destroy")
        check("protected match",
              ff.targets_protected("kubectl apply -n prod-eu1 -f x.yaml",
                                   ff.DEFAULT_CONFIG))
        check("not protected",
              not ff.targets_protected("kubectl apply -n dev -f x.yaml",
                                       ff.DEFAULT_CONFIG))
        check("verify regex pytest", ff.is_verify_command("python3 -m pytest tests/"))
        check("verify regex helm lint", ff.is_verify_command("helm lint ./chart"))
        check("correction detect", ff.looks_like_correction("No, that's wrong."))
        check("normal prompt not correction",
              not ff.looks_like_correction("Add a logging middleware"))
        check("error from dict resp",
              ff.tool_response_error({"exit_code": 2, "output": "boom"}) != "")
        check("success dict resp",
              ff.tool_response_error({"exit_code": 0, "output": "fine"}) == "")

        # ---------------- structure lint -------------------------------
        print("\n[structure]")
        structure_lint()

    finally:
        os.environ.pop("CLAUDE_PROJECT_DIR", None)
        shutil.rmtree(project, ignore_errors=True)

    print("\n%d passed, %d failed" % (PASS, len(FAIL)))
    if FAIL:
        for f in FAIL:
            print("  FAILED: %s" % f)
        sys.exit(1)
    print("ALL GREEN")


if __name__ == "__main__":
    main()
