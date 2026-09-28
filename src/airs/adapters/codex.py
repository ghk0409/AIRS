from __future__ import annotations

from pathlib import Path

from ..models import Provider, RouteDecision
from .base import AgentAdapter


class CodexAdapter(AgentAdapter):
    provider = Provider.CODEX

    def build_command(
        self, decision: RouteDecision, root: Path, prompt: str, review: bool = False
    ) -> tuple[list[str], str | None]:
        command = [str(part) for part in self.config.get("command", ["codex", "exec"])]
        command.extend(
            [
                "--skip-git-repo-check",
                "-C",
                str(root),
                "-s",
                "read-only" if review else "workspace-write",
                "-m",
                str(decision.model),
                "-c",
                f'model_reasoning_effort="{decision.effort}"',
                "-",
            ]
        )
        return command, prompt
