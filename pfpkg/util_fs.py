"""Filesystem helpers."""

from __future__ import annotations

import os
from pathlib import Path

from pfpkg.errors import EXIT_VALIDATION, PfError


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def path_to_repo_relative(repo_root: Path, user_path: str) -> Path:
    repo_root_resolved = repo_root.resolve()
    candidate = Path(user_path)
    if candidate.is_absolute():
        abs_path = candidate.resolve()
        try:
            abs_path.relative_to(repo_root_resolved)
        except ValueError as exc:
            raise PfError("path must be inside repository", EXIT_VALIDATION) from exc
        return abs_path

    abs_path = (repo_root_resolved / candidate).resolve()
    try:
        abs_path.relative_to(repo_root_resolved)
    except ValueError as exc:
        raise PfError("path escapes repository root", EXIT_VALIDATION) from exc
    return abs_path


def list_files_bounded(root: Path, *, limit: int = 5000) -> list[Path]:
    files: list[Path] = []
    for dirpath, _, filenames in os.walk(root):
        for name in sorted(filenames):
            files.append(Path(dirpath) / name)
            if len(files) >= limit:
                return files
    return files
