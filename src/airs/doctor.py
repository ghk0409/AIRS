from __future__ import annotations

from pathlib import Path
from typing import Any
import shutil
import subprocess

from .adapters.base import subscription_environment
from .config import provider_tier
from .models import ModelTier
from .routing.jev import resolve_api_key


def diagnose(config: dict[str, Any], root: Path, *, offline: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    jev = config["routing"]["jev"]
    env_name = str(jev.get("api_key_env", "JEV_API_KEY"))
    enabled = bool(jev.get("enabled", True))
    key_present = bool(resolve_api_key(env_name, root)) if enabled else False
    checks.append({
        "name": "jev_key", "ok": not enabled or key_present,
        "detail": "disabled" if not enabled else "configured" if key_present else f"missing {env_name}",
    })
    for provider in ("codex", "antigravity"):
        command = [str(part) for part in config["providers"][provider]["command"]]
        executable = shutil.which(command[0]) if command else None
        checks.append({"name": f"{provider}_cli", "ok": bool(executable), "detail": executable or "not found"})
        if not executable:
            continue
        models = [provider_tier(config, provider, tier.value)["model"] for tier in ModelTier]
        if offline:
            continue
        probe = [command[0], "login", "status"] if provider == "codex" else [command[0], "models"]
        try:
            result = subprocess.run(
                probe, cwd=root, capture_output=True, text=True, timeout=30,
                env=subscription_environment({env_name}), check=False,
            )
            ok = result.returncode == 0
            checks.append({"name": f"{provider}_login", "ok": ok, "detail": "available" if ok else "check CLI login"})
            if provider == "antigravity" and ok:
                catalog = result.stdout + result.stderr
                missing = sorted(set(models) - {model for model in models if model in catalog})
                checks.append({
                    "name": "antigravity_models", "ok": not missing,
                    "detail": "available" if not missing else "not listed: " + ", ".join(missing),
                })
        except (OSError, subprocess.TimeoutExpired):
            checks.append({"name": f"{provider}_login", "ok": False, "detail": "probe timed out or failed"})
    return {"ok": all(item["ok"] for item in checks), "checks": checks}
