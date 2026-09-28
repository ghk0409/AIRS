# Python + FastAPI Profile

Use this profile for repositories whose primary application is a Python FastAPI service. Repository conventions override these defaults.

## Baseline

- Use the Python version, package manager, formatter, linter, and type checker declared by the repository.
- Keep type annotations at public boundaries and wherever they materially improve correctness.
- Separate transport schemas, application orchestration, domain behavior, and infrastructure adapters when the existing architecture uses those boundaries.
- Keep domain code independent of FastAPI and persistence details where practical.

## API changes

- Define explicit request and response models.
- Validate untrusted input at the boundary and map domain failures to stable API errors.
- Preserve documented status codes, error shapes, pagination, idempotency, and compatibility.
- Review authorization, audit, and tenant boundaries when access behavior changes.

## Data and async behavior

- Add an explicit migration for schema changes; do not rely on runtime schema mutation.
- Define transaction boundaries and rollback behavior.
- Use async only across genuinely asynchronous boundaries and avoid blocking work on the event loop.
- Consider retry, timeout, connection-pool, and idempotency behavior for external I/O.

## Verification

Prefer repository commands. A typical order is targeted unit tests, affected integration tests, type checking, linting, then broader tests proportional to risk. Use dependency overrides or approved fixtures rather than live production services.
