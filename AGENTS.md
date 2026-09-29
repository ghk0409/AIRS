# AIRS v0.4.1 Repository

## Purpose

This repository contains the AIRS standard, reusable templates, stack profiles, canonical skills, and the v0.4.1 local orchestration CLI.

## Start

1. Read this file.
2. Read `standards/STANDARD.md` for normative principles.
3. Read only the standard, profile, template, or skill relevant to the task.
4. Do not load every profile or skill by default.

## Map

- Context rules and budgets: `standards/CONTEXT.md`
- Task lifecycle: `standards/WORKFLOW.md`
- Security boundaries: `standards/SECURITY.md`
- Rollout guidance: `standards/ADOPTION.md`
- Stack overlays: `profiles/`
- Canonical workflows: `.agents/skills/`
- Copyable files: `templates/`
- Example configuration: `airs.example.yaml`
- Runtime configuration: `airs.yaml`
- Task Contract schema: `schemas/task-contract.schema.json`
- CLI implementation: `src/airs/`
- Router and adapter tests: `tests/`

## Change rules

- Preserve agent neutrality; describe outcomes and invariants rather than tool-specific commands.
- Keep `AGENTS.md` files as routers, not encyclopedias.
- Put context in the narrowest layer that owns it.
- Avoid duplicating canonical content across templates.
- Treat budgets as guidance unless a security or project rule makes a bound mandatory.
- Keep examples free of credentials, internal hostnames, and production data.
- When changing a skill, validate its `SKILL.md` frontmatter and ensure its description is precise.

## Completion

- Check links and paths touched by the change.
- Confirm templates contain no unintended organization-specific information.
- Summarize changed files, validation, and unresolved decisions concisely.
