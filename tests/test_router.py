from pathlib import Path

from airs.config import DEFAULT_CONFIG
from airs.models import JevAssessment, ModelTier, Provider, TaskContract
from airs.routing import HybridRouter, RouteOverrides


class FakeJev:
    def __init__(self, assessment: JevAssessment) -> None:
        self.assessment = assessment

    def assess(self, task: TaskContract) -> JevAssessment:
        return self.assessment


def test_router_maps_jev_signal_to_provider_model() -> None:
    assessment = JevAssessment("implementation", "medium", "low", "high", True, 0.90)
    router = HybridRouter(DEFAULT_CONFIG, FakeJev(assessment))
    decision = router.plan(TaskContract("t", "Feature", "Add profile caching", Path.cwd()))
    assert decision.tier == ModelTier.HIGH
    assert decision.provider == Provider.CODEX
    assert decision.model == "gpt-5.6-sol"
    assert decision.reviewer == Provider.ANTIGRAVITY


def test_policy_guardrail_rejects_lower_tier_and_no_review_overrides() -> None:
    router = HybridRouter(DEFAULT_CONFIG)
    task = TaskContract("t", "Security", "Change authentication permissions", Path.cwd())
    decision = router.plan(
        task,
        RouteOverrides(tier=ModelTier.LIGHT, no_review=True),
    )
    assert decision.tier == ModelTier.HIGH
    assert decision.review is True
    assert any("ignored" in reason for reason in decision.rationale)
