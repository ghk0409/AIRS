# Context Loading and Budgets

## Goal

Load enough evidence to act correctly without repeatedly paying for irrelevant project history. Budgets are default targets, not permission to omit information required for safety or correctness.

## Progressive loading algorithm

1. Read the nearest applicable `AGENTS.md`.
2. Read `tasks/CURRENT.md` when continuing, coordinating, or changing active work.
3. Classify the task size and load the referenced active Spec, Plan, Tasks, and relevant skill.
4. Inspect the smallest relevant source and test surface using targeted search.
5. If a decision or invariant remains unclear, read the specific ADR or architecture section.
6. If the task crosses a boundary, read `WORKSPACE.md`, then only the affected repositories and contracts.
7. Use external documentation, broad history, large logs, or repository-wide scans only when narrower evidence is insufficient.
8. Stop loading context once the task can be completed and verified safely.

## Default budgets

| Tier | Content | Target |
|---|---|---|
| 0 — Router | `AGENTS.md` | at most 1,500 tokens |
| 1 — State | `tasks/CURRENT.md` | at most 1,000 tokens |
| 2 — Task | Spec + Tasks + relevant Skill | at most 5,000 tokens |
| 3 — Source | Relevant source and test files | usually 10–15 files |
| 4 — Architecture | Specific ADR, architecture, workspace context | on demand |
| 5 — Expensive | Broad scans, large logs, generated code, history, multiple repos | avoid by default |

Measure and tune the budgets for the repository. Do not optimize token count at the expense of incorrect changes.

## Default exclusions

Unless the task directly concerns them, do not load:

- dependency directories such as `node_modules/` or vendored code;
- build output, coverage output, generated code, bundles, and lockfiles;
- database dumps, binary assets, large fixtures, or full log archives;
- archived specs or unrelated ADRs;
- complete Git history;
- other repositories in the workspace.

Prefer bounded log windows around a failure, targeted search results, changed-file diffs, and specific configuration sections.

## Cross-repository expansion test

Expand beyond the active repository only when at least one is true:

- the requested change explicitly names multiple repositories;
- a public contract or schema must change on both sides;
- integration behavior cannot be established from the local contract or tests;
- deployment order, compatibility, or rollback spans repositories;
- the active repository points to a workspace ADR that governs the change.

Record the affected repositories and contract in the Spec or `CURRENT.md`. Do not copy their internal implementation details into the active repository.

## Keeping context fresh

- `AGENTS.md` contains stable routing and invariants.
- `CURRENT.md` contains volatile state and should be rewritten, not endlessly appended.
- Specs contain desired behavior and boundaries.
- Plans contain an implementation approach that may evolve.
- Tasks contain checkable work items.
- ADRs contain durable decisions.
- Code, tests, schemas, and deployed configuration remain the authoritative implementation evidence.
