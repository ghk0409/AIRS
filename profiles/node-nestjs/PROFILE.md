# Node.js + NestJS Profile

Use this profile for repositories whose primary application is a TypeScript NestJS service. Repository conventions override these defaults.

## Baseline

- Follow the repository's Node.js version, package manager, module format, linting, and formatting configuration.
- Keep TypeScript strictness enabled; avoid weakening types or using broad casts to bypass errors.
- Keep domain and application behavior independent of NestJS decorators and transport concerns where the architecture supports it.
- Use dependency injection at explicit boundaries and avoid service-locator patterns.

## API and module changes

- Validate and transform untrusted input at the boundary.
- Define stable DTOs and response contracts; review backward compatibility before changing shared shapes.
- Keep controllers thin and place orchestration in application services or use cases.
- Preserve module ownership; avoid exporting providers merely to bypass a boundary.
- Review guards, authorization, tenant isolation, and audit behavior for access changes.

## Data and asynchronous behavior

- Use explicit migrations for schema changes and document rollback or forward-fix strategy.
- Define transaction boundaries across repository calls.
- Make retry, timeout, queue acknowledgement, and idempotency behavior explicit for external operations.
- Handle promises deliberately; do not leave floating work or swallow rejected operations.

## Verification

Prefer repository commands. A typical order is focused unit tests, affected integration or end-to-end tests, TypeScript compilation, linting, then broader tests proportional to risk.
