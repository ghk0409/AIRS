# Infrastructure Profile

Use this profile for repositories containing infrastructure as code, deployment manifests, CI/CD configuration, or platform operations. Repository and environment policies override these defaults.

## Baseline

- Treat rendered plans, manifests, and diffs as the review surface; do not assume source syntax alone proves the resulting change.
- Separate environments and verify the exact target before mutation.
- Keep secrets in approved secret stores and reference them by identifier only.
- Preserve least privilege, ownership boundaries, policy controls, and auditability.
- Avoid manual production-only changes that are not represented in the source of truth.

## Change design

- State dependencies, ordering, compatibility, blast radius, health signals, and rollback or forward-fix strategy.
- Prefer small, staged, reversible changes.
- Review resource limits, availability, persistence, networking, identity, and observability when affected.
- For stateful changes, define backup, restore, and data-compatibility expectations.

## Verification

Use the repository's safe validation path: format and static validation, render or plan, policy checks, tests, non-production rollout, health verification, then approved production rollout. Never report an apply or deployment that was not actually performed.

## Diagnostics

Start with a bounded time window, affected component, and relevant events or metrics. Avoid loading complete cluster inventories or full logs unless narrower evidence is insufficient.
