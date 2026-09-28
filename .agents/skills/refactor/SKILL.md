---
name: refactor
description: Improve internal code structure while preserving externally observable behavior. Use for scoped restructuring, simplification, or dependency-boundary changes where behavior should remain stable.
---

# Refactor

Improve structure without silently changing the contract.

## Establish invariants

- Read the router, current state, relevant architecture boundary, and the smallest source and test surface affected.
- State which public behavior, data shape, side effect, performance property, or operational contract must remain unchanged.
- Run or identify baseline tests. Add characterization tests when important behavior is not otherwise protected.
- If behavior is intentionally changing, separate that work into an explicit implementation task or Spec.

## Change safely

- Make small, reviewable transformations with a clear structural purpose.
- Preserve public interfaces unless the task explicitly includes a coordinated migration.
- Keep dependency direction aligned with the repository architecture.
- Avoid mixing unrelated formatting, renaming, cleanup, and behavior changes.
- Delete obsolete code only after callers and runtime registration are checked.
- Reassess scope if the refactor crosses modules, repositories, persistence schemas, or deployment boundaries.

## Verify

Run focused tests after meaningful steps and broader checks proportional to the affected surface. Compare behavior, not just compilation. For performance-sensitive refactors, use the repository's existing measurement method and avoid unsupported claims.

Update Tasks and `CURRENT.md` with completed transformations, verification, residual risks, and the next safe step.
