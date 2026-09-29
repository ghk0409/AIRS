from copy import deepcopy
from pathlib import Path
import json
import subprocess

from airs.config import DEFAULT_CONFIG
from airs.doctor import diagnose


def test_offline_doctor_checks_local_clis_without_probe(tmp_path: Path, monkeypatch) -> None:
    config = deepcopy(DEFAULT_CONFIG)
    config["routing"]["jev"]["enabled"] = False
    monkeypatch.setattr("airs.doctor.shutil.which", lambda name: f"/bin/{name}")
    monkeypatch.setattr("airs.doctor.subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("probe called")))
    report = diagnose(config, tmp_path, offline=True)
    assert report["ok"] is True
    assert [check["name"] for check in report["checks"]] == ["jev_key", "codex_cli", "antigravity_cli"]


def test_doctor_checks_visible_codex_models_and_efforts(tmp_path: Path, monkeypatch) -> None:
    config = deepcopy(DEFAULT_CONFIG)
    config["routing"]["jev"]["enabled"] = False
    monkeypatch.setattr("airs.doctor.shutil.which", lambda name: f"/bin/{name}")
    entries = []
    for mapping in config["providers"]["codex"]["tiers"].values():
        entries.append({
            "slug": mapping["model"], "visibility": "list",
            "supported_reasoning_levels": [{"effort": mapping["effort"]}],
        })

    def fake_run(command, **kwargs):
        if command[1:] == ["debug", "models"]:
            return subprocess.CompletedProcess(command, 0, json.dumps({"models": entries}), "")
        if command[1:] == ["models"]:
            return subprocess.CompletedProcess(command, 0, " ".join(
                mapping["model"] for mapping in config["providers"]["antigravity"]["tiers"].values()
            ), "")
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr("airs.doctor.subprocess.run", fake_run)
    report = diagnose(config, tmp_path)
    assert report["ok"] is True
    assert next(item for item in report["checks"] if item["name"] == "codex_models")["ok"] is True
    entries[-1]["visibility"] = "hidden"
    report = diagnose(config, tmp_path)
    assert report["ok"] is False
    assert "not listed" in next(item for item in report["checks"] if item["name"] == "codex_models")["detail"]
