"""Skills generation from engine + local overlay."""

from __future__ import annotations

import shutil
from pathlib import Path

from csk_next.io.files import ensure_dir


def _iter_relative_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(candidate.relative_to(path) for candidate in path.rglob("*") if candidate.is_file())


def generate_skills(engine_skills_src: Path, local_override: Path, output_dir: Path) -> None:
    """Merge skills from engine and local override into output directory."""
    ensure_dir(output_dir)

    merged: dict[Path, Path] = {}
    for rel in _iter_relative_files(engine_skills_src):
        merged[rel] = engine_skills_src / rel
    for rel in _iter_relative_files(local_override):
        merged[rel] = local_override / rel

    existing = {candidate.relative_to(output_dir) for candidate in output_dir.rglob("*") if candidate.is_file()}
    stale = existing - set(merged)
    for rel in sorted(stale):
        (output_dir / rel).unlink(missing_ok=True)

    for rel, source in sorted(merged.items()):
        destination = output_dir / rel
        ensure_dir(destination.parent)
        shutil.copy2(source, destination)
