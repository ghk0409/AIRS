from __future__ import annotations

from pathlib import Path
import hashlib
import subprocess


def changed_files(root: Path) -> list[str]:
    """List current Git changes, including deletions, without agent exploration."""
    return selected_files(root, sorted(_git_changed_names(root)), allow_empty=True)


def _git_changed_names(root: Path) -> set[str]:
    commands = (
        ["git", "diff", "--name-only", "-z", "--no-ext-diff"],
        ["git", "diff", "--cached", "--name-only", "-z", "--no-ext-diff"],
        ["git", "ls-files", "--others", "--exclude-standard", "--exclude=.airs/", "-z"],
    )
    names: set[str] = set()
    for command in commands:
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError(f"cannot collect changed files: {exc}") from exc
        if result.returncode:
            raise ValueError("review requires a Git working tree or explicit --file paths")
        names.update(part.decode("utf-8", "surrogateescape") for part in result.stdout.split(b"\0") if part)
    return names


def snapshot_changed_files(root: Path) -> dict[str, str]:
    return file_hashes(root, changed_files(root))


def file_hashes(root: Path, files: list[str]) -> dict[str, str]:
    return {
        name: hashlib.sha256(
            (root / name).read_bytes() if (root / name).is_file() else deleted_diff(root, [name]).encode()
        ).hexdigest()
        for name in files
    }


def changed_since(root: Path, before: dict[str, str]) -> list[str]:
    after = file_hashes(root, changed_files(root))
    return [name for name, digest in after.items() if before.get(name) != digest]


def selected_files(root: Path, paths: list[str], *, allow_empty: bool = False) -> list[str]:
    base = root.resolve()
    selected: list[str] = []
    deleted_candidates: set[str] | None = None
    for name in paths:
        path = Path(name)
        resolved = (base / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(base) or resolved.is_dir():
            raise ValueError(f"review path must remain inside the project: {name}")
        relative = resolved.relative_to(base).as_posix()
        if relative.startswith(".airs/"):
            continue
        if not resolved.is_file():
            if deleted_candidates is None:
                deleted_candidates = _git_changed_names(root)
            if relative not in deleted_candidates:
                raise ValueError(f"review path must be a current Git deletion: {name}")
        if relative not in selected:
            selected.append(relative)
    if not selected and not allow_empty:
        raise ValueError("no review files found; use --file or --run-id")
    return selected


def deleted_diff(root: Path, files: list[str], *, max_chars: int = 30000) -> str:
    """Return bounded Git patches for deleted paths, including staged deletions."""
    deleted = [name for name in files if not (root / name).exists()]
    if not deleted:
        return ""
    parts: list[str] = []
    for cached in (False, True):
        command = ["git", "diff", "--no-ext-diff"]
        if cached:
            command.append("--cached")
        command.extend(["--", *deleted])
        try:
            result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=10, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValueError(f"cannot collect deleted-file diff: {exc}") from exc
        if result.returncode:
            raise ValueError("cannot collect deleted-file diff")
        if result.stdout:
            parts.append(result.stdout)
    patch = "\n".join(parts)
    if not patch or "Binary files " in patch or "GIT binary patch" in patch:
        raise ValueError("deleted-file diff is unavailable or binary; review it separately")
    if len(patch) > max_chars:
        raise ValueError(f"deleted-file diff exceeds {max_chars} characters; review smaller changes separately")
    return patch
