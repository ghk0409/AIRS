from pathlib import Path
import json
import os

from airs.models import TaskContract
from airs.routing.jev import JevClient, resolve_api_key


def test_jev_parses_typed_answers(monkeypatch) -> None:
    monkeypatch.setenv("JEV_API_KEY", "test-only")
    captured = {}

    def transport(url, headers, body, timeout):
        captured.update(url=url, headers=headers, body=json.loads(body), timeout=timeout)
        return {
            "code": 0,
            "message": "ok",
            "data": {"answers": {
                "task_type": {"choice": "implementation", "confidence": 0.91},
                "complexity": {"choice": "medium", "confidence": 0.90},
                "risk": {"choice": "low", "confidence": 0.89},
                "reasoning_need": {"choice": "medium", "confidence": 0.88},
                "review_need": {"noul": 0.74, "confidence": 0.82}
            }},
        }

    client = JevClient({
        "endpoint": "https://www.jevai.org/api/v1/decisions",
        "api_key_env": "JEV_API_KEY",
        "timeout_seconds": 3,
    }, transport)
    assessment = client.assess(TaskContract("t", "T", "Build it", Path.cwd()))
    assert assessment.complexity == "medium"
    assert assessment.review_need is True
    assert assessment.confidence == 0.82
    assert captured["headers"]["Authorization"] == "Bearer test-only"
    assert "task_type" in captured["body"]["questions"]


def test_jev_key_from_global_dotenv(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    config_home = tmp_path / "config"
    key_file = config_home / "airs" / ".env"
    key_file.parent.mkdir(parents=True)
    key_file.write_text('JEV_API_KEY="global-test-key"\n', encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))

    assert resolve_api_key("JEV_API_KEY", tmp_path / "project") == "global-test-key"
    assert "JEV_API_KEY" not in os.environ

    headers_seen = {}

    def transport(_url, headers, _body, _timeout):
        headers_seen.update(headers)
        return {
            "code": 0,
            "data": {"answers": {
                "task_type": {"choice": "implementation", "confidence": 0.9},
                "complexity": {"choice": "medium", "confidence": 0.9},
                "risk": {"choice": "low", "confidence": 0.9},
                "reasoning_need": {"choice": "medium", "confidence": 0.9},
                "review_need": {"noul": 0.2, "confidence": 0.9},
            }},
        }

    client = JevClient({"endpoint": "https://www.jevai.org/api/v1/decisions"}, transport)
    client.assess(TaskContract("t", "T", "Build it", tmp_path / "project"))
    assert headers_seen["Authorization"] == "Bearer global-test-key"


def test_jev_key_precedence_and_no_interpolation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    config_home = tmp_path / "config"
    key_file = config_home / "airs" / ".env"
    key_file.parent.mkdir(parents=True)
    key_file.write_text("JEV_API_KEY=global-key\n", encoding="utf-8")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(config_home))
    project = tmp_path / "project"
    project.mkdir()
    (project / ".env").write_text('JEV_API_KEY="project-${TOKEN}"\n', encoding="utf-8")

    assert resolve_api_key("JEV_API_KEY", project) == "project-${TOKEN}"
    monkeypatch.setenv("JEV_API_KEY", "environment-key")
    assert resolve_api_key("JEV_API_KEY", project) == "environment-key"


def test_jev_key_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    assert resolve_api_key("JEV_API_KEY", tmp_path / "project") is None
