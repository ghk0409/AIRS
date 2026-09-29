from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import json

from ..models import Provider, RouteDecision
from .base import AgentAdapter, AgentResult


class AntigravityAdapter(AgentAdapter):
    provider = Provider.ANTIGRAVITY

    def build_command(
        self, decision: RouteDecision, root: Path, prompt: str, review: bool = False
    ) -> tuple[list[str], str | None]:
        command = [str(part) for part in self.config.get("command", ["agy"])]
        # agy consumes the next argument after --print as its prompt. Attach the
        # prompt with '=' so another flag can never be mistaken for prompt text.
        command = [part for part in command if part not in {"--print", "-p", "--prompt"}]
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
            ]
        )
        if review:
            command.append("--sandbox")
            command.extend(["--print-timeout", f"{int(self.config.get('review_timeout_seconds', 120))}s"])
            prompt += (
                "\n\nFor this read-only review, use workspace file-reading tools to inspect "
                "the relevant files. Do not run terminal commands or request write "
                "permissions. If you cannot inspect the files, say so explicitly "
                "instead of guessing."
            )
        command.append(f"--print={prompt}")
        return command, None

    def execute(
        self,
        decision: RouteDecision,
        root: Path,
        prompt: str,
        review: bool = False,
        dry_run: bool = False,
        progress: Callable[[float], None] | None = None,
    ) -> AgentResult:
        result = super().execute(decision, root, prompt, review, dry_run, progress)
        if result.dry_run:
            return result
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            result.error = "Antigravity did not return valid JSON"
            return result
        if not isinstance(payload, dict):
            result.error = "Antigravity returned an invalid result"
            return result
        response = payload.get("response")
        result.response = response if isinstance(response, str) else None
        denied = payload.get("denied_actions")
        if denied:
            result.error = "Antigravity denied one or more actions; review is incomplete"
        elif payload.get("status") != "SUCCESS":
            result.error = f"Antigravity status: {payload.get('status', 'missing')}"
        elif not result.response or not result.response.strip():
            result.error = "Antigravity returned an empty response"
        return result

    def history_command(self, command: list[str]) -> list[str]:
        sanitized = command.copy()
        if sanitized:
            sanitized[-1] = "<task-prompt>"
        return sanitized
