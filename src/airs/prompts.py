from __future__ import annotations

from .models import TaskContract


ROLE_GUIDANCE = {
    "implementer": "Implement the requested change, preserve unrelated work, and verify the result.",
    "planner": "Produce an actionable implementation plan without modifying files.",
    "reviewer": "Review independently. Report concrete findings with severity and file references. Do not edit files.",
    "tester": "Focus on reproducible verification and failures. Make no product changes unless explicitly required.",
    "debugger": "Find and explain the root cause, then apply the smallest safe fix.",
    "security-reviewer": "Look for trust-boundary, secret, injection, authorization, and unsafe execution issues. Do not edit files.",
}


def task_prompt(task: TaskContract, role: str | None = None) -> str:
    selected_role = role or task.role
    guidance = ROLE_GUIDANCE.get(selected_role, ROLE_GUIDANCE["implementer"])
    sections = [
        f"AIRS task {task.id}: {task.title}",
        f"Role: {selected_role}\n{guidance}",
        f"Objective:\n{task.objective}",
    ]
    if task.context:
        sections.append("Context:\n- " + "\n- ".join(task.context))
    if task.constraints:
        sections.append("Constraints:\n- " + "\n- ".join(task.constraints))
    if task.acceptance_criteria:
        sections.append("Acceptance criteria:\n- " + "\n- ".join(task.acceptance_criteria))
    if task.verification.commands or task.verification.criteria:
        verification = task.verification.criteria + [f"Run: {cmd}" for cmd in task.verification.commands]
        sections.append("Verification:\n- " + "\n- ".join(verification))
    sections.append("Return a concise summary of changes, checks, and any remaining risk.")
    return "\n\n".join(sections)


def review_prompt(task: TaskContract) -> str:
    return task_prompt(task, "reviewer") + (
        "\n\nReview the current working tree after the primary agent's work. "
        "Prioritize correctness, regressions, security, and missing tests."
    )
