---
name: test
description: Design, add, repair, or run tests for a defined behavior in an AIRS repository. Use when verification is the primary task, including regression coverage and test strategy for a scoped change.
---

# Test

Create evidence about behavior, not merely additional test code.

## Select the test surface

- Read the repository router, current state, relevant requirement, and the production boundary under test.
- Identify the risk the test must detect and the observable contract it proves.
- Prefer the lowest-cost level that provides confidence: unit for local rules, integration for boundaries, and end-to-end for critical user or system flows.
- Follow existing test organization, fixtures, factories, and repository commands.

## Design

- Cover the requested success path and meaningful failure or boundary cases.
- For a regression, make the test fail for the original defect before relying on the fix when feasible.
- Keep tests deterministic, isolated, readable, and independent of execution order.
- Control time, randomness, concurrency, network, and external services using the repository's approved mechanisms.
- Assert public outcomes and important side effects. Avoid duplicating the implementation in assertions.

Do not weaken an assertion, skip a test, inflate a timeout, or replace realistic behavior with excessive mocking merely to make a suite pass. If the product behavior is ambiguous, surface the missing contract.

## Verify

Run the smallest affected test selection first. Then run adjacent or broader suites proportional to the change. Distinguish product failures, test defects, environment failures, and unavailable checks. Record exact results in `CURRENT.md` when they affect handoff.
