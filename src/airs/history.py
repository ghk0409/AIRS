from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
import json
import os
import re
import shutil
import tempfile
import uuid


def new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


class RunHistory:
    def __init__(self, root: Path, history_dir: str) -> None:
        project_root = root.resolve()
        relative = Path(history_dir)
        self.base = (project_root / relative).resolve()
        if relative.is_absolute() or self.base == project_root or not self.base.is_relative_to(project_root):
            raise ValueError("history_dir must be a subdirectory inside the project root")

    def create(self, task: dict[str, Any], decision: dict[str, Any], kind: str) -> tuple[str, dict[str, Any]]:
        run_id = new_run_id()
        record = {
            "schema_version": 1,
            "run_id": run_id,
            "kind": kind,
            "status": "running",
            "started_at": _now(),
            "finished_at": None,
            "task": task,
            "decision": _without_raw(decision),
            "steps": [],
        }
        self.save(run_id, record)
        return run_id, record

    def save(self, run_id: str, record: dict[str, Any]) -> Path:
        directory = self._directory(run_id)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        target = directory / "record.json"
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=directory, delete=False) as file:
            temporary = Path(file.name)
            os.chmod(temporary, 0o600)
            file.write(json.dumps(record, indent=2, ensure_ascii=False))
        os.replace(temporary, target)
        return target

    def finish(self, run_id: str, record: dict[str, Any], status: str) -> Path:
        record["status"] = status
        record["finished_at"] = _now()
        return self.save(run_id, record)

    def latest(self) -> dict[str, Any] | None:
        if not self.base.exists():
            return None
        records = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in self.base.glob("*/record.json")
            if not path.is_symlink() and not path.parent.is_symlink()
        ]
        if not records:
            return None
        return max(records, key=lambda record: (record.get("started_at", ""), record.get("run_id", "")))

    def load(self, run_id: str) -> dict[str, Any]:
        path = self._directory(run_id) / "record.json"
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"run not found: {run_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def prune(self, older_than_days: int, *, apply: bool = False) -> list[str]:
        if older_than_days < 1:
            raise ValueError("older-than must be at least one day")
        cutoff = datetime.now(UTC) - timedelta(days=older_than_days)
        candidates: list[str] = []
        for record_path in self.base.glob("*/record.json"):
            directory = record_path.parent
            if record_path.is_symlink() or directory.is_symlink() or not re.fullmatch(r"[A-Za-z0-9T_-]+", directory.name):
                continue
            record = json.loads(record_path.read_text(encoding="utf-8"))
            if record.get("status") == "running":
                continue
            started = datetime.fromisoformat(str(record["started_at"]))
            if started < cutoff:
                candidates.append(directory.name)
        if apply:
            for run_id in candidates:
                shutil.rmtree(self._directory(run_id))
        return sorted(candidates)

    def scrub(self, run_id: str, *, apply: bool = False) -> dict[str, Any]:
        record = self.load(run_id)
        if apply:
            decision = record.get("decision", {})
            safe_decision = {
                key: decision.get(key) for key in
                ("provider", "tier", "review", "reviewer", "model", "effort", "source")
                if key in decision
            }
            safe_steps = [
                {
                    key: step[key] for key in
                    ("name", "provider", "returncode", "duration_seconds", "dry_run", "ok")
                    if key in step
                }
                for step in record.get("steps", [])
            ]
            record = {
                key: record.get(key) for key in
                ("schema_version", "run_id", "kind", "status", "started_at", "finished_at")
            } | {"task": {"redacted": True}, "decision": safe_decision, "steps": safe_steps, "redacted": True}
            self.save(run_id, record)
        return record

    def _directory(self, run_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9T_-]+", run_id):
            raise ValueError("invalid run id")
        directory = self.base / run_id
        if directory.is_symlink() or (directory.exists() and not directory.resolve().is_relative_to(self.base)):
            raise ValueError("run directory must remain inside history_dir")
        return directory


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _without_raw(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_raw(item) for key, item in value.items() if key != "raw"}
    if isinstance(value, list):
        return [_without_raw(item) for item in value]
    return value
