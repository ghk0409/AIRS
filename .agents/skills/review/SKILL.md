---
name: review
description: Review a code or configuration change for correctness, regressions, security, maintainability, and missing verification. Use for read-only assessment; do not edit unless the user separately requests changes.
---

# Review

Prioritize actionable defects supported by current code and change context.

## Scope

Read the nearest router, the requested diff or changed files, and only the contracts, tests, and call sites needed to assess them. Use the active Spec or ADR when the change claims to implement one. Preserve a read-only posture unless edits are explicitly requested.

## Evaluate

Check, in priority order:

1. correctness and unmet acceptance criteria;
2. security, authorization, privacy, tenant, and trust boundaries;
3. data loss, migration, compatibility, concurrency, transaction, and rollback risks;
4. error handling, resource lifecycle, retry, timeout, and operational behavior;
5. missing or misleading tests and documentation;
6. maintainability issues that create a concrete future failure mode.

Trace changed values across their boundaries. Consider failure paths and callers, not just the happy path. Avoid speculative style feedback already enforced by tooling and do not report pre-existing issues unless the change worsens or depends on them.

## Findings

For each finding, state severity, exact location, triggering conditions, impact, and a concise correction. Keep line ranges tight. If evidence is incomplete, label it as a question or residual risk rather than a defect.

Lead with findings ordered by severity, then list open questions and a brief verification summary. If there are no actionable findings, say so and name any material tests or risks not verified.
