from __future__ import annotations

from pathlib import Path
import hashlib
import subprocess


def changed_files(root: Path) -> list[str]:
    """List current Git changes without asking the reviewer to explore the repository."""
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
    existing = [name for name in sorted(names) if (root / name).is_file()]
    return selected_files(root, existing, allow_empty=True)


def snapshot_changed_files(root: Path) -> dict[str, str]:
    return file_hashes(root, changed_files(root))


def file_hashes(root: Path, files: list[str]) -> dict[str, str]:
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in files}


def changed_since(root: Path, before: dict[str, str]) -> list[str]:
    return [
        name for name in changed_files(root)
        if name not in before or hashlib.sha256((root / name).read_bytes()).hexdigest() != before[name]
    ]


def selected_files(root: Path, paths: list[str], *, allow_empty: bool = False) -> list[str]:
    base = root.resolve()
    selected: list[str] = []
    for name in paths:
        path = Path(name)
        resolved = (base / path).resolve()
        if path.is_absolute() or not resolved.is_relative_to(base) or not resolved.is_file():
            raise ValueError(f"review file must be an existing file inside the project: {name}")
        relative = resolved.relative_to(base).as_posix()
        if relative.startswith(".airs/"):
            continue
        if relative not in selected:
            selected.append(relative)
    if not selected and not allow_empty:
        raise ValueError("no review files found; use --file or --run-id")
    return selected
