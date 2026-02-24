"""State migration helpers."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from csk_next.io.files import copy_tree, ensure_dir
from csk_next.runtime.paths import Layout


def _resolve_source_root(layout: Layout, source_root: str | None) -> Path:
    if source_root is None:
        return layout.repo_root
    candidate = Path(source_root).expanduser()
    if not candidate.is_absolute():
        candidate = layout.repo_root / candidate
    return candidate.resolve()


def _copy_directory(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    ensure_dir(destination)
    copy_tree(source, destination)
    return True


def _copy_file(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    ensure_dir(destination.parent)
    shutil.copy2(source, destination)
    return True


def migrate_state(layout: Layout, source_root: str | None = None) -> dict[str, Any]:
    source = _resolve_source_root(layout, source_root)
    target = layout.state_root

    if source == target:
        return {
            "status": "ok",
            "migrated": False,
            "source_root": str(source),
            "state_root": str(target),
            "note": "source and destination are identical",
        }

    source_csk = source / ".csk"
    source_agents = source / ".agents"
    source_agents_md = source / "AGENTS.md"

    target_csk = target / ".csk"
    target_agents = target / ".agents"
    target_agents_md = target / "AGENTS.md"

    copied = {
        ".csk": _copy_directory(source_csk, target_csk),
        ".agents": _copy_directory(source_agents, target_agents),
        "AGENTS.md": _copy_file(source_agents_md, target_agents_md),
    }

    return {
        "status": "ok",
        "migrated": any(copied.values()),
        "source_root": str(source),
        "state_root": str(target),
        "copied": copied,
    }

