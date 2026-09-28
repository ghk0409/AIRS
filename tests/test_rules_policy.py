from pathlib import Path

from airs.models import JevAssessment, ModelTier, Provider, TaskContract
from airs.routing.policy import decide_from_jev
from airs.routing.rules import match_rule


def task(objective: str, **kwargs: object) -> TaskContract:
    return TaskContract("t1", "Task", objective, Path.cwd(), **kwargs)


def test_simple_rule_skips_jev() -> None:
    match = match_rule(task("Fix a README typo"))
    assert match is not None
    assert match.tier == ModelTier.LIGHT
    assert match.review is False


def test_high_risk_rule_requires_review() -> None:
    match = match_rule(task("Change authentication permissions"))
    assert match is not None
    assert match.tier == ModelTier.HIGH
    assert match.review is True


def test_low_confidence_jev_uses_conservative_fallback() -> None:
    assessment = JevAssessment("implementation", "low", "low", "low", False, 0.60)
    decision = decide_from_jev(task("Add a feature"), assessment, Provider.CODEX, 0.72)
    assert decision.tier == ModelTier.MEDIUM
    assert decision.review is True
    assert decision.source == "jev-low-confidence-fallback"


def test_policy_minimum_beats_jev_for_security() -> None:
    assessment = JevAssessment("security", "low", "low", "low", False, 0.95)
    decision = decide_from_jev(task("Inspect trust boundary"), assessment, Provider.CODEX, 0.72)
    assert decision.tier == ModelTier.HIGH
    assert decision.review is True
