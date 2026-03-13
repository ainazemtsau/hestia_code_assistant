from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


BEGIN_MARKER = "<!-- CSK:BEGIN ROOT BOOTSTRAP -->"
END_MARKER = "<!-- CSK:END ROOT BOOTSTRAP -->"


def _replace_managed_block(existing_text: str, block_text: str) -> str:
    start = existing_text.find(BEGIN_MARKER)
    end = existing_text.find(END_MARKER)

    if start == -1 or end == -1:
        stripped = existing_text.rstrip()
        if not stripped:
            return block_text.strip() + "\n"
        return stripped + "\n\n" + block_text.strip() + "\n"

    end += len(END_MARKER)
    before = existing_text[:start].rstrip()
    after = existing_text[end:].lstrip()

    parts = []
    if before:
        parts.append(before)
    parts.append(block_text.strip())
    if after:
        parts.append(after)
    return "\n\n".join(parts) + "\n"


def ensure_root_agents_block(path: Path, block_text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""

    action = "created"
    if BEGIN_MARKER in existing and END_MARKER in existing:
        action = "updated"
    elif existing.strip():
        action = "merged"

    updated = _replace_managed_block(existing, block_text)
    path.write_text(updated, encoding="utf-8")
    return action


def strip_root_agents_block(path: Path) -> str:
    if not path.exists():
        return "skipped"

    existing = path.read_text(encoding="utf-8")
    start = existing.find(BEGIN_MARKER)
    end = existing.find(END_MARKER)
    if start == -1 or end == -1:
        return "skipped"

    end += len(END_MARKER)
    before = existing[:start].rstrip()
    after = existing[end:].lstrip()
    parts = []
    if before:
        parts.append(before)
    if after:
        parts.append(after)

    if parts:
        path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    else:
        path.unlink()
    return "removed"


def safe_rel_path(path_value: str) -> Path:
    rel = Path(path_value)
    if rel.anchor or rel.is_absolute():
        raise ValueError(f"Manifest path must be relative: {path_value}")
    if not rel.parts or str(rel) == ".":
        raise ValueError(f"Manifest path must not point at the root itself: {path_value}")
    if ".." in rel.parts:
        raise ValueError(f"Manifest path must stay inside the root: {path_value}")
    return rel


def resolve_workflow_root(workflow_root: Path) -> Path:
    if not workflow_root.exists():
        raise ValueError("workflow_root must exist")
    if not workflow_root.is_dir():
        raise ValueError("workflow_root must be a directory")
    return workflow_root.resolve(strict=True)


def resolve_manifest_path(workflow_root: Path, manifest_path: Path | None = None) -> Path:
    if manifest_path is None:
        candidate = workflow_root / "install" / "manifest" / "client_base_manifest.json"
    else:
        candidate = manifest_path if manifest_path.is_absolute() else workflow_root / manifest_path

    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise ValueError(f"manifest does not exist: {candidate}") from exc

    try:
        resolved.relative_to(workflow_root)
    except ValueError as exc:
        raise ValueError("manifest must live inside workflow_root") from exc
    return resolved


def load_install_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _remove_target(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()


def _cleanup_paths(manifest: dict[str, Any]) -> list[Path]:
    raw_paths = manifest.get("managed_cleanup_paths", [])
    if not isinstance(raw_paths, list):
        raise ValueError("managed_cleanup_paths must be a list")

    seen: set[str] = set()
    paths: list[Path] = []
    for raw in raw_paths:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("managed_cleanup_paths entries must be non-empty strings")
        rel = safe_rel_path(raw)
        key = str(rel).replace("\\", "/")
        if key in seen:
            continue
        seen.add(key)
        paths.append(rel)
    paths.sort(key=lambda rel: (len(rel.parts), str(rel).replace("\\", "/")))
    return paths


def _bridge_cleanup_paths(manifest: dict[str, Any]) -> list[Path]:
    raw_paths = manifest.get("bridge_cleanup_targets", [])
    if not isinstance(raw_paths, list):
        raise ValueError("bridge_cleanup_targets must be a list")

    seen: set[str] = set()
    paths: list[Path] = []
    for raw in raw_paths:
        if not isinstance(raw, str) or not raw.strip():
            raise ValueError("bridge_cleanup_targets entries must be non-empty strings")
        rel = safe_rel_path(raw)
        key = str(rel).replace("\\", "/")
        if key in seen:
            continue
        seen.add(key)
        paths.append(rel)
    paths.sort(key=lambda rel: (len(rel.parts), str(rel).replace("\\", "/")))
    return paths


def _planned_assets(source_root: Path, target_root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    raw_assets = manifest.get("assets", [])
    if not isinstance(raw_assets, list):
        raise ValueError("assets must be a list")

    planned: list[dict[str, Any]] = []
    seen_targets: set[str] = set()
    for asset in raw_assets:
        if not isinstance(asset, dict):
            raise ValueError("each asset must be an object")

        source_raw = asset.get("source")
        target_raw = asset.get("target")
        ownership = asset.get("ownership")
        if not isinstance(source_raw, str) or not source_raw.strip():
            raise ValueError("asset source must be a non-empty string")
        if not isinstance(target_raw, str) or not target_raw.strip():
            raise ValueError("asset target must be a non-empty string")
        if ownership not in {"managed", "bridge", "project-owned-template"}:
            raise ValueError(f"unsupported asset ownership: {ownership}")

        source_rel = safe_rel_path(source_raw)
        target_rel = safe_rel_path(target_raw)
        target_key = str(target_rel).replace("\\", "/")
        if target_key in seen_targets:
            raise ValueError(f"duplicate asset target: {target_key}")
        seen_targets.add(target_key)
        source = source_root / source_rel
        target = target_root / target_rel
        if not source.exists():
            raise FileNotFoundError(source)

        planned.append(
            {
                "source_rel": source_rel,
                "target_rel": target_rel,
                "source": source,
                "target": target,
                "ownership": ownership,
                "target_existed": target.exists(),
            }
        )
    return planned


def copy_manifest_asset(planned_asset: dict[str, Any]) -> str:
    source = planned_asset["source"]
    target = planned_asset["target"]
    ownership = planned_asset["ownership"]

    if ownership == "bridge":
        block_text = source.read_text(encoding="utf-8")
        return ensure_root_agents_block(target, block_text)

    if ownership == "project-owned-template" and target.exists():
        return "skipped"

    existed = planned_asset["target_existed"]

    target.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        shutil.copy2(source, target)

    return "updated" if existed else "created"


def apply_manifest(source_root: Path, target_root: Path, manifest: dict[str, Any]) -> list[dict[str, str]]:
    cleanup_paths = _cleanup_paths(manifest)
    bridge_cleanup_paths = _bridge_cleanup_paths(manifest)
    planned_assets = _planned_assets(source_root, target_root, manifest)

    results: list[dict[str, str]] = []
    for rel in cleanup_paths:
        target = target_root / rel
        if not target.exists():
            continue
        _remove_target(target)
        results.append(
            {
                "target": str(rel).replace("\\", "/"),
                "ownership": "managed",
                "action": "removed",
            }
        )

    current_bridge_targets = {
        str(asset["target_rel"]).replace("\\", "/")
        for asset in planned_assets
        if asset["ownership"] == "bridge"
    }
    for rel in bridge_cleanup_paths:
        rel_key = str(rel).replace("\\", "/")
        if rel_key in current_bridge_targets:
            continue
        action = strip_root_agents_block(target_root / rel)
        if action != "skipped":
            results.append(
                {
                    "target": rel_key,
                    "ownership": "bridge",
                    "action": action,
                }
            )

    for asset in planned_assets:
        action = copy_manifest_asset(asset)
        results.append(
            {
                "target": str(asset["target_rel"]).replace("\\", "/"),
                "ownership": asset["ownership"],
                "action": action,
            }
        )
    return results
