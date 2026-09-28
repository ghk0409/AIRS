# {{PROJECT_NAME}}

## Project

{{ONE_OR_TWO_SENTENCE_PURPOSE}}

Stack: {{PRIMARY_STACK}}

## Start

1. Read `tasks/CURRENT.md` when continuing or changing active work.
2. Read the active Spec, Plan, or Tasks only when referenced or required by task size.
3. Load the relevant skill from `.agents/skills/`.
4. Inspect only the source and tests relevant to the requested behavior.
5. Read a specific ADR or `docs/ARCHITECTURE.md` only when a decision or boundary is unclear.
6. Read workspace context or another repository only for an actual cross-repository dependency.

## Profile

- Profile: `{{PROFILE_NAME_OR_NONE}}`
- Source: `{{PROFILE_PATH_OR_REFERENCE}}`

## Repository rules

- {{STABLE_PROJECT_INVARIANT}}
- {{LOCAL_COMMAND_OR_BOUNDARY_THAT_CHANGES_DECISIONS}}
- Preserve unrelated working-tree changes.
- Do not modify generated files directly.

## Map

- Current state: `tasks/CURRENT.md`
- Architecture: `docs/ARCHITECTURE.md`
- Active specs: `specs/active/`
- ADRs: `docs/adr/`
- Skills: `.agents/skills/`

## Context efficiency

- Prefer targeted search; do not recursively scan the repository by default.
- Exclude dependencies, build output, coverage, generated code, dumps, large fixtures, and full logs unless directly relevant.
- Stop loading context when there is enough evidence to implement and verify safely.
- Keep final reports to outcome, changed files, verification, and remaining issues.

## Verification

- Fast checks: `{{TARGETED_TEST_OR_CHECK_COMMAND}}`
- Broader checks: `{{FULL_TEST_OR_VALIDATION_COMMAND}}`

## Completion

Before stopping, update task status and `tasks/CURRENT.md` with truthful progress, verification, blockers, and the next action. Do not use chat history as the only handoff.
