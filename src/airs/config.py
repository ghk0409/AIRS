from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any
import os

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "version": "0.4.0",
    "history_dir": ".airs/history",
    "history_retention_days": 30,
    "review": {"max_files": 12},
    "routing": {
        "default_provider": "codex",
        "confidence_threshold": 0.72,
        "jev": {
            "enabled": True,
            "endpoint": "https://api.typesafe.ai/v1/systemone",
            "api_key_env": "JEV_API_KEY",
            "timeout_seconds": 10,
            "model": "jev-latest",
        },
    },
    "providers": {
        "codex": {
            "command": ["codex", "exec"],
            "tiers": {
                "light": {"model": "gpt-5.6-luna", "effort": "low"},
                "medium": {"model": "gpt-5.6-terra", "effort": "medium"},
                "high": {"model": "gpt-5.6-sol", "effort": "high"},
                "ultra": {"model": "gpt-6-astra", "effort": "xhigh"},
            },
        },
        "antigravity": {
            "command": ["agy"],
            "review_timeout_seconds": 120,
            "review_max_tool_calls": 20,
            "review_max_input_tokens": 120000,
            "tiers": {
                "light": {"model": "gemini-3.8-flash-low", "effort": "low"},
                "medium": {"model": "gemini-3.8-flash-medium", "effort": "medium"},
                "high": {"model": "gemini-3.8-flash-high", "effort": "high"},
                "ultra": {"model": "gemini-3.8-flash-high", "effort": "high"},
            },
        },
    },
}


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    candidate = Path(path).expanduser() if path else Path(os.environ.get("AIRS_CONFIG", "airs.yaml"))
    if not candidate.exists():
        return deepcopy(DEFAULT_CONFIG)
    loaded = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"configuration must be an object: {candidate}")
    return _merge(DEFAULT_CONFIG, loaded)


def provider_tier(config: dict[str, Any], provider: str, tier: str) -> dict[str, str]:
    try:
        result = config["providers"][provider]["tiers"][tier]
        return {"model": str(result["model"]), "effort": str(result["effort"])}
    except KeyError as exc:
        raise ValueError(f"missing mapping for {provider}/{tier}") from exc
