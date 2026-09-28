from pathlib import Path

from airs.adapters.antigravity import AntigravityAdapter
from airs.adapters.codex import CodexAdapter
from airs.adapters.base import subscription_environment
from airs.models import ModelTier, Provider, RouteDecision


def decision(provider: Provider) -> RouteDecision:
    return RouteDecision(provider, ModelTier.MEDIUM, False, None, "implementer", "test", [], model="test-model", effort="medium")


def test_codex_uses_stdin_and_subscription_cli() -> None:
    command, stdin = CodexAdapter({"command": ["codex", "exec"]}).build_command(
        decision(Provider.CODEX), Path("/tmp/project"), "prompt"
    )
    assert command[:2] == ["codex", "exec"]
    assert "--skip-git-repo-check" in command
    assert command[-1] == "-"
    assert stdin == "prompt"
    assert not any("api" in item.lower() for item in command)


def test_antigravity_review_is_plan_only() -> None:
    command, stdin = AntigravityAdapter({"command": ["agy", "--print"]}).build_command(
        decision(Provider.ANTIGRAVITY), Path("/tmp/project"), "review", review=True
    )
    assert command[:2] == ["agy", "--print"]
    assert command[command.index("--mode") + 1] == "plan"
    assert stdin is None


def test_antigravity_history_redacts_prompt() -> None:
    adapter = AntigravityAdapter({"command": ["agy", "--print"]})
    result = adapter.execute(
        decision(Provider.ANTIGRAVITY), Path("/tmp/project"), "sensitive task", dry_run=True
    )
    assert result.command[-1] == "<task-prompt>"


def test_agent_environment_excludes_developer_api_keys(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-pass")
    monkeypatch.setenv("GEMINI_API_KEY", "do-not-pass")
    monkeypatch.setenv("JEV_API_KEY", "do-not-pass")
    monkeypatch.setenv("MY_JEV_KEY", "do-not-pass")
    env = subscription_environment({"MY_JEV_KEY"})
    assert "OPENAI_API_KEY" not in env
    assert "GEMINI_API_KEY" not in env
    assert "JEV_API_KEY" not in env
    assert "MY_JEV_KEY" not in env
