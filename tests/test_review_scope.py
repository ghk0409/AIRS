from pathlib import Path
import subprocess

import pytest

from airs.review_scope import changed_files, changed_since, selected_files, snapshot_changed_files


def test_review_scope_detects_only_new_or_modified_work(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / "existing.md").write_text("before\n", encoding="utf-8")
    before = snapshot_changed_files(tmp_path)
    assert list(before) == ["existing.md"]
    (tmp_path / "existing.md").write_text("after\n", encoding="utf-8")
    (tmp_path / "new.md").write_text("new\n", encoding="utf-8")
    assert changed_since(tmp_path, before) == ["existing.md", "new.md"]
    assert changed_files(tmp_path) == ["existing.md", "new.md"]


def test_review_scope_rejects_paths_outside_project(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="inside the project"):
        selected_files(tmp_path, ["../outside.md"])
