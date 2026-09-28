# AIRS v0.1 Standard

## Status and language

This document defines AIRS v0.1. The words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** express requirement strength.

## Constitution

1. **Repository is the source of truth.** Durable project facts, decisions, and active state belong in version-controlled artifacts.
2. **Chat history is not project memory.** A session may help produce durable state, but it must not be the only place that state exists.
3. **Context belongs to the narrowest owning scope.** Personal guidance is global; company policy is organizational; relationships are workspace-level; project facts are repository-level.
4. **`AGENTS.md` routes context.** It points to the next relevant source and does not duplicate the whole project.
5. **Context loads progressively.** Begin with the smallest useful set and expand only when evidence, risk, or task scope requires it.
6. **Context has a budget.** Budgets guide discovery and prevent accidental repository-wide loading; correctness and safety still take priority.
7. **Intent precedes large changes.** Medium and larger work uses proportionate Spec, Plan, Tasks, and ADR artifacts.
8. **ADRs record decisions.** They capture context, decision, alternatives, and consequences—not a chronological implementation log.
9. **Every unfinished session is recoverable.** `CURRENT.md` records a truthful checkpoint, verification state, blockers, and next action.
10. **Cross-repository context is on demand.** Another repository is inspected only when an interface, dependency, rollout, or explicit task scope requires it.
11. **Skills contain reusable workflows.** Project facts remain in project documents; repeated operational guidance belongs in skills.
12. **AIRS is agent-agnostic.** Canonical artifacts use open Markdown/YAML and thin adapters instead of depending on one vendor's chat memory.

## Conformance

A repository conforms to AIRS v0.1 when it has:

- a root `AGENTS.md` that identifies the project and routes context;
- a maintained `tasks/CURRENT.md` for active or paused work;
- a documented context-loading order and default exclusions;
- proportionate task artifacts for medium and larger changes;
- an ADR location and ownership rule;
- a recoverable handoff practice;
- no required project knowledge that exists only in chat history.

A workspace conforms when `WORKSPACE.md` and `workspace.yaml` describe repositories and relationships without becoming a duplicate architecture manual.

An organization implementation conforms when it publishes standards and profiles as a source of standard while allowing repositories to own their local truth.

## Precedence

Within compatible instructions, apply the narrowest applicable scope:

```text
explicit user/task instruction
  -> repository
  -> workspace
  -> organization
  -> global
```

Higher-priority platform, safety, legal, and security controls always remain in force. A narrower layer cannot authorize access or weaken a mandatory policy.

## Required maintenance behavior

- Update `CURRENT.md` when the active goal, progress, blocker, validation status, or next step materially changes.
- Archive completed specs after their outcome and durable decisions are recorded.
- Replace stale paths and links promptly.
- Remove instructions that no longer affect decisions.
- Keep secrets and sensitive operational data out of AIRS artifacts.
