from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import json
import re
import uuid


def new_run_id() -> str:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{timestamp}-{uuid.uuid4().hex[:8]}"


class RunHistory:
    def __init__(self, root: Path, history_dir: str) -> None:
        self.base = (root / history_dir).resolve()

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
        if not re.fullmatch(r"[A-Za-z0-9T_-]+", run_id):
            raise ValueError("invalid run id")
        directory = self.base / run_id
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / "record.json"
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
        return target

    def finish(self, run_id: str, record: dict[str, Any], status: str) -> Path:
        record["status"] = status
        record["finished_at"] = _now()
        return self.save(run_id, record)

    def latest(self) -> dict[str, Any] | None:
        if not self.base.exists():
            return None
        records = sorted(self.base.glob("*/record.json"), reverse=True)
        if not records:
            return None
        return json.loads(records[0].read_text(encoding="utf-8"))


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _without_raw(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_raw(item) for key, item in value.items() if key != "raw"}
    if isinstance(value, list):
        return [_without_raw(item) for item in value]
    return value
