from airs.cli import main
from airs.history import RunHistory
from airs.models import ModelTier, Provider, RouteDecision, TaskContract
from airs.review_scope import file_hashes


def test_inline_prompt_runs_and_verifies_in_one_command(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    result = main([
        "run", "-p", "Fix a README typo", "--dry-run",
        "--verify-cmd", "git diff --check",
    ])

    assert result == 0
    record = RunHistory(tmp_path, ".airs/history").latest()
    assert record is not None
    assert record["task"]["project_root"] == str(tmp_path)
    assert record["task"]["metadata"]["source"] == "cli-prompt"
    assert [step["name"] for step in record["steps"]] == ["primary", "verification"]
    assert "(dry run)" in capsys.readouterr().out


def test_prompt_and_task_file_are_mutually_exclusive(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    result = main(["plan", "task.yaml", "-p", "Fix a README typo"])

    assert result == 2
    assert "either a task file or --prompt" in capsys.readouterr().err


def test_inline_prompt_requires_text(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    result = main(["plan", "-p", "  "])

    assert result == 2
    assert "prompt must not be empty" in capsys.readouterr().err


def test_review_of_prior_run_uses_recorded_files_without_jev(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "README.md").write_text("Review this\n", encoding="utf-8")
    task = TaskContract.from_prompt("Improve README", tmp_path)
    decision = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    history = RunHistory(tmp_path, ".airs/history")
    run_id, record = history.create(task.to_dict(), decision.to_dict(), "run")
    record["review_files"] = ["README.md"]
    record["steps"] = [{"name": "primary", "returncode": 0, "ok": True}]
    history.finish(run_id, record, "review_failed")

    def unexpected_plan(*args, **kwargs):
        raise AssertionError("Jev/router must not run for --run-id")

    monkeypatch.setattr("airs.cli.HybridRouter.plan", unexpected_plan)
    assert main(["review", "--run-id", run_id, "--dry-run"]) == 0
    latest = history.latest()
    assert latest is not None
    assert latest["source_run_id"] == run_id
    assert latest["review_files"] == ["README.md"]


def test_review_of_prior_run_rejects_changed_files(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("before\n", encoding="utf-8")
    task = TaskContract.from_prompt("Improve README", tmp_path)
    decision = RouteDecision(
        Provider.CODEX, ModelTier.MEDIUM, True, Provider.ANTIGRAVITY,
        "implementer", "test", [], model="gpt-test", effort="medium",
    )
    history = RunHistory(tmp_path, ".airs/history")
    run_id, record = history.create(task.to_dict(), decision.to_dict(), "run")
    record["review_files"] = ["README.md"]
    record["review_file_hashes"] = file_hashes(tmp_path, ["README.md"])
    record["steps"] = [{"name": "primary", "returncode": 0, "ok": True}]
    history.finish(run_id, record, "completed")
    readme.write_text("after\n", encoding="utf-8")
    assert main(["review", "--run-id", run_id, "--dry-run"]) == 2
    assert "changed since the run" in capsys.readouterr().err
