from pathlib import Path

from airs.config import DEFAULT_CONFIG, load_config, provider_tier


ROOT = Path(__file__).resolve().parents[1]


def test_provider_tiers_match_runnable_and_example_configs() -> None:
    runnable = load_config(ROOT / "airs.yaml")
    example = load_config(ROOT / "airs.example.yaml")
    for provider in ("codex", "antigravity"):
        for tier in ("light", "medium", "high", "ultra"):
            expected = provider_tier(DEFAULT_CONFIG, provider, tier)
            assert provider_tier(runnable, provider, tier) == expected
            assert provider_tier(example, provider, tier) == expected


def test_current_model_mapping() -> None:
    assert provider_tier(DEFAULT_CONFIG, "codex", "medium") == {
        "model": "gpt-6-sol", "effort": "medium"
    }
    assert provider_tier(DEFAULT_CONFIG, "codex", "high") == {
        "model": "gpt-6-sol", "effort": "high"
    }
    for tier, effort in (("light", "low"), ("medium", "medium"), ("high", "high"), ("ultra", "high")):
        assert provider_tier(DEFAULT_CONFIG, "antigravity", tier) == {
            "model": f"gemini-3.8-flash-{effort}", "effort": effort
        }
