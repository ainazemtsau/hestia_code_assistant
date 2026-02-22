"""Directory snapshot helpers for scope gate."""

from __future__ import annotations

from pathlib import Path

from csk_next.io.hashing import sha256_file


def take_snapshot(root: Path, ignore_prefixes: tuple[str, ...] = (".csk/run",)) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    if not root.exists():
        return snapshot
    for file_path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        rel = file_path.relative_to(root).as_posix()
        if any(rel.startswith(prefix) for prefix in ignore_prefixes):
            continue
        snapshot[rel] = sha256_file(file_path)
    return snapshot


def changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    changed: set[str] = set()
    for path, old_hash in before.items():
        if path not in after:
            changed.add(path)
        elif after[path] != old_hash:
            changed.add(path)
    for path in after:
        if path not in before:
            changed.add(path)
    return sorted(changed)
