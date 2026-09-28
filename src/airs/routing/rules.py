from __future__ import annotations

from dataclasses import dataclass

from ..models import ModelTier, TaskContract


@dataclass(slots=True)
class RuleMatch:
    tier: ModelTier
    review: bool
    task_type: str
    risk: str
    reason: str


SIMPLE_TERMS = {
    "typo", "spelling", "readme", "comment", "formatting", "문구", "오타", "주석", "포맷",
}
HIGH_RISK_TERMS = {
    "authentication", "authorization", "credential", "secret", "payment", "migration",
    "production", "permission", "encryption", "delete", "security", "인증", "권한", "결제",
    "마이그레이션", "운영", "삭제", "보안", "비밀",
}
ULTRA_TERMS = {
    "architecture", "cross-repository", "irreversible", "data loss", "breaking change",
    "아키텍처", "복구 불가", "데이터 손실", "호환성 파괴",
}


def match_rule(task: TaskContract) -> RuleMatch | None:
    text = task.routing_text().lower()
    if any(term in text for term in ULTRA_TERMS):
        return RuleMatch(
            ModelTier.ULTRA, True, "architecture", "critical",
            "deterministic critical/architectural keyword guardrail",
        )
    if any(term in text for term in HIGH_RISK_TERMS):
        return RuleMatch(
            ModelTier.HIGH, True, "high_risk_change", "high",
            "deterministic high-risk keyword guardrail",
        )
    has_simple_term = any(term in text for term in SIMPLE_TERMS)
    structurally_small = (
        len(task.objective) <= 180
        and len(task.context) <= 1
        and len(task.constraints) <= 1
        and not task.risk_hints
    )
    if has_simple_term and structurally_small:
        return RuleMatch(
            ModelTier.LIGHT, False, "simple_change", "low",
            "deterministic low-risk simple-task rule",
        )
    return None
