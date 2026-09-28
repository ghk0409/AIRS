---
name: debug
description: Diagnose failures, regressions, flaky behavior, or unexplained runtime results with bounded evidence and testable hypotheses. Use for root-cause investigation; change code only when the request includes a fix.
---

# Debug

Find the earliest supported cause of the observed behavior without turning investigation into a broad repository scan.

## Establish the failure

- Read the router and current state, then capture the exact symptom, expected behavior, affected version or environment, and reproduction conditions.
- Reproduce with the smallest safe case when possible. Preserve the original error, timing, inputs, and relevant environment facts.
- Bound logs by component, time, correlation identifier, and a small window around the failure. Redact sensitive values.

## Investigate

1. Trace the failing path from the observable boundary inward.
2. Separate confirmed facts from hypotheses.
3. Form the smallest falsifiable hypothesis and choose one check that can disprove it.
4. Compare a working and failing path when available.
5. Continue until evidence identifies the earliest incorrect state or violated contract.

Do not make multiple speculative changes at once. Do not treat a later exception as the root cause when an earlier invalid state explains it. Expand to history, infrastructure, another repository, or external systems only when local evidence points there.

## Fix boundary

If the user requested diagnosis only, report cause, evidence, impact, and the smallest credible fix without editing. If a fix is authorized, add a regression test where practical, implement the narrow correction, and verify the original reproduction plus relevant surrounding behavior.

Update `CURRENT.md` with the confirmed cause, verification, unresolved uncertainty, and next action when the investigation remains open.
