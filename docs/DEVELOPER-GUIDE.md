# Firefly Developer & Customization Guide

Welcome to the Firefly Workspace Developer Guide! Since your DevOps, SRE, QA, and Research teams operate in a highly secure, airgapped environment, this guide details how Firefly works under the hood, what it can and cannot do, what every directory contains, and how to customize, extend, and maintain it with low effort.

---

## 1. What Firefly CAN and CANNOT Do

Firefly enforces a strict operational model optimized for weaker, offline LLMs and airgapped clusters.

### What it CAN Do:
* **Orchestrate disciplined workflows**: Enforce senior-level engineering rigor (TDD, systematic debugging, pre-verification of edits, and plan-first coding) on models like MiniMax M2.5/M2.7.
* **Automatically learn and self-improve**: Every command, prompt, and session is analyzed. Repeated patterns automatically turn into quarantined playbook lessons, and successful sessions reinforce existing ones.
* **Propagate team learning**: Allow engineers to opt-into sharing validated, helpful lessons to a shared directory (e.g., an NFS mount or committed Git directory `.firefly-team/`) so that one engineer's learnings benefit the whole team.
* **Deny unsafe actions mechanically**: A deterministic Python hook blocks destructive commands (R4 class) and mutations targeting protected prod contexts (R3 class).
* **Reference an offline source of truth**: Pin GitLab URLs, container registry endpoints, cluster contexts, and Kiwix documentation (`WikiAll`) via `FIREFLY-ENV.md` so agents never hallucinate environment facts.

### What it CANNOT Do (and why):
* **No internet access**: It operates completely offline (all scripts use Python standard libraries only; no vector databases or external APIs).
* **No auto-approval of unsafe actions**: While the guard blocks dangerous commands, it never bypasses Claude Code's own permission prompt for normal mutations.
* **No automatic team-sharing without human confirmation**: Playbook changes are compiled into proposals, but sharing to the team store always prompts the user (Stop hook) to prevent low-quality or incorrect lessons from spreading.
* **No unverified session completions**: The Stop gate prevents the model from closing a session if edits were made but the project's verification checks have not been run.

---

## 2. Directory and File Map

Here is the exact structure of the Firefly Workspace repository:

```text
.claude-plugin/
  ├── plugin.json          # Main plugin manifest defining commands, agents, and hooks
  └── marketplace.json     # Declarative marketplace registry for installation
commands/                  # User-invokable workflows (disable-model-invocation: true)
  ├── init.md              # Initializes .firefly/ configs and appends CLAUDE.md contract
  ├── plan.md              # Interviews the user to establish a checked, approved plan
  ├── implement.md         # Executes a plan step-by-step with verify-before-completion
  ├── review.md            # Independent clean-context code reviews
  ├── debug.md             # Hypothesis-driven systematic incident/bug triage
  ├── research.md          # Offline documentation lookup and synthesis
  ├── parallel.md          # Best-of-N strategy brainstorming/test-runs
  ├── retro.md             # Generates playbook proposals from the session's friction
  ├── commit.md            # Runs pre-commit hygiene checks and formats commit messages
  ├── handoff.md           # Closes current task, compiles state, and prepares next session
  ├── lessons.md           # Inspects, manages, and overrides the playbook
  ├── skillgen.md          # Builds a reusable skill from repeated session commands
  ├── config.md            # Read/write tool for managing effective configs
  └── onboard.md           # Interactive onboarding tour for SRE/QA/DEV/Research
agents/                    # Specialist subagent definitions (bound roles, fresh context)
  ├── planner.md           # Guides the planning/interview phase
  ├── implementer.md       # Executes code changes with validation discipline
  ├── evaluator.md         # Evaluates changes from spec + diff in clean context
  ├── scout.md             # High-speed parallel codebase/logs explorers
  ├── researcher.md        # Extracts facts and synthesizes literature with citations
  ├── reflector.md         # Compiles cross-session friction trends during deep retros
  └── auditor.md           # Inspects generated skills/lessons against safety policy
skills/                    # Prompt-injected knowledge/workflow discipline packs
  ├── tdd/                 # Test-Driven Development discipline
  ├── systematic-debugging/# Root-cause analysis step-ladder
  ├── offline-docs-lookup/ # Integrates internal WikiAll ZIM docs & MCP lookups
  ├── sre-incident-triage/ # SRE-specific triage steps (observe, hypothesize, verify)
  ├── qa-test-design/      # QA risk-based and boundary-value test planning
  └── ... (20 more)        # Personas, writing-plans, model-discipline, etc.
hooks/
  └── hooks.json           # Declares hook events and maps them to Python entry points
scripts/                   # The Core Reflex Engine (Python 3.8+ stdlib, fail-open)
  ├── lib_firefly.py       # Shared core library (config, events, guard classification)
  ├── pre_tool_guard.py    # Classifies bash commands, blocks destroy/protected-mutate
  ├── session_start.py     # Housekeeping, injects contract, env facts, and lessons
  ├── prompt_submit.py     # Captures turns, detects corrections, nudges behavior
  ├── tool_event.py        # Flight recorder logging edits, errors, and verifier runs
  ├── stop_gate.py         # Enforces verification tests, triggers Stop-hook auto-retro
  ├── session_end.py       # Distills recurring patterns, votes up helpful lessons
  ├── curator.py           # Atomic applicator for playbook edits/dedup/lifecycle
  ├── team.py              # Shared team store logic (propagations, votes, unshared)
  └── team_share.py        # Stop-hook handler prompting user to share lessons to team
assets/                    # Resources and configuration templates
  ├── CLAUDE.snippet.md    # Codebase contract snippet appended to CLAUDE.md
  ├── config.schema.json   # JSON Schema for .firefly/config.json
  ├── config.example.json  # Complete example configuration
  ├── environment.template.md # Template for your org's FIREFLY-ENV.md
  └── templates/           # Output templates for plans, adrs, experiments, etc.
docs/                      # Deep-dive user and operator documentation
  ├── ARCHITECTURE.md      # Detailed component map, hook lifecycles, data flows
  ├── SAFETY.md            # Risk classifications, command guards, safety configurations
  ├── SELF-IMPROVEMENT.md  # Detailed lesson curation pipeline, auto-retro, decay
  ├── PERSONAS.md          # SRE, QA, DEV, and Research usage scenarios
  ├── INSTALL-airgapped.md # Secure mirroring, rollout templates, troubleshooting
  └── ADOPTION.md          # Adoption strategy, team rollout guide, and ROI metrics
```

---

## 3. How to Extend and Modify the Plugin

You can expand Firefly as your team’s tools, workflows, and infrastructure evolve.

### A. Adding a New Workflow Command
To add a new command, say `/ff:kargo` to help promote images in your Kargo pipelines:

1. **Create the Markdown file**: Add `commands/kargo.md`.
   ```markdown
   ---
   name: ff:kargo
   description: Promote a release image to a target stage in Kargo GitOps
   disable-model-invocation: true
   ---
   You are now driving the Kargo promotion workflow.
   
   1. Locate the target application in the `.firefly/config.json` or `FIREFLY-ENV.md`.
   2. Check the live state of the target stage using `/ff:scout` or reading GitOps properties.
   3. Draft the promotion candidate.
   4. Ask the human to approve the promotion before running `kargo promote`.
   ```
2. **Register it in the manifest**: Edit `.claude-plugin/plugin.json` to add your command.
   ```json
   "commands": {
     "ff:kargo": {
       "prompt": "commands/kargo.md"
     }
   }
   ```

### B. Adding a New Specialist Agent
To create a specialist agent, say a dedicated `argo-operator` agent:

1. **Create the Markdown file**: Add `agents/argo-operator.md`.
   ```markdown
   ---
   name: argo-operator
   description: ArgoCD operations specialist
   disallowedTools: [ "Bash" ] # Limit its tools if you want it to be read-only!
   ---
   You are the ArgoCD Operations Specialist. Your job is to inspect desired-vs-live sync status.
   You may call the offline-docs-lookup skill if you need help with ArgoCD API parameters.
   ```
2. **Register the agent**: Edit `.claude-plugin/plugin.json` to define the agent.
   ```json
   "agents": {
     "argo-operator": {
       "prompt": "agents/argo-operator.md"
     }
   }
   ```

### C. Adding a New Skill
To add a skill, e.g., `sre-k8s-debugging`:

1. **Create the directory and SKILL.md**: Create `skills/sre-k8s-debugging/SKILL.md`.
   ```markdown
   # Kubernetes SRE Debugging Discipline
   
   When troubleshooting Pod issues:
   1. Check events first: `kubectl get events --namespace <ns> --sort-by='.metadata.creationTimestamp'`
   2. Inspect container logs of previous restarts: `kubectl logs --previous`
   3. Analyze resource limits vs usage (never scale replicas up blindly).
   ```
2. **Register the skill in `plugin.json`**:
   ```json
   "skills": [
     "skills/sre-k8s-debugging/SKILL.md"
   ]
   ```

---

## 4. Customizing the Safety Guardrail

The safety guardrail classifies and screens commands. If your SRE team introduces new tools or protected namespaces, update `scripts/lib_firefly.py` and `scripts/pre_tool_guard.py`.

### Modifying Command Classifications:
Open `scripts/lib_firefly.py` and locate `classify_command(cmd, config)` (around line ~500).
* **Adding a new forbidden command pattern**:
  Add it to the `DESTROY_RES` regex list (which triggers immediate R4 block). E.g., adding `kargo delete` or a custom internal script:
  ```python
  DESTROY_RES = [
      r"\bkubectl\s+delete\b",
      r"\bkargo\s+delete\b",  # Custom add
      r"\bcurl\s+.*\s*\|\s*(sh|bash)\b", # Pipe-to-shell block
  ]
  ```
* **Adding a new mutation pattern**:
  Add it to `MUTATE_RES` (triggers R3 block if run inside protected contexts like `*prod*`):
  ```python
  MUTATE_RES = [
      r"\bkubectl\s+(apply|patch|scale|edit|exec)\b",
      r"\bkargo\s+promote\b", # Custom add
  ]
  ```

---

## 5. Offline Testing and Verification

When hacking on Firefly locally, use these commands to ensure everything is correct before rolling it out:

### 1. Validate the Plugin Manifest:
```bash
# Validates plugin.json structure and syntax
claude plugin validate .
```

### 2. Dry-Run the Command Guard:
You can test command classifications without launching a full Claude Code session:
```bash
# Verify that a dangerous command is correctly blocked:
python3 scripts/pre_tool_guard.py --check "kubectl delete namespace prod"

# Output should show classification: destroy and VERDICT: DENIED.
```

### 3. Verify the Shared Team-Store Flow:
You can manually trigger and trace the team propagation logic:
```bash
# Run stop_gate verification simulation:
python3 scripts/stop_gate.py --session-dir .firefly

# Run the team sharing confirmation:
python3 scripts/team_share.py --yes
```

---

## 6. How to Version and Release

When promoting updates to your team:
1. Increment the `version` field in both `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
2. Update `CHANGELOG.md` with your changes.
3. Commit and push the tag:
   ```bash
   git tag -a v1.3.0 -m "Firefly Workspace 1.3.0 - Custom Kubernetes addition"
   git push origin v1.3.0
   ```
4. Update your internal git mirror so your team can easily fetch the latest release.
