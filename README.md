# AIRS v0.4.2

[한국어 README](README.ko.md)

[Project adoption guide (Korean)](PROJECT_ADOPTION.ko.md)

AIRS (AI-native Repository Standard) combines the original agent-agnostic repository convention with a local CLI that routes work to subscription-backed Codex and Antigravity agents. It does not call the OpenAI or Gemini developer APIs.

Its central rule is:

> Context belongs to the narrowest scope that owns it.

The repository is the source of truth. Chat history is temporary working context, not project memory. The v0.1 standard remains the compatibility baseline; v0.4.2 improves per-project adoption and long-review configuration without weakening those rules.

## Orchestration

```text
Task Contract
    │
    ▼
Rule Router ── clear case ───────────────┐
    │ ambiguous                         │
    ▼                                   │
Jev assessment                          │
(type/complexity/risk/reason/review)     │
    └──────────────┬─────────────────────┘
                   ▼
              Policy engine
        (tier minimums and guardrails)
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Codex CLI          agy CLI
          └────────┬────────┘
                   ▼
       optional cross-model review
                   ▼
          .airs/history/<run-id>
```

Jev is a decision signal only. It never executes an agent or bypasses policy. The policy engine maps the abstract `light`, `medium`, `high`, and `ultra` tiers to provider-specific model and reasoning settings.

The current default mapping is:

| Tier | Codex | Antigravity |
|---|---|---|
| light | `gpt-5.6-luna` / low | `gemini-3.8-flash-low` |
| medium | `gpt-5.6-terra` / medium | `gemini-3.8-flash-medium` |
| high | `gpt-5.6-sol` / high | `gemini-3.8-flash-high` |
| ultra | `gpt-6-astra` / xhigh | `gemini-3.8-flash-high` |

Antigravity currently lists effort-specific model IDs, so its model and `--effort` settings are kept in sync. Its highest available Gemini 3.8 Flash effort is high. Adjust the YAML mapping if an account exposes a different model catalog.

Codex model availability varies by ChatGPT account and rollout. The default light–high mapping uses the GPT-5.6 family for accounts where GPT-6 Luna and Sol are not yet enabled; ultra keeps GPT-6 Astra where available. Check the Codex CLI `/model` picker before changing these mappings for your account.

## Install and configure

Prerequisites are Python 3.11+, `uv`, a Codex CLI login backed by a ChatGPT subscription, and an `agy` login backed by the user's Google subscription. Configure those CLIs directly; AIRS does not accept or store OpenAI/Gemini API keys. The adapter process explicitly removes common OpenAI, Gemini, Google, and Jev developer-key variables while preserving normal CLI login state.

```bash
uv sync --extra dev
mkdir -p ~/.config/airs
chmod 700 ~/.config/airs
cp .env.example ~/.config/airs/.env
chmod 600 ~/.config/airs/.env
# Edit ~/.config/airs/.env and set JEV_API_KEY to your real key.
uv run airs plan -p "Add a small unit test"
```

`routing.jev.api_key_env: JEV_API_KEY` names the key; it is not the secret value and can be committed. Put the real key on the `JEV_API_KEY=` line of `~/.config/airs/.env`. AIRS reads this file automatically on every invocation, so a new terminal needs no `export` or `.zshrc` change. The file is outside Git repositories by default. AIRS checks the process environment first, then the target project's `.env`, then `~/.config/airs/.env` (or `$XDG_CONFIG_HOME/airs/.env`). A project `.env` is also supported, but add `.env` to that project's `.gitignore` and note that an agent working inside the project may be able to read it; the user-level file is safer. AIRS reads only the configured key and does not export file contents into agent subprocesses. Copy `airs.yaml` when provider model names or policy settings need customization. `AIRS_CONFIG` may point to another configuration file, and `routing.jev.api_key_env` may name a different variable. Never put the key value in YAML, `.env.example`, or a tracked file.

The default Jev endpoint is TypeSafe's official System One API at `https://api.typesafe.ai/v1/systemone`, using the configurable `jev-latest` model. The key must come from the TypeSafe console; keys issued by other Jev gateways are not interchangeable. The task title, objective, role, context, constraints, acceptance criteria, and risk hints are sent for ambiguous tasks. Do not place secrets or unrelated private data in those fields.

## Task Contract

Task files are YAML or JSON and conform to `schemas/task-contract.schema.json`:

```yaml
id: feature-123
title: Add cache invalidation
objective: Invalidate cached profiles after a successful update.
project_root: /absolute/path/to/project
role: implementer
context:
  - Profile writes happen in src/profile/service.py.
constraints:
  - Preserve the public API.
acceptance_criteria:
  - Updated profiles are visible immediately.
verification:
  commands:
    - uv run pytest tests/profile
  criteria:
    - Existing profile behavior remains compatible.
risk_hints: []
```

Supported roles are `implementer`, `planner`, `reviewer`, `tester`, `debugger`, and `security-reviewer`.

## CLI

For day-to-day use, install the command once from this repository, then run it inside the repository you want to change:

```bash
uv tool install .
cd /path/to/target-repository
airs run -p "Add a regression test for the login bug" --verify-cmd "git diff --check"
```

When updating an existing installation from this checkout, run `uv tool install --force --reinstall .` in the AIRS repository. `--force` alone can reuse a cached wheel for the same package version. If a target repository has its own `airs.yaml`, check its `routing.jev.endpoint` and `routing.jev.model` too: that local file overrides AIRS's built-in defaults.

The inline request creates a temporary Task Contract in memory using the current directory as `project_root`. `run` plans the route, runs the selected agent, performs any policy-required cross-model review, and runs configured verification commands. `--verify-cmd` can be repeated. The key environment variable remains available to AIRS but is removed from the subprocess environments of Codex and agy. Add `.airs/` to the target repository's `.gitignore` because run history is stored there.

Use `airs plan -p "..."` to inspect routing without running an agent. `airs run -p "..." --dry-run` shows the planned commands. For projects outside the current directory, pass `--root /path/to/project` with `-p`. A detailed Task Contract file is optional and remains useful for repeatable work, constraints, acceptance criteria, and shared verification rules. `examples/task.yaml` demonstrates the format; its README typo request is not tied to a known typo, so create a real task before running it.

```bash
uv run airs plan TASK.yaml
uv run airs run TASK.yaml
uv run airs review TASK.yaml
uv run airs verify TASK.yaml
uv run airs status --root /path/to/project
uv run airs doctor
```

`plan`, `run`, and `review` accept `--provider codex|antigravity`, `--tier light|medium|high|ultra`, and `--no-review`. Provider and tier mappings live in `airs.yaml`. A lower tier or `--no-review` cannot weaken a high-risk policy minimum. Use `--dry-run` with `run`, `review`, or `verify` to inspect behavior without invoking an agent or verification command.

`run` executes the selected provider and, when required, invokes the other provider in read-only/plan mode for independent review. The primary prompt asks the agent to consult the project's root `AGENTS.md` and task-relevant pointers; this does not expand the cross-model review scope. AIRS snapshots existing Git changes before the primary run and reviews only files newly changed by that run. `verify` reruns Task Contract commands directly without a shell. Verification still runs if the review fails; the final status reports review and verification failures separately. Each operation records its decision, command, result, output, and timing under the target project's `.airs/history/`; this directory may contain sensitive task output and is ignored only when the target repository excludes it.

To retry a review without rerunning the primary agent or Jev, use `airs review --run-id RUN_ID` from the target repository. The run history records the review file list and hashes so a later edit cannot silently change its scope. Older runs without that list use current Git changes. For an ad-hoc review, use repeatable `--file PATH` arguments; otherwise AIRS uses current changed files and refuses a repository-wide scan. The default maximum is 12 files (`review.max_files`). Deleted Git files are reviewed through a bounded text patch; binary or oversized patches require separate review. `airs status --run-id RUN_ID` shows a specific run.

```bash
airs review --run-id RUN_ID --provider antigravity
airs review -p "Check this documentation update" --file docs/PROJECT_OVERVIEW.md --file README.md --provider antigravity
```

Antigravity reviews use plan mode and a terminal sandbox. AIRS asks the reviewer to inspect files with workspace-reading tools instead of shell commands. The review has a 600-second limit by default (`providers.antigravity.review_timeout_seconds` in `airs.yaml`), plus limits of 20 tool calls and 120,000 input tokens. A target project can override the timeout with a small local `airs.yaml`, as shown in [the example](examples/project-airs.yaml). AIRS reads `stream-json` progress events to display file reads and token usage, and stops a runaway review at its limits. A denied action, timeout, empty response, or non-success status fails the review even if `agy` exits with code 0. If a review genuinely needs a terminal command, add only a narrowly scoped `permissions.allow` rule in Antigravity's global `~/.gemini/antigravity-cli/settings.json`; those rules apply beyond AIRS, so review their scope carefully. Do not use `--dangerously-skip-permissions` for routine reviews.

`airs doctor` checks the configured Jev key without printing it, verifies the provider CLIs, probes Codex login status, compares configured Codex models and effort levels with the logged-in CLI's visible catalog (`codex debug models`), and compares configured Antigravity models with `agy models`. `airs doctor --offline` skips login/catalog probes. The Codex catalog command is a debug interface that may change with CLI versions; an actual run remains the final access check.

History files are written atomically with owner-only file permissions. `airs history prune` previews runs older than `history_retention_days` (30 by default); add `--apply` to remove those exact run directories. `airs history scrub RUN_ID` previews removal of task text, commands, agent output, and rationale from one record; add `--apply` to redact it. Scrubbed runs cannot be used with `review --run-id`. These actions are never automatic.

In an interactive terminal, `run` and `review` show the active agent stage immediately and report elapsed time every 10 seconds. Agent output is printed at the end of the run and retained in history. Machine-readable `--json` output omits progress messages.

## What is included

```text
.
├── AGENTS.md                  # router for this standards repository
├── airs.example.yaml          # example AIRS configuration
├── airs.yaml                  # runnable router/provider configuration
├── pyproject.toml             # Python package and airs command
├── schemas/                   # Task Contract schema
├── src/airs/                  # router, policy, adapters, workflow, history
├── tests/                     # unit and dry-run integration tests
├── standards/                 # normative AIRS documents
├── profiles/                  # stack-specific overlays
├── .agents/skills/            # reusable, agent-agnostic workflows
└── templates/
    ├── global/                # personal defaults
    ├── organization/          # company-wide catalog
    ├── workspace/             # relationships across repositories
    └── repository/            # files copied into an application repo
```

## The four layers

| Layer | Owns | Typical location |
|---|---|---|
| Global | Personal, portable defaults and skills | `~/.airs/` or agent-specific global config |
| Organization | Shared standards, profiles, approved skills | Dedicated standards Git repository |
| Workspace | Repository map and cross-repository decisions | Parent directory containing related repositories |
| Repository | Project rules, active work, specs, code, repository ADRs | Each Git repository |

Narrower rules override broader rules. A repository-specific skill may refine an organization skill, which may refine a global skill. Security policy and explicit user instructions are never weakened by an override.

## Quick start: one repository

1. Inspect the target repository's existing files, then merge only the needed contents of `templates/repository/` without overwriting local work. `airs.project.yaml` is optional project metadata; a separate `airs.yaml` controls the CLI.
2. Copy only the needed skill folders from `.agents/skills/` into the target repository's `.agents/skills/` directory. Copy all seven for the default starter.
3. Choose one profile under `profiles/`, then reference its name and location from the target `AGENTS.md`.
4. Replace every `{{PLACEHOLDER}}` and remove unused template guidance.
5. Fill `tasks/CURRENT.md`; keep it short and commit the result.

Example:

```bash
mkdir -p /path/to/my-repo/tasks
cp -n templates/repository/AGENTS.md /path/to/my-repo/AGENTS.md
cp -n templates/repository/tasks/CURRENT.md /path/to/my-repo/tasks/CURRENT.md
```

This example skips existing files; review and merge any existing project rules manually. Add architecture documents, profiles, and skills only as needed. See the [project adoption guide](PROJECT_ADOPTION.ko.md) for a worked example, the distinction between `airs.project.yaml` and CLI `airs.yaml`, and a per-project review timeout override.

## Quick start: multiple repositories

1. Create or designate a parent workspace directory.
2. Copy `templates/workspace/WORKSPACE.md`, `workspace.yaml`, and `docs/` to that directory.
3. List each Git repository, its path, profile, purpose, and only the relationships needed for cross-repository work.
4. Keep each repository's `AGENTS.md` and `tasks/CURRENT.md` independent.

Workspace context is not loaded for ordinary repository-local tasks. Read it only when the task crosses a repository boundary or depends on another service.

## Default context path

```text
AGENTS.md
  -> tasks/CURRENT.md
  -> active spec and relevant skill
  -> target source and tests
  -> ADR or architecture, if needed
  -> workspace, other repositories, or external docs, if needed
```

Stop expanding context as soon as there is enough evidence to act safely. See `standards/CONTEXT.md` for budgets and exceptions.

## Task artifact policy

| Size | Typical work | Required artifact |
|---|---|---|
| XS | Typo, local rename | None |
| S | Small bug | `CURRENT.md` |
| M | Endpoint or contained feature | Spec + tasks |
| L | New module or domain | Spec + plan + tasks |
| XL | Architectural or cross-repository change | Spec + plan + ADR + tasks |

These are guidelines, not ceremony. Increase or reduce documentation when risk, reversibility, or coordination requires it.

## Agent compatibility

`.agents/skills` is the canonical skill location in AIRS. Agent-specific files should be thin adapters that point to the canonical instructions. Prefer a symlink only when every supported operating system and tool handles it reliably; otherwise use a small, reviewed synchronization step. Do not maintain divergent copies by hand.

## Adoption

Start with one active repository and measure whether agents find the right context without broad scans. Expand to workspace and organization layers only after the repository layer is useful. The full rollout checklist is in `standards/ADOPTION.md`.

## Validation

```bash
uv run --extra dev pytest
uv run python -m compileall -q src tests
```

Tests mock the Jev transport and use adapter dry runs, so they neither consume Jev credit nor agent subscription allowance.

## Status

AIRS v0.4.2 is a local-first orchestration reference implementation. Deleted Git files are included in scoped review using a bounded text patch (30,000 characters); binary or larger deleted-file patches fail safely and require separate review. Provider model names remain configurable because availability can vary by subscription and CLI release. Future work includes labeled routing evaluations, retries with backoff, and richer provider capability discovery.
