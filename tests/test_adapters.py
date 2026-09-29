from pathlib import Path
import sys

from airs.adapters.antigravity import AntigravityAdapter
from airs.adapters.codex import CodexAdapter
from airs.adapters.base import AgentAdapter, AgentResult, subscription_environment
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
    assert command[0] == "agy"
    assert "--print" not in command
    assert command[-1].startswith("--print=review")
    assert command.index("--output-format") < len(command) - 1
    assert command[command.index("--mode") + 1] == "plan"
    assert "--sandbox" in command
    assert command[command.index("--print-timeout") + 1] == "120s"
    assert "Do not run terminal commands" in command[-1]
    assert stdin is None


def test_antigravity_history_redacts_prompt() -> None:
    adapter = AntigravityAdapter({"command": ["agy", "--print"]})
    result = adapter.execute(
        decision(Provider.ANTIGRAVITY), Path("/tmp/project"), "sensitive task", dry_run=True
    )
    assert result.command[-1] == "<task-prompt>"


def test_antigravity_rejects_soft_denied_empty_review(monkeypatch, tmp_path: Path) -> None:
    def fake_execute(self, *args, **kwargs):
        return AgentResult(
            "antigravity", ["agy"], 0,
            '{"status":"SUCCESS","response":"","denied_actions":[{"action":"command"}]}',
            "permission denied", 1.0,
        )

    monkeypatch.setattr(AgentAdapter, "execute", fake_execute)
    result = AntigravityAdapter({}).execute(
        decision(Provider.ANTIGRAVITY), tmp_path, "review", review=True
    )
    assert not result.ok
    assert result.error == "Antigravity denied one or more actions; review is incomplete"


def test_antigravity_extracts_successful_response(monkeypatch, tmp_path: Path) -> None:
    def fake_execute(self, *args, **kwargs):
        return AgentResult(
            "antigravity", ["agy"], 0,
            '{"status":"SUCCESS","response":"No findings.","denied_actions":[]}',
            "", 1.0,
        )

    monkeypatch.setattr(AgentAdapter, "execute", fake_execute)
    result = AntigravityAdapter({}).execute(
        decision(Provider.ANTIGRAVITY), tmp_path, "review", review=True
    )
    assert result.ok
    assert result.response == "No findings."


def test_antigravity_rejects_empty_response_without_denial(monkeypatch, tmp_path: Path) -> None:
    def fake_execute(self, *args, **kwargs):
        return AgentResult("antigravity", ["agy"], 0, '{"status":"SUCCESS","response":" "}', "", 1.0)

    monkeypatch.setattr(AgentAdapter, "execute", fake_execute)
    result = AntigravityAdapter({}).execute(
        decision(Provider.ANTIGRAVITY), tmp_path, "review", review=True
    )
    assert not result.ok
    assert result.error == "Antigravity returned an empty response"


class SlowAdapter(AgentAdapter):
    provider = Provider.CODEX

    def build_command(self, decision, root, prompt, review=False):
        return [
            sys.executable, "-c",
            "import sys,time; time.sleep(0.3); print(sys.stdin.read()); print('warning', file=sys.stderr)",
        ], prompt


def test_agent_progress_preserves_captured_output(tmp_path: Path) -> None:
    updates = []
    adapter = SlowAdapter({"progress_interval_seconds": 0.1})
    result = adapter.execute(
        decision(Provider.CODEX), tmp_path, "hello", progress=updates.append
    )
    assert result.ok
    assert result.stdout.strip() == "hello"
    assert result.stderr.strip() == "warning"
    assert updates[0] == 0
    assert any(elapsed > 0 for elapsed in updates)


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
