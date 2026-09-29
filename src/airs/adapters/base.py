from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import shutil
import subprocess
import tempfile
import time

from ..models import Provider, RouteDecision


@dataclass(slots=True)
class AgentResult:
    provider: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    duration_seconds: float
    dry_run: bool = False
    response: str | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "command": self.command,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_seconds": self.duration_seconds,
            "dry_run": self.dry_run,
            "response": self.response,
            "error": self.error,
            "ok": self.ok,
        }


class AgentAdapter:
    provider: Provider

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def build_command(
        self, decision: RouteDecision, root: Path, prompt: str, review: bool = False
    ) -> tuple[list[str], str | None]:
        raise NotImplementedError

    def execute(
        self,
        decision: RouteDecision,
        root: Path,
        prompt: str,
        review: bool = False,
        dry_run: bool = False,
        progress: Callable[[float], None] | None = None,
    ) -> AgentResult:
        command, stdin = self.build_command(decision, root, prompt, review)
        executable = command[0]
        if not dry_run and shutil.which(executable) is None:
            raise RuntimeError(f"provider CLI is not installed or not on PATH: {executable}")
        if dry_run:
            return AgentResult(self.provider.value, self.history_command(command), 0, "", "", 0.0, True)
        started = time.monotonic()
        interval = max(float(self.config.get("progress_interval_seconds", 10)), 0.1)
        with (
            tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stdout_file,
            tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stderr_file,
            tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as stdin_file,
        ):
            if stdin is not None:
                stdin_file.write(stdin)
                stdin_file.seek(0)
            process = subprocess.Popen(
                command,
                stdin=stdin_file if stdin is not None else subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                cwd=root,
                env=subscription_environment(set(self.config.get("blocked_env", []))),
            )
            try:
                if progress:
                    progress(0.0)
                while True:
                    try:
                        returncode = process.wait(timeout=interval)
                        break
                    except subprocess.TimeoutExpired:
                        if progress:
                            progress(time.monotonic() - started)
            except BaseException:
                if process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                raise
            stdout_file.seek(0)
            stderr_file.seek(0)
            stdout = stdout_file.read()
            stderr = stderr_file.read()
        return AgentResult(
            self.provider.value,
            self.history_command(command),
            returncode,
            stdout,
            stderr,
            time.monotonic() - started,
        )

    def history_command(self, command: list[str]) -> list[str]:
        return command.copy()


def subscription_environment(extra_blocked: set[str] | None = None) -> dict[str, str]:
    """Keep normal CLI state while preventing accidental developer-API authentication."""
    blocked = {
        "OPENAI_API_KEY",
        "CODEX_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "JEV_API_KEY",
    }
    blocked.update(extra_blocked or set())
    return {key: value for key, value in os.environ.items() if key not in blocked}


def adapter_for(provider: Provider, config: dict[str, Any]) -> AgentAdapter:
    provider_config = dict(config["providers"][provider.value])
    provider_config["blocked_env"] = [
        str(config.get("routing", {}).get("jev", {}).get("api_key_env", "JEV_API_KEY"))
    ]
    if provider == Provider.CODEX:
        from .codex import CodexAdapter

        return CodexAdapter(provider_config)
    from .antigravity import AntigravityAdapter

    return AntigravityAdapter(provider_config)
