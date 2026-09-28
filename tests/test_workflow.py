from pathlib import Path

from airs.config import DEFAULT_CONFIG
from airs.models import ModelTier, Provider, RouteDecision, TaskContract
from airs.workflow import Workflow


def test_dry_run_saves_primary_and_cross_model_review(tmp_path: Path) -> None:
    task = TaskContract("t", "T", "Do work", tmp_path)
    route = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    record = Workflow(DEFAULT_CONFIG).run(task, route, dry_run=True)
    assert record["status"] == "completed"
    assert [step["provider"] for step in record["steps"]] == ["codex", "antigravity"]
    assert (tmp_path / ".airs" / "history" / record["run_id"] / "record.json").exists()
