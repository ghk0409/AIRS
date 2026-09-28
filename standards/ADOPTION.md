# Adoption Guide

## Recommended rollout

Adopt AIRS incrementally. The repository layer provides most of the value and should be proven before adding organizational automation.

### Phase 1 — Pilot one repository

- Copy `templates/repository/` into one active repository.
- Fill `AGENTS.md` and `tasks/CURRENT.md` with current, verified facts.
- Select one profile and copy only the skills the team will actually use.
- Run two or three real tasks and note unnecessary reads, missing routes, and stale state.

Success means a new session can resume from repository artifacts without a conversation transcript and without a broad repository scan.

### Phase 2 — Establish the organization source

- Publish this repository or a fork as the source of standard.
- Assign maintainers for standards, profiles, and skills.
- Record releases or commits used by each pilot repository.
- Prefer reviewed copy/sync updates over Git submodules by default.

### Phase 3 — Add workspace context

- Add a workspace only for repositories that form one operating system or product.
- Document repository purposes, contracts, owners, and directional relationships.
- Put cross-repository ADRs at workspace scope.
- Confirm ordinary local tasks do not require workspace loading.

### Phase 4 — Scale and automate

- Add validation for required files, broken links, placeholders, and stale dates.
- Measure context loaded, time to resume, verification quality, and artifact maintenance cost.
- Add profiles only for repeated differences that affect decisions.
- Remove process that creates more maintenance than value.

## Repository adoption checklist

- [ ] Root `AGENTS.md` is under the target budget and routes to current sources.
- [ ] `tasks/CURRENT.md` reflects the actual active state.
- [ ] One profile is selected or explicitly marked unnecessary.
- [ ] Task size policy is understood and proportionate.
- [ ] ADR ownership is defined.
- [ ] Generated, large, sensitive, and irrelevant paths are excluded by default.
- [ ] Relevant skills are installed under `.agents/skills/`.
- [ ] Agent-specific adapters point to canonical artifacts.
- [ ] A fresh session can find, change, verify, and hand off a small task.

## Update strategy

Record the adopted AIRS release or commit in repository configuration. When updating:

1. compare standards and templates with local customizations;
2. review behavior-changing differences;
3. merge deliberately rather than overwriting local truth;
4. validate paths and handoff behavior;
5. record the new version.

## What not to centralize

Do not move project architecture, active tasks, local commands, repository-specific exceptions, or service credentials into the organization standard. Do not copy every organization skill into every repository. Centralize reusable policy; keep changing project truth local.

## Suggested measures

- percentage of sessions that resume using only `AGENTS.md` and `CURRENT.md`;
- number of files loaded before the first useful action;
- frequency of repository-wide or cross-repository scans;
- stale or incorrect handoffs;
- verification failures caused by missing context;
- maintenance time for AIRS artifacts.
