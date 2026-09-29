from pathlib import Path
import sys

from airs.adapters.base import AgentResult
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


def test_run_reports_failed_post_verification(tmp_path: Path, monkeypatch) -> None:
    class SuccessfulAgent:
        def execute(self, *args, **kwargs):
            return AgentResult("codex", ["codex", "exec"], 0, "done", "", 0.0)

    monkeypatch.setattr("airs.workflow.adapter_for", lambda *args: SuccessfulAgent())
    task = TaskContract("t", "T", "Do work", tmp_path)
    task.verification.commands = [f"{sys.executable} -c 'import sys; sys.exit(1)'"]
    route = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, False, None,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )

    record = Workflow(DEFAULT_CONFIG).run(task, route)

    assert record["status"] == "verification_failed"
    assert [step["name"] for step in record["steps"]] == ["primary", "verification"]
    assert record["steps"][-1]["returncode"] == 1


def test_review_reports_soft_denied_agent_as_failed(tmp_path: Path, monkeypatch) -> None:
    class DeniedAgent:
        def execute(self, *args, **kwargs):
            return AgentResult(
                "antigravity", ["agy"], 0, "", "permission denied", 1.0,
                error="Antigravity denied one or more actions; review is incomplete",
            )

    monkeypatch.setattr("airs.workflow.adapter_for", lambda *args: DeniedAgent())
    task = TaskContract("t", "T", "Review work", tmp_path)
    route = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    record = Workflow(DEFAULT_CONFIG).review(task, route, Provider.ANTIGRAVITY)
    assert record["status"] == "failed"
    assert record["steps"][0]["returncode"] == 0
    assert record["steps"][0]["ok"] is False
