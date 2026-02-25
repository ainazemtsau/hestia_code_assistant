"""Skills generation from engine + local overlay."""

from __future__ import annotations

import shutil
from pathlib import Path

from csk_next.io.files import ensure_dir
from csk_next.io.files import read_text, write_text


GENERATED_MARKER = "<!-- GENERATED: do not edit by hand -->"


def _iter_relative_files(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(candidate.relative_to(path) for candidate in path.rglob("*") if candidate.is_file())


def _with_marker(content: str, rel: Path) -> str:
    if rel.name.upper() != "SKILL.MD":
        return content
    if content.startswith(GENERATED_MARKER):
        return content
    normalized = content if content.endswith("\n") else content + "\n"
    return f"{GENERATED_MARKER}\n\n{normalized}"


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
        if rel.suffix.lower() == ".md":
            content = read_text(source)
            write_text(destination, _with_marker(content, rel))
        else:
            shutil.copy2(source, destination)


def validate_generated_skills(engine_skills_src: Path, local_override: Path, output_dir: Path) -> dict[str, object]:
    merged: dict[Path, Path] = {}
    for rel in _iter_relative_files(engine_skills_src):
        merged[rel] = engine_skills_src / rel
    for rel in _iter_relative_files(local_override):
        merged[rel] = local_override / rel

    missing: list[str] = []
    modified: list[str] = []
    stale: list[str] = []

    existing = {candidate.relative_to(output_dir) for candidate in output_dir.rglob("*") if candidate.is_file()}
    stale = [str(rel) for rel in sorted(existing - set(merged))]

    for rel, source in sorted(merged.items()):
        dst = output_dir / rel
        if not dst.exists():
            missing.append(str(rel))
            continue
        if rel.suffix.lower() == ".md":
            expected = _with_marker(read_text(source), rel)
            actual = read_text(dst)
            if actual != expected:
                modified.append(str(rel))
        else:
            if dst.read_bytes() != source.read_bytes():
                modified.append(str(rel))

    passed = not missing and not modified and not stale
    return {"status": "ok" if passed else "failed", "missing": missing, "modified": modified, "stale": stale}
