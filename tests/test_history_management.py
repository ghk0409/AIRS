from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from airs.history import RunHistory


def test_scrub_requires_apply_and_removes_sensitive_text(tmp_path: Path) -> None:
    history = RunHistory(tmp_path, ".airs/history")
    run_id, record = history.create(
        {"id": "t", "project_root": str(tmp_path), "objective": "private text"},
        {"provider": "codex", "rationale": ["private text"]}, "run",
    )
    record["steps"] = [{"name": "primary", "stdout": "private text", "stderr": "private text", "command": ["private text"]}]
    history.finish(run_id, record, "completed")
    history.scrub(run_id)
    assert "private text" in str(history.load(run_id))
    history.scrub(run_id, apply=True)
    assert "private text" not in str(history.load(run_id))
    assert history.load(run_id)["redacted"] is True


def test_prune_previews_before_deleting_one_old_run(tmp_path: Path) -> None:
    history = RunHistory(tmp_path, ".airs/history")
    run_id, record = history.create({"id": "t"}, {}, "run")
    record["started_at"] = (datetime.now(UTC) - timedelta(days=40)).isoformat()
    history.finish(run_id, record, "completed")
    assert history.prune(30) == [run_id]
    assert history.load(run_id)["status"] == "completed"
    assert history.prune(30, apply=True) == [run_id]
    assert history.latest() is None


def test_history_refuses_project_root_as_storage(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="subdirectory"):
        RunHistory(tmp_path, ".")


def test_history_refuses_symlinked_run_directory(tmp_path: Path) -> None:
    history = RunHistory(tmp_path, ".airs/history")
    history.base.mkdir(parents=True)
    (history.base / "run-link").symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(ValueError, match="run directory"):
        history.load("run-link")
