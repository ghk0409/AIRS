from __future__ import annotations

from ..models import JevAssessment, ModelTier, Provider, RouteDecision, TaskContract, max_tier
from .rules import RuleMatch


LEVEL_TO_TIER = {
    "low": ModelTier.LIGHT,
    "medium": ModelTier.MEDIUM,
    "high": ModelTier.HIGH,
    "critical": ModelTier.ULTRA,
}


def decide_from_rule(task: TaskContract, match: RuleMatch, provider: Provider) -> RouteDecision:
    reviewer = _other(provider) if match.review else None
    return RouteDecision(
        provider=provider,
        tier=match.tier,
        review=match.review,
        reviewer=reviewer,
        role=task.role,
        source="rule",
        rationale=[match.reason],
        confidence=1.0,
    )


def decide_from_jev(
    task: TaskContract,
    assessment: JevAssessment,
    provider: Provider,
    confidence_threshold: float,
) -> RouteDecision:
    rationale = [
        f"Jev: type={assessment.task_type}, complexity={assessment.complexity}, "
        f"risk={assessment.risk}, reasoning={assessment.reasoning_need}",
    ]
    if assessment.confidence < confidence_threshold:
        tier = ModelTier.MEDIUM
        review = True
        source = "jev-low-confidence-fallback"
        rationale.append(
            f"confidence {assessment.confidence:.2f} is below threshold {confidence_threshold:.2f}"
        )
    else:
        tier = max_tier(
            LEVEL_TO_TIER.get(assessment.complexity, ModelTier.MEDIUM),
            LEVEL_TO_TIER.get(assessment.reasoning_need, ModelTier.MEDIUM),
        )
        review = assessment.review_need
        source = "jev"
    tier, review, guardrails = apply_minimum_guardrails(
        tier, review, assessment.task_type, assessment.risk
    )
    rationale.extend(guardrails)
    return RouteDecision(
        provider=provider,
        tier=tier,
        review=review,
        reviewer=_other(provider) if review else None,
        role=task.role,
        source=source,
        rationale=rationale,
        confidence=assessment.confidence,
        assessment=assessment,
    )


def conservative_fallback(task: TaskContract, provider: Provider, reason: str) -> RouteDecision:
    return RouteDecision(
        provider=provider,
        tier=ModelTier.MEDIUM,
        review=True,
        reviewer=_other(provider),
        role=task.role,
        source="fallback",
        rationale=[reason, "conservative medium tier with independent review"],
    )


def apply_minimum_guardrails(
    tier: ModelTier, review: bool, task_type: str, risk: str
) -> tuple[ModelTier, bool, list[str]]:
    reasons: list[str] = []
    if risk in {"high", "critical"}:
        minimum = ModelTier.ULTRA if risk == "critical" else ModelTier.HIGH
        new_tier = max_tier(tier, minimum)
        if new_tier != tier:
            reasons.append(f"policy raised tier to {new_tier.value} for {risk} risk")
        tier = new_tier
        if not review:
            reasons.append("policy requires independent review for high/critical risk")
        review = True
    if task_type in {"security", "migration"}:
        new_tier = max_tier(tier, ModelTier.HIGH)
        if new_tier != tier:
            reasons.append(f"policy raised tier to high for {task_type}")
        tier, review = new_tier, True
    if task_type == "architecture":
        if tier != ModelTier.ULTRA:
            reasons.append("policy raised tier to ultra for architecture")
        tier, review = ModelTier.ULTRA, True
    return tier, review, reasons


def _other(provider: Provider) -> Provider:
    return Provider.ANTIGRAVITY if provider == Provider.CODEX else Provider.CODEX
