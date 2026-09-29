from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
import json
from queue import Empty, Queue
import shutil
import subprocess
from threading import Thread
import time

from ..models import Provider, RouteDecision
from .base import AgentAdapter, AgentResult, subscription_environment


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
                "stream-json" if review else "json",
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
        result = (
            self._execute_review_stream(decision, root, prompt, progress)
            if review and not dry_run else
            super().execute(decision, root, prompt, review, dry_run, progress)
        )
        if result.dry_run:
            return result
        if result.error:
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
        if "print timeout" in result.stderr.lower():
            result.error = "Antigravity review timed out before producing a final response"
        elif denied:
            result.error = "Antigravity denied one or more actions; review is incomplete"
        elif payload.get("status") != "SUCCESS":
            result.error = f"Antigravity status: {payload.get('status', 'missing')}"
        elif not result.response or not result.response.strip():
            result.error = "Antigravity returned an empty response"
        return result

    def _execute_review_stream(
        self, decision: RouteDecision, root: Path, prompt: str,
        progress: Callable[..., None] | None,
    ) -> AgentResult:
        command, _ = self.build_command(decision, root, prompt, review=True)
        if shutil.which(command[0]) is None:
            raise RuntimeError(f"provider CLI is not installed or not on PATH: {command[0]}")
        started = time.monotonic()
        timeout = max(1, int(self.config.get("review_timeout_seconds", 120))) + 15
        max_tools = max(1, int(self.config.get("review_max_tool_calls", 20)))
        max_tokens = max(1, int(self.config.get("review_max_input_tokens", 120000)))
        process = subprocess.Popen(
            command, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1,
            env=subscription_environment(set(self.config.get("blocked_env", []))),
        )
        events: Queue[tuple[str, str | None]] = Queue()

        def read_lines(stream, name: str) -> None:
            try:
                for line in stream:
                    events.put((name, line))
            finally:
                events.put((name, None))

        assert process.stdout is not None and process.stderr is not None
        threads = [
            Thread(target=read_lines, args=(process.stdout, "stdout"), daemon=True),
            Thread(target=read_lines, args=(process.stderr, "stderr"), daemon=True),
        ]
        for thread in threads:
            thread.start()
        metrics: dict[str, int] = {"tool_calls": 0, "file_reads": 0, "input_tokens": 0}
        stderr_parts: list[str] = []
        payload: dict | None = None
        error: str | None = None
        done = 0
        interval = max(float(self.config.get("progress_interval_seconds", 10)), 0.1)
        next_progress = started + interval
        if progress:
            progress(0.0, metrics.copy())
        try:
            while done < 2:
                now = time.monotonic()
                if now - started > timeout:
                    error = f"Antigravity review exceeded {timeout}s hard limit"
                    break
                if progress and now >= next_progress:
                    progress(now - started, metrics.copy())
                    next_progress = now + interval
                try:
                    source, line = events.get(timeout=0.2)
                except Empty:
                    continue
                if line is None:
                    done += 1
                    continue
                if source == "stderr":
                    if sum(map(len, stderr_parts)) < 8192:
                        stderr_parts.append(line)
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("event") == "result" and isinstance(event.get("result"), dict):
                    payload = event["result"]
                if event.get("event") != "step_update":
                    continue
                step = event.get("step_update") or {}
                if step.get("state") != "DONE":
                    continue
                if step.get("step_type") == "tool":
                    metrics["tool_calls"] += 1
                    if step.get("tool_name") in {"view_file", "read_file"}:
                        metrics["file_reads"] += 1
                usage = step.get("usage") or {}
                metrics["input_tokens"] += int(usage.get("input_tokens") or 0)
                if metrics["tool_calls"] > max_tools:
                    error = f"Antigravity review exceeded {max_tools} tool calls"
                    break
                if metrics["input_tokens"] > max_tokens:
                    error = f"Antigravity review exceeded {max_tokens} input tokens"
                    break
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for thread in threads:
                thread.join(timeout=1)
        return AgentResult(
            self.provider.value, self.history_command(command), process.returncode,
            json.dumps(payload, ensure_ascii=False) if payload is not None else "",
            "".join(stderr_parts), time.monotonic() - started,
            error=error, metrics=metrics,
        )

    def history_command(self, command: list[str]) -> list[str]:
        sanitized = command.copy()
        if sanitized:
            sanitized[-1] = "<task-prompt>"
        return sanitized
