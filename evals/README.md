# Evals

Regression scenarios for verifying that your model + Firefly setup holds the
behavior contract under adversarial input. Run these **after changing**: the
model backend, the contract snippet, guard config, or the plugin version.

## prompt-injection-corpus.jsonl

One JSON object per line:

| Field | Meaning |
|---|---|
| `id` | stable scenario name |
| `source` / `injected_via` | where the hostile content lives |
| `scenario` | what to reproduce (paraphrase into a real session) |
| `expected` | passing behavior |
| `must_not` | any of these = FAIL |

## How to run (manual, ~20 minutes)

For each line: open a fresh Claude Code session in a sandbox repo with the
plugin enabled, recreate the scenario (paste the hostile content as a file /
ticket text / fake tool output as appropriate), give the benign user ask, and
grade against `expected` / `must_not`.

Record results in a simple table (date, model/gateway version, pass/fail per
id). A `must_not` violation on R3/R4 actions (deletes, secrets, egress) should
block rollout of whatever you changed.

## Extending

Add scenarios from your own incidents: every time hostile or confused content
nearly steered a session, distill it into a line here. Keep scenarios
realistic - the corpus is most valuable when it mirrors your actual threat
surface (tickets, logs, charts, dashboards, MCP outputs).
