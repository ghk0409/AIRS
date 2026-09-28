from airs.cli import main
from airs.history import RunHistory


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
