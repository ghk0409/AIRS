from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse
import json
import os

from dotenv import dotenv_values

from ..models import JevAssessment, TaskContract


class JevError(RuntimeError):
    pass


Transport = Callable[[str, dict[str, str], bytes, float], dict[str, Any]]


def resolve_api_key(env_name: str, project_root: Path) -> str | None:
    """Read only the configured Jev key; never export .env values to agent processes."""
    if key := os.environ.get(env_name):
        return key
    config_home = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    for path in (project_root / ".env", config_home / "airs" / ".env"):
        if path.is_file() and (key := dotenv_values(path, interpolate=False).get(env_name)):
            return key
    return None


def _urlopen_transport(url: str, headers: dict[str, str], body: bytes, timeout: float) -> dict[str, Any]:
    request = Request(url, data=body, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - configured HTTPS endpoint
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise JevError(f"Jev request failed: {exc}") from exc


class JevClient:
    def __init__(self, config: dict[str, Any], transport: Transport | None = None) -> None:
        self.config = config
        self.transport = transport or _urlopen_transport

    def assess(self, task: TaskContract) -> JevAssessment:
        env_name = str(self.config.get("api_key_env", "JEV_API_KEY"))
        api_key = resolve_api_key(env_name, task.project_root)
        if not api_key:
            raise JevError(
                f"Jev API key {env_name} was not found in the environment, "
                "project .env, or user config .env"
            )
        endpoint = str(self.config["endpoint"])
        if urlparse(endpoint).scheme != "https":
            raise JevError("Jev endpoint must use HTTPS")
        payload: dict[str, Any] = {
            "model": str(self.config.get("model") or "jev-latest"),
            "state": {
                "title": task.title,
                "objective": task.objective,
                "role": task.role,
                "context": task.context,
                "constraints": task.constraints,
                "acceptance_criteria": task.acceptance_criteria,
                "risk_hints": task.risk_hints,
            },
            "questions": {
                "task_type": {
                    "type": "choice",
                    "instructions": "Classify the primary software-engineering task type.",
                    "criteria": {
                        "documentation": "Documentation, comments, or formatting only.",
                        "implementation": "Add or change application behavior.",
                        "debugging": "Diagnose or fix faulty behavior.",
                        "testing": "Primarily add or execute verification.",
                        "refactor": "Change structure while preserving behavior.",
                        "migration": "Change data, compatibility, or deployment state.",
                        "security": "Security or trust-boundary work.",
                        "architecture": "Broad system design or cross-repository work.",
                    },
                },
                "complexity": {
                    "type": "choice",
                    "instructions": "Estimate implementation complexity.",
                    "criteria": {
                        "low": "Local, obvious, and easily reversible.",
                        "medium": "Contained multi-step work with ordinary tradeoffs.",
                        "high": "Broad or difficult work with important interactions.",
                        "critical": "System-wide, unusually difficult, or irreversible work.",
                    },
                },
                "risk": {
                    "type": "choice",
                    "instructions": "Estimate correctness, security, and operational risk.",
                    "criteria": {
                        "low": "Small blast radius and easy rollback.",
                        "medium": "Meaningful behavior change with normal verification.",
                        "high": "Security, data, production, or compatibility consequences.",
                        "critical": "Potentially irreversible or severe consequences.",
                    },
                },
                "reasoning_need": {
                    "type": "choice",
                    "instructions": "Estimate the depth of reasoning required.",
                    "criteria": {
                        "low": "Mostly mechanical execution.",
                        "medium": "Several decisions with bounded context.",
                        "high": "Complex reasoning or substantial unknowns.",
                        "critical": "Deep architecture or safety reasoning is essential.",
                    },
                },
                "review_need": {
                    "type": "noul",
                    "instructions": "Should an independent second model review the completed work?",
                },
            },
        }
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        response = self.transport(
            endpoint,
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            encoded,
            float(self.config.get("timeout_seconds", 10)),
        )
        answers = response.get("answers")
        if not isinstance(answers, dict):
            raise JevError("TypeSafe response does not contain answers")
        task_type, c1 = _choice(answers, "task_type")
        complexity, c2 = _choice(answers, "complexity")
        risk, c3 = _choice(answers, "risk")
        reasoning, c4 = _choice(answers, "reasoning_need")
        review_need, c5 = _noul(answers, "review_need")
        confidence = min(c1, c2, c3, c4, c5)
        return JevAssessment(task_type, complexity, risk, reasoning, review_need, confidence, response)


def _answer(answers: dict[str, Any], name: str) -> dict[str, Any]:
    answer = answers.get(name)
    if not isinstance(answer, dict):
        raise JevError(f"Jev answer is missing: {name}")
    return answer


def _choice(answers: dict[str, Any], name: str) -> tuple[str, float]:
    answer = _answer(answers, name)
    choice = answer.get("choice", answer.get("selected", answer.get("value")))
    if not isinstance(choice, str):
        raise JevError(f"Jev choice is invalid: {name}")
    return choice.lower(), float(answer.get("confidence", 0.0))


def _noul(answers: dict[str, Any], name: str) -> tuple[bool, float]:
    answer = _answer(answers, name)
    probability = float(answer.get("noul", answer.get("probability", answer.get("value", 0.5))))
    confidence = float(answer.get("confidence", max(probability, 1.0 - probability)))
    return probability >= 0.5, confidence
