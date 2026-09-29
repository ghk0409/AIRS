from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
import shlex
import subprocess
import time

from .adapters import adapter_for
from .config import provider_tier
from .history import RunHistory
from .models import Provider, RouteDecision, TaskContract
from .prompts import review_prompt, task_prompt
from .review_scope import changed_files, changed_since, deleted_diff, file_hashes, selected_files, snapshot_changed_files


class Workflow:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def run(
        self,
        task: TaskContract,
        decision: RouteDecision,
        dry_run: bool = False,
        progress: Callable[..., None] | None = None,
    ) -> dict[str, Any]:
        history = RunHistory(task.project_root, str(self.config["history_dir"]))
        run_id, record = history.create(task.to_dict(), decision.to_dict(), "run")
        try:
            before = None
            if not dry_run:
                try:
                    before = snapshot_changed_files(task.project_root)
                except ValueError:
                    pass
            primary = adapter_for(decision.provider, self.config).execute(
                decision, task.project_root, task_prompt(task), dry_run=dry_run,
                progress=(lambda elapsed: progress("primary", elapsed)) if progress else None,
            )
            record["steps"].append({"name": "primary", **primary.to_dict()})
            if not primary.ok:
                history.finish(run_id, record, "failed")
                return record
            if dry_run:
                review_files = ["<changed files from primary run>"]
            else:
                try:
                    review_files = changed_since(task.project_root, before) if before is not None else changed_files(task.project_root)
                except ValueError as exc:
                    review_files = []
                    record["review_error"] = str(exc)
            record["review_files"] = review_files
            if not dry_run:
                try:
                    record["review_file_hashes"] = file_hashes(task.project_root, review_files)
                except ValueError as exc:
                    record["review_error"] = str(exc)
            if decision.review and decision.reviewer:
                if record.get("review_error") or not review_files or len(review_files) > self._max_review_files():
                    record["review_error"] = record.get("review_error") or (
                        "no changed files to review" if not review_files else
                        f"{len(review_files)} changed files exceed review limit {self._max_review_files()}"
                    )
                    status = "review_failed"
                else:
                    reviewer_decision = self._reviewer_decision(decision)
                    try:
                        patch = "" if dry_run else deleted_diff(task.project_root, review_files)
                        review = adapter_for(decision.reviewer, self.config).execute(
                            reviewer_decision, task.project_root, review_prompt(task, review_files, patch),
                            review=True, dry_run=dry_run,
                            progress=(lambda elapsed, metrics=None: progress("cross_model_review", elapsed, metrics)) if progress else None,
                        )
                        record["steps"].append({"name": "cross_model_review", **review.to_dict()})
                        status = "completed" if review.ok else "review_failed"
                    except ValueError as exc:
                        record["review_error"] = str(exc)
                        status = "review_failed"
            else:
                status = "completed"
            if task.verification.commands:
                steps, checks_ok = self._verification_steps(task, dry_run)
                record["steps"].extend(steps)
                if not checks_ok:
                    status = "review_and_verification_failed" if status == "review_failed" else "verification_failed"
            history.finish(run_id, record, status)
            return record
        except Exception as exc:
            record["error"] = str(exc)
            history.finish(run_id, record, "failed")
            raise

    def review(
        self,
        task: TaskContract,
        decision: RouteDecision,
        provider: Provider | None,
        dry_run: bool = False,
        progress: Callable[..., None] | None = None,
        files: list[str] | None = None,
        source_run_id: str | None = None,
    ) -> dict[str, Any]:
        reviewer = provider or (
            Provider.ANTIGRAVITY if decision.provider == Provider.CODEX else Provider.CODEX
        )
        review_decision = self._reviewer_decision(decision, reviewer)
        history = RunHistory(task.project_root, str(self.config["history_dir"]))
        run_id, record = history.create(task.to_dict(), review_decision.to_dict(), "review")
        try:
            review_files = selected_files(task.project_root, files) if files is not None else changed_files(task.project_root)
            if not review_files:
                raise ValueError("no changed files to review; use --file")
            if len(review_files) > self._max_review_files():
                raise ValueError(f"{len(review_files)} changed files exceed review limit {self._max_review_files()}; use --file")
            record["review_files"] = review_files
            if source_run_id:
                record["source_run_id"] = source_run_id
            result = adapter_for(reviewer, self.config).execute(
                review_decision, task.project_root,
                review_prompt(task, review_files, "" if dry_run else deleted_diff(task.project_root, review_files)),
                review=True, dry_run=dry_run,
                progress=(lambda elapsed, metrics=None: progress("review", elapsed, metrics)) if progress else None,
            )
            record["steps"].append({"name": "review", **result.to_dict()})
            history.finish(run_id, record, "completed" if result.ok else "failed")
            return record
        except Exception as exc:
            record["error"] = str(exc)
            history.finish(run_id, record, "failed")
            raise

    def _max_review_files(self) -> int:
        return max(1, int(self.config.get("review", {}).get("max_files", 12)))

    def verify(self, task: TaskContract, dry_run: bool = False) -> dict[str, Any]:
        history = RunHistory(task.project_root, str(self.config["history_dir"]))
        run_id, record = history.create(task.to_dict(), {}, "verify")
        try:
            steps, all_ok = self._verification_steps(task, dry_run)
            record["steps"].extend(steps)
            history.finish(run_id, record, "completed" if all_ok else "failed")
            return record
        except Exception as exc:
            record["error"] = str(exc)
            history.finish(run_id, record, "failed")
            raise

    @staticmethod
    def _verification_steps(
        task: TaskContract, dry_run: bool
    ) -> tuple[list[dict[str, Any]], bool]:
        steps: list[dict[str, Any]] = []
        for command_text in task.verification.commands:
            command = shlex.split(command_text)
            if not command:
                continue
            if dry_run:
                step: dict[str, Any] = {
                    "command": command, "returncode": 0,
                    "stdout": "", "stderr": "", "dry_run": True,
                }
            else:
                started = time.monotonic()
                completed = subprocess.run(
                    command,
                    cwd=task.project_root,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                step = {
                    "command": command,
                    "returncode": completed.returncode,
                    "stdout": completed.stdout,
                    "stderr": completed.stderr,
                    "duration_seconds": time.monotonic() - started,
                }
            step["name"] = "verification"
            steps.append(step)
            if step["returncode"] != 0:
                return steps, False
        return steps, True

    def _reviewer_decision(
        self, primary: RouteDecision, provider: Provider | None = None
    ) -> RouteDecision:
        reviewer = provider or primary.reviewer
        assert reviewer is not None
        mapping = provider_tier(self.config, reviewer.value, primary.tier.value)
        return RouteDecision(
            provider=reviewer,
            tier=primary.tier,
            review=False,
            reviewer=None,
            role="reviewer",
            source="cross-model-review",
            rationale=[f"independent review of {primary.provider.value} output"],
            model=mapping["model"],
            effort=mapping["effort"],
        )
