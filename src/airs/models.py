from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any
import json

import yaml


class ContractError(ValueError):
    pass


class ModelTier(StrEnum):
    LIGHT = "light"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


class Provider(StrEnum):
    CODEX = "codex"
    ANTIGRAVITY = "antigravity"


ALLOWED_ROLES = {
    "implementer", "planner", "reviewer", "tester", "debugger", "security-reviewer",
}
ALLOWED_CONTRACT_FIELDS = {
    "id", "title", "objective", "project_root", "role", "context", "constraints",
    "acceptance_criteria", "verification", "risk_hints", "metadata",
}


TIER_ORDER = {
    ModelTier.LIGHT: 0,
    ModelTier.MEDIUM: 1,
    ModelTier.HIGH: 2,
    ModelTier.ULTRA: 3,
}


@dataclass(slots=True)
class VerificationSpec:
    commands: list[str] = field(default_factory=list)
    criteria: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TaskContract:
    id: str
    title: str
    objective: str
    project_root: Path
    role: str = "implementer"
    context: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    verification: VerificationSpec = field(default_factory=VerificationSpec)
    risk_hints: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source: Path | None = None) -> "TaskContract":
        required = ("id", "title", "objective", "project_root")
        missing = [name for name in required if not data.get(name)]
        if missing:
            raise ContractError(f"missing required field(s): {', '.join(missing)}")
        unknown = sorted(set(data) - ALLOWED_CONTRACT_FIELDS)
        if unknown:
            raise ContractError(f"unknown field(s): {', '.join(unknown)}")
        role = str(data.get("role", "implementer"))
        if role not in ALLOWED_ROLES:
            raise ContractError(f"unsupported role: {role}")
        root = Path(str(data["project_root"])).expanduser()
        if not root.is_absolute() and source:
            root = (source.parent / root).resolve()
        verification = data.get("verification") or {}
        if not isinstance(verification, dict):
            raise ContractError("verification must be an object")
        list_fields = ("context", "constraints", "acceptance_criteria", "risk_hints")
        for name in list_fields:
            if not isinstance(data.get(name, []), list):
                raise ContractError(f"{name} must be a list")
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            objective=str(data["objective"]),
            project_root=root.resolve(),
            role=role,
            context=[str(item) for item in data.get("context", [])],
            constraints=[str(item) for item in data.get("constraints", [])],
            acceptance_criteria=[str(item) for item in data.get("acceptance_criteria", [])],
            verification=VerificationSpec(
                commands=[str(item) for item in verification.get("commands", [])],
                criteria=[str(item) for item in verification.get("criteria", [])],
            ),
            risk_hints=[str(item) for item in data.get("risk_hints", [])],
            metadata=dict(data.get("metadata", {})),
        )

    @classmethod
    def load(cls, path: str | Path) -> "TaskContract":
        source = Path(path).resolve()
        try:
            raw = source.read_text(encoding="utf-8")
            data = json.loads(raw) if source.suffix.lower() == ".json" else yaml.safe_load(raw)
        except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
            raise ContractError(f"cannot load task contract: {exc}") from exc
        if not isinstance(data, dict):
            raise ContractError("task contract must be an object")
        return cls.from_mapping(data, source)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["project_root"] = str(self.project_root)
        return data

    def routing_text(self) -> str:
        parts = [self.title, self.objective, self.role]
        parts.extend(self.context)
        parts.extend(self.constraints)
        parts.extend(self.risk_hints)
        return "\n".join(parts)


@dataclass(slots=True)
class JevAssessment:
    task_type: str
    complexity: str
    risk: str
    reasoning_need: str
    review_need: bool
    confidence: float
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


@dataclass(slots=True)
class RouteDecision:
    provider: Provider
    tier: ModelTier
    review: bool
    reviewer: Provider | None
    role: str
    source: str
    rationale: list[str]
    confidence: float | None = None
    assessment: JevAssessment | None = None
    model: str | None = None
    effort: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["provider"] = self.provider.value
        result["tier"] = self.tier.value
        result["reviewer"] = self.reviewer.value if self.reviewer else None
        return result


def max_tier(left: ModelTier, right: ModelTier) -> ModelTier:
    return left if TIER_ORDER[left] >= TIER_ORDER[right] else right
