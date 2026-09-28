# AIRS Workflow

## 1. Start or resume

Read the repository router and current state. Confirm the goal, constraints, working-tree state, and current verification status. Treat summaries and old plans as pointers; verify important claims against current code and tests.

## 2. Classify the change

| Size | Characteristics | Artifacts |
|---|---|---|
| XS | Local, obvious, low-risk, easily reversible | None |
| S | Small bug or isolated behavior change | `CURRENT.md` |
| M | Contained feature or endpoint | Spec + Tasks |
| L | New module, domain, or multi-step refactor | Spec + Plan + Tasks |
| XL | Architecture, migration, or cross-repository contract | Spec + Plan + Tasks + ADR |

Raise the class for high-risk, irreversible, security-sensitive, data-changing, or highly coordinated work. Lower ceremony only when the repository already contains an equivalent durable artifact.

## 3. Specify

A Spec states the problem, users, scope, requirements, acceptance criteria, constraints, and non-goals. It should not prematurely prescribe every implementation detail.

## 4. Plan

A Plan maps the requirement to affected components, interfaces, data changes, sequencing, validation, rollout, and rollback. Resolve risky unknowns before broad implementation.

## 5. Decompose

Tasks should be small enough to verify and ordered by dependency. Each task names its outcome and validation, not merely a file to edit.

## 6. Implement

Load the relevant implementation skill and source surface. Preserve scope, existing local conventions, and unrelated work. Keep changes coherent and update tests with behavior.

## 7. Verify

Run the narrowest relevant checks first, then broader checks proportional to the change. Record exactly what ran, what passed, what failed, and what was not run. Never report a check as passed without evidence.

## 8. Decide and document

Create an ADR only for a durable decision with meaningful alternatives or consequences. Put repository decisions in the repository, cross-service decisions in the workspace, and rare company-wide architecture decisions in the organization standard.

## 9. Complete or hand off

Before stopping:

- update task checkboxes and verification results;
- rewrite `CURRENT.md` into a concise, truthful checkpoint;
- state blockers and the single best next action;
- capture relevant paths, commands, and decision links;
- archive completed task artifacts when appropriate.

Do not paste the conversation transcript into the repository. Compress the work into durable, actionable state.
