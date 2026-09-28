---
name: implement
description: Implement a requested feature or behavior change in an AIRS repository. Use when code or configuration should be changed; use debug for root-cause investigation and review for read-only assessment.
---

# Implement

Deliver the smallest coherent change that satisfies the requested behavior and repository constraints.

## Context

1. Read the nearest `AGENTS.md` and, when work is active or continuing, `tasks/CURRENT.md`.
2. Classify the task. For M or larger work, read the referenced Spec and Tasks; for L or XL work, also read the Plan and relevant ADR.
3. Load the selected stack profile and only the source and tests needed to trace the affected behavior.
4. Expand to architecture, workspace, another repository, or external documentation only when a boundary or contract requires it.

## Work

- Confirm the observable outcome and acceptance criteria before editing.
- Inspect the current implementation and tests; preserve established local patterns unless the task intentionally changes them.
- Respect authorization, public contracts, data ownership, migrations, and rollback constraints.
- Keep edits within scope and preserve unrelated working-tree changes.
- Add or update tests at the lowest level that proves the behavior. Avoid tests coupled only to implementation detail.
- Do not edit generated output when its source can be changed and regenerated.

If the requested outcome conflicts with current evidence or needs a consequential unmade decision, stop and surface the decision rather than inventing policy.

## Verify and finish

Run focused checks first, then broader checks proportional to risk. Record what passed, failed, and was not run. Update the active Tasks and `CURRENT.md` when state materially changes. Report the outcome, changed surface, verification, and remaining issues concisely.
