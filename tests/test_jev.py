from pathlib import Path
import json

from airs.models import TaskContract
from airs.routing.jev import JevClient


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
