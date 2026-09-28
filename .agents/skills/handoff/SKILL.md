---
name: handoff
description: Create a compact, recoverable checkpoint for unfinished or transferred work using repository artifacts. Use before changing agent, session, device, or owner, or whenever work must pause safely.
---

# Handoff

Convert transient session context into concise, verified repository state. Do not paste the conversation transcript.

## Gather

Inspect the actual working tree and active artifacts. Confirm what changed, what remains, and the latest verification evidence. Treat prior summaries as claims to verify.

## Rewrite `tasks/CURRENT.md`

Keep it under roughly 1,000 tokens and include:

- updated date and truthful status;
- one-sentence goal and the single current task;
- links to active Spec, Plan, Tasks, and relevant ADR;
- only the source and test paths needed to resume;
- completed and incomplete checklist items;
- decisions and constraints that affect the next action;
- exact checks that passed, failed, or were not run;
- blockers, risks, and unresolved uncertainty;
- one concrete next action.

Remove stale notes and session chronology. Do not store secrets, large logs, speculative conclusions, or details already authoritative elsewhere.

## Check recoverability

A fresh agent should be able to read `AGENTS.md`, `CURRENT.md`, linked artifacts, and the working tree, then identify the next safe action without chat history. Repair broken paths or ambiguous status before completing the handoff.

## Report

State where the checkpoint was written, whether changes are committed or only present in the working tree, verification status, and any action that still requires human authority. Committing or pushing is a separate action and requires the task to authorize it.
