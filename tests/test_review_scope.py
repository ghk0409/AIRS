from pathlib import Path
import subprocess

import pytest

from airs.review_scope import changed_files, changed_since, deleted_diff, selected_files, snapshot_changed_files


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


def test_deleted_file_is_detected_and_has_bounded_patch(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    file = tmp_path / "obsolete.md"
    file.write_text("obsolete content\n", encoding="utf-8")
    subprocess.run(["git", "add", "obsolete.md"], cwd=tmp_path, check=True)
    before = snapshot_changed_files(tmp_path)
    file.unlink()
    assert changed_files(tmp_path) == ["obsolete.md"]
    assert changed_since(tmp_path, before) == ["obsolete.md"]
    assert selected_files(tmp_path, ["obsolete.md"]) == ["obsolete.md"]
    assert "-obsolete content" in deleted_diff(tmp_path, ["obsolete.md"])
    with pytest.raises(ValueError, match="exceeds"):
        deleted_diff(tmp_path, ["obsolete.md"], max_chars=10)
    with pytest.raises(ValueError, match="current Git deletion"):
        selected_files(tmp_path, ["missing.md"])
