from __future__ import annotations

from pathlib import Path

from ..models import Provider, RouteDecision
from .base import AgentAdapter


class AntigravityAdapter(AgentAdapter):
    provider = Provider.ANTIGRAVITY

    def build_command(
        self, decision: RouteDecision, root: Path, prompt: str, review: bool = False
    ) -> tuple[list[str], str | None]:
        command = [str(part) for part in self.config.get("command", ["agy", "--print"])]
        command.extend(
            [
                "--output-format",
                "json",
                "--model",
                str(decision.model),
                "--effort",
                str(decision.effort),
                "--mode",
                "plan" if review else "accept-edits",
                prompt,
            ]
        )
        return command, None

    def history_command(self, command: list[str]) -> list[str]:
        sanitized = command.copy()
        if sanitized:
            sanitized[-1] = "<task-prompt>"
        return sanitized
