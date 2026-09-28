from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import provider_tier
from ..models import ModelTier, Provider, RouteDecision, TaskContract, max_tier
from .jev import JevClient, JevError
from .policy import conservative_fallback, decide_from_jev, decide_from_rule
from .rules import match_rule


@dataclass(slots=True)
class RouteOverrides:
    provider: Provider | None = None
    tier: ModelTier | None = None
    no_review: bool = False


class HybridRouter:
    def __init__(self, config: dict[str, Any], jev_client: JevClient | None = None) -> None:
        self.config = config
        self.routing = config["routing"]
        self.jev_client = jev_client or JevClient(self.routing["jev"])

    def plan(self, task: TaskContract, overrides: RouteOverrides | None = None) -> RouteDecision:
        overrides = overrides or RouteOverrides()
        provider = overrides.provider or Provider(self.routing.get("default_provider", "codex"))
        rule = match_rule(task)
        if rule:
            decision = decide_from_rule(task, rule, provider)
        elif not self.routing["jev"].get("enabled", True):
            decision = conservative_fallback(task, provider, "Jev is disabled")
        else:
            try:
                assessment = self.jev_client.assess(task)
                decision = decide_from_jev(
                    task,
                    assessment,
                    provider,
                    float(self.routing.get("confidence_threshold", 0.72)),
                )
            except JevError as exc:
                decision = conservative_fallback(task, provider, str(exc))
        self._apply_overrides(decision, overrides)
        mapping = provider_tier(self.config, decision.provider.value, decision.tier.value)
        decision.model, decision.effort = mapping["model"], mapping["effort"]
        return decision

    @staticmethod
    def _apply_overrides(decision: RouteDecision, overrides: RouteOverrides) -> None:
        if overrides.provider:
            decision.provider = overrides.provider
            decision.reviewer = (
                Provider.ANTIGRAVITY if decision.provider == Provider.CODEX else Provider.CODEX
            ) if decision.review else None
            decision.rationale.append(f"provider overridden to {overrides.provider.value}")
        if overrides.tier:
            # Explicit tier may raise resource use, but never weakens a policy minimum.
            selected = max_tier(decision.tier, overrides.tier)
            if selected != overrides.tier:
                decision.rationale.append(
                    f"tier override {overrides.tier.value} was clamped by policy minimum {decision.tier.value}"
                )
            else:
                decision.rationale.append(f"tier overridden to {selected.value}")
            decision.tier = selected
        if overrides.no_review:
            mandatory = decision.tier in {ModelTier.HIGH, ModelTier.ULTRA} and decision.review
            if mandatory:
                decision.rationale.append("--no-review ignored by policy minimum guardrail")
            else:
                decision.review = False
                decision.reviewer = None
                decision.rationale.append("review disabled by override")
