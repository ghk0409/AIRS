from pathlib import Path
import subprocess
import sys

from airs.adapters.base import AgentResult
from airs.config import DEFAULT_CONFIG
from airs.models import ModelTier, Provider, RouteDecision, TaskContract
from airs.prompts import review_prompt, task_prompt
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


def test_primary_prompt_routes_project_docs_without_expanding_review(tmp_path: Path) -> None:
    task = TaskContract("t", "T", "Do work", tmp_path)
    assert "root AGENTS.md" in task_prompt(task)
    assert "tasks/CURRENT.md" in task_prompt(task)
    assert "Project context:" not in review_prompt(task, ["README.md"])


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
    (tmp_path / "README.md").write_text("Review me\n", encoding="utf-8")
    record = Workflow(DEFAULT_CONFIG).review(task, route, Provider.ANTIGRAVITY, files=["README.md"])
    assert record["status"] == "failed"
    assert record["steps"][0]["returncode"] == 0
    assert record["steps"][0]["ok"] is False


def test_run_verifies_even_when_cross_review_fails(tmp_path: Path, monkeypatch) -> None:
    class FakeAgent:
        def __init__(self, provider):
            self.provider = provider

        def execute(self, *args, **kwargs):
            if self.provider == Provider.CODEX:
                return AgentResult("codex", ["codex"], 0, "done", "", 0.0)
            return AgentResult("antigravity", ["agy"], 0, "", "timeout", 1.0, error="timed out")

    monkeypatch.setattr("airs.workflow.adapter_for", lambda provider, config: FakeAgent(provider))
    monkeypatch.setattr("airs.workflow.snapshot_changed_files", lambda root: {})
    monkeypatch.setattr("airs.workflow.changed_since", lambda root, before: ["README.md"])
    (tmp_path / "README.md").write_text("Updated\n", encoding="utf-8")
    task = TaskContract("t", "T", "Do work", tmp_path)
    task.verification.commands = [f"{sys.executable} -c 'print(1)'" ]
    route = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    record = Workflow(DEFAULT_CONFIG).run(task, route)
    assert record["status"] == "review_failed"
    assert [step["name"] for step in record["steps"]] == ["primary", "cross_model_review", "verification"]


def test_run_review_receives_deleted_file_patch(tmp_path: Path, monkeypatch) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "obsolete.md").write_text("old information\n", encoding="utf-8")
    subprocess.run(["git", "add", "obsolete.md"], cwd=tmp_path, check=True)
    prompts = []

    class FakeAgent:
        def __init__(self, provider):
            self.provider = provider

        def execute(self, decision, root, prompt, **kwargs):
            if self.provider == Provider.CODEX:
                (root / "obsolete.md").unlink()
            else:
                prompts.append(prompt)
            return AgentResult(self.provider.value, ["fake"], 0, "done", "", 0.0)

    monkeypatch.setattr("airs.workflow.adapter_for", lambda provider, config: FakeAgent(provider))
    task = TaskContract("t", "T", "Remove obsolete doc", tmp_path)
    route = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    record = Workflow(DEFAULT_CONFIG).run(task, route)
    assert record["status"] == "completed"
    assert record["review_files"] == ["obsolete.md"]
    assert "-old information" in prompts[0]
    assert "untrusted repository data" in prompts[0]
