from pathlib import Path
import pytest
import yaml

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
    assert provider_tier(DEFAULT_CONFIG, "codex", "light") == {
        "model": "gpt-5.6-luna", "effort": "low"
    }
    assert provider_tier(DEFAULT_CONFIG, "codex", "medium") == {
        "model": "gpt-5.6-terra", "effort": "medium"
    }
    assert provider_tier(DEFAULT_CONFIG, "codex", "high") == {
        "model": "gpt-5.6-sol", "effort": "high"
    }
    assert provider_tier(DEFAULT_CONFIG, "codex", "ultra") == {
        "model": "gpt-6-astra", "effort": "xhigh"
    }
    for tier, effort in (("light", "low"), ("medium", "medium"), ("high", "high"), ("ultra", "high")):
        assert provider_tier(DEFAULT_CONFIG, "antigravity", tier) == {
            "model": f"gemini-3.8-flash-{effort}", "effort": effort
        }


def test_project_manifest_is_not_mistaken_for_cli_config(tmp_path: Path) -> None:
    manifest = tmp_path / "airs.yaml"
    manifest.write_text('version: "0.1"\nproject: example\npaths: {}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="rename it to airs.project.yaml"):
        load_config(manifest)


def test_project_cli_timeout_override_preserves_default_models(tmp_path: Path) -> None:
    config_file = tmp_path / "airs.yaml"
    config_file.write_text("providers:\n  antigravity:\n    review_timeout_seconds: 900\n", encoding="utf-8")
    loaded = load_config(config_file)
    assert loaded["providers"]["antigravity"]["review_timeout_seconds"] == 900
    assert provider_tier(loaded, "codex", "medium") == provider_tier(DEFAULT_CONFIG, "codex", "medium")


def test_documented_project_override_is_loadable() -> None:
    loaded = load_config(ROOT / "examples" / "project-airs.yaml")
    assert loaded["providers"]["antigravity"]["review_timeout_seconds"] == 900


def test_repository_template_does_not_shadow_cli_configuration() -> None:
    template = ROOT / "templates" / "repository"
    assert not (template / "airs.yaml").exists()
    manifest = yaml.safe_load((template / "airs.project.yaml").read_text(encoding="utf-8"))
    assert "project" in manifest and "providers" not in manifest
