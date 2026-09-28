---
name: migration
description: Plan or execute a versioned data, schema, API, dependency, platform, or infrastructure migration. Use when compatibility, sequencing, rollout, or recovery matters across old and new states.
---

# Migration

Move between states with explicit compatibility, validation, and recovery.

## Required context

Treat migrations as L or XL unless evidence supports a smaller class. Read the Spec, Plan, Tasks, relevant ADR, current state, owning profile, and affected contracts. Load workspace and other repository context only for actual consumers, producers, rollout dependencies, or shared data.

## Design

Document:

- source and target states;
- affected owners, environments, data, contracts, and versions;
- compatibility during mixed-version operation;
- ordered phases and stopping conditions;
- backfill or transformation rules, including idempotency;
- validation signals and acceptance thresholds;
- rollback feasibility or an explicit forward-fix strategy;
- backup and restore expectations for stateful changes.

Prefer expand-and-contract changes when old and new versions may coexist. Avoid irreversible steps until compatibility and validation gates are satisfied.

## Execute safely

- Verify the exact target and authorization before mutations.
- Use previews, plans, dry runs, samples, or non-production environments when available.
- Make each phase observable and resumable.
- Do not claim a migration, deployment, or rollback was executed without direct evidence.
- Stop when a validation gate fails; capture evidence before attempting a materially different action.

## Finish

Record completed phase, versions, counts or health signals, exceptions, checks, rollback state, and next action in durable artifacts. Create or update an ADR for durable architectural consequences. Remove compatibility paths only after their consumers and data are confirmed migrated.
