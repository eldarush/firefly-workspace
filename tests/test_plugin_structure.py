import json
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "firefly-workspace"


REQUIRED_SKILLS = {
    "architect",
    "context-map",
    "deep-research",
    "implementation-loop",
    "verify-and-reflect",
    "mine-skill",
    "sre-ops",
    "qa-release",
    "prompt-upgrade",
    "offline-release",
    "governance",
}

REQUIRED_AGENTS = {
    "firefly-architect.md",
    "codebase-cartographer.md",
    "plan-critic.md",
    "implementation-worker.md",
    "verification-sentinel.md",
    "sre-diagnostician.md",
    "qa-strategist.md",
    "security-governor.md",
    "workflow-miner.md",
}


class PluginStructureTests(unittest.TestCase):
    def test_marketplace_references_firefly_workspace_plugin(self):
        marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(marketplace["name"], "fireflyteam")
        plugin_names = {entry["name"] for entry in marketplace["plugins"]}
        self.assertIn("firefly-workspace", plugin_names)

    def test_plugin_manifest_is_claude_code_native(self):
        manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "firefly-workspace")
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertTrue(manifest["defaultEnabled"])
        self.assertIn("userConfig", manifest)

    def test_default_agent_and_hooks_are_configured(self):
        settings = json.loads((PLUGIN / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["agent"], "firefly-architect")

        hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        for event_name in ("SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUseFailure", "Stop"):
            self.assertIn(event_name, hooks["hooks"])

    def test_required_agents_exist_with_frontmatter(self):
        existing = {path.name for path in (PLUGIN / "agents").glob("*.md")}
        self.assertTrue(REQUIRED_AGENTS.issubset(existing))
        for filename in REQUIRED_AGENTS:
            text = (PLUGIN / "agents" / filename).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), filename)
            self.assertIn("description:", text, filename)

    def test_required_skills_exist_with_frontmatter_and_examples(self):
        existing = {path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir()}
        self.assertTrue(REQUIRED_SKILLS.issubset(existing))
        for skill in REQUIRED_SKILLS:
            text = (PLUGIN / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), skill)
            self.assertIn("description:", text, skill)
            self.assertIn("## Output", text, skill)

    def test_governance_assets_exist(self):
        required_files = [
            "policy/commands.yaml",
            "policy/mcp_allowlist.example.json",
            "schemas/proposal.schema.json",
            "schemas/audit-event.schema.json",
            "evals/prompt-injection-corpus.jsonl",
        ]
        for relative in required_files:
            path = PLUGIN / relative
            self.assertTrue(path.exists(), relative)
            self.assertGreater(path.stat().st_size, 20, relative)


if __name__ == "__main__":
    unittest.main()
