from copy import deepcopy
from pathlib import Path

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
