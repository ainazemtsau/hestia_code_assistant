"""Module lifecycle operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from csk_next.domain.models import new_module_record, normalize_module_path
from csk_next.domain.state import ensure_registry, find_module, find_module_by_path, save_registry
from csk_next.eventlog.store import append_event
from csk_next.io.files import ensure_dir, write_json, write_text
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso


def _slugify(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return result or "module"


def _normalize_module_input(layout: Layout, module_path: str) -> str:
    path = Path(module_path).expanduser()
    if path.is_absolute():
        resolved = path.resolve()
        try:
            relative = resolved.relative_to(layout.repo_root)
        except ValueError as exc:
            raise ValueError(
                f"Module path must be inside repository root: {resolved}"
            ) from exc
        return normalize_module_path(relative.as_posix())
    return normalize_module_path(module_path)


def _module_keywords(module_id: str, module_path: str) -> list[str]:
    tokens: set[str] = set()
    for raw in [module_id, module_path.replace("/", "-")]:
        for part in re.split(r"[^a-zA-Z0-9]+", raw.lower()):
            if part:
                tokens.add(part)
    return sorted(tokens)


def _module_record(module_id: str, normalized_path: str) -> dict[str, Any]:
    record = new_module_record(module_id, normalized_path).to_dict()
    record["name"] = module_id
    record["root_path"] = normalized_path
    record["keywords"] = _module_keywords(module_id, normalized_path)
    return record


def _module_view(module: dict[str, Any]) -> dict[str, Any]:
    module_id = str(module["module_id"])
    root_path = str(module.get("root_path", module.get("path", ".")))
    keywords_raw = module.get("keywords")
    if isinstance(keywords_raw, list) and all(isinstance(item, str) for item in keywords_raw):
        keywords = keywords_raw
    else:
        keywords = _module_keywords(module_id, root_path)

    return {
        "module_id": module_id,
        "name": str(module.get("name", module_id)),
        "root_path": root_path,
        "keywords": keywords,
        "path": str(module.get("path", root_path)),
        "initialized": bool(module.get("initialized", False)),
    }


def _unique_module_id(base_id: str, scope_hint: str, used_ids: set[str]) -> str:
    candidate = base_id
    if candidate not in used_ids:
        return candidate

    hinted = f"{base_id}-{_slugify(scope_hint)}"
    if hinted not in used_ids:
        return hinted

    suffix = 2
    while True:
        numbered = f"{hinted}-{suffix}"
        if numbered not in used_ids:
            return numbered
        suffix += 1


def _detected_candidates(layout: Layout) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []
    for root_name in ["packages", "apps", "services"]:
        root = layout.repo_root / root_name
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(entry for entry in root.iterdir() if entry.is_dir()):
            module_path = normalize_module_path(f"{root_name}/{child.name}")
            candidates.append((_slugify(child.name), module_path, root_name))

    if not candidates:
        return [("root", ".", "root")]
    return candidates


def module_add(layout: Layout, module_path: str, module_id: str | None = None) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    normalized = _normalize_module_input(layout, module_path)

    existing = find_module_by_path(registry, normalized)
    if existing is not None:
        return {"status": "ok", "module": existing, "created": False}

    if module_id is None:
        module_id = _slugify(normalized.replace("/", "-"))

    for item in registry["modules"]:
        if item["module_id"] == module_id:
            raise ValueError(f"module_id already exists: {module_id}")

    record = _module_record(module_id, normalized)
    registry["modules"].append(record)
    save_registry(layout.registry, registry)

    append_event(
        layout=layout,
        event_type="module.added",
        actor="engine",
        module_id=module_id,
        payload={"module_id": module_id, "root_path": normalized, "source": "manual"},
        artifact_refs=[str(layout.registry)],
    )

    return {"status": "ok", "module": record, "created": True}


def module_init(layout: Layout, module_id: str, write_scaffold: bool = False) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    module_path = module["path"]
    root = layout.module_root(module_path)

    ensure_dir(root)
    ensure_dir(layout.module_kernel(module_path))
    ensure_dir(layout.module_tasks(module_path))
    ensure_dir(layout.module_run(module_path))

    kernel_path = layout.module_kernel(module_path) / "kernel.json"
    if not kernel_path.exists():
        write_json(
            kernel_path,
            {
                "schema_version": "1.0.0",
                "module_id": module_id,
                "path": module_path,
                "created_at": utc_now_iso(),
            },
        )

    if write_scaffold:
        module_agents = root / "AGENTS.md"
        if not module_agents.exists():
            write_text(
                module_agents,
                f"# AGENTS.md ({module_id})\n\nUse `$csk` from repository root.\n",
            )

        public_api = root / "PUBLIC_API.md"
        if not public_api.exists():
            write_text(
                public_api,
                f"# PUBLIC API ({module_id})\n\nDocument externally visible contracts here.\n",
            )

    module["initialized"] = True
    module["updated_at"] = utc_now_iso()
    save_registry(layout.registry, registry)

    return {
        "status": "ok",
        "module_id": module_id,
        "path": module_path,
        "initialized": True,
        "scaffold_written": write_scaffold,
    }


def module_status(layout: Layout, module_id: str | None = None) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    if module_id is None:
        return {"status": "ok", "modules": registry["modules"]}
    module = find_module(registry, module_id)
    return {
        "status": "ok",
        "module": module,
        "kernel_exists": (layout.module_kernel(module["path"]) / "kernel.json").exists(),
    }


def module_list(layout: Layout) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    return {"status": "ok", "modules": [_module_view(row) for row in registry["modules"]]}


def module_show(layout: Layout, module_id: str) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    view = _module_view(module)
    return {
        "status": "ok",
        "module": view,
        "kernel_exists": (layout.module_kernel(view["path"]) / "kernel.json").exists(),
    }


def registry_detect(layout: Layout) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    used_ids = {str(row["module_id"]) for row in registry["modules"]}

    created: list[dict[str, Any]] = []
    detected: list[dict[str, Any]] = []

    path_to_module = {str(row["path"]): row for row in registry["modules"]}
    for base_id, module_path, scope_hint in _detected_candidates(layout):
        existing = path_to_module.get(module_path)
        if existing is not None:
            detected.append(_module_view(existing))
            continue

        module_id = _unique_module_id(base_id, scope_hint, used_ids)
        used_ids.add(module_id)

        record = _module_record(module_id, module_path)
        registry["modules"].append(record)
        path_to_module[module_path] = record
        created.append(record)
        detected.append(_module_view(record))

    if created:
        save_registry(layout.registry, registry)

    append_event(
        layout=layout,
        event_type="registry.detected",
        actor="engine",
        payload={
            "detected_count": len(detected),
            "created_count": len(created),
            "module_ids": [row["module_id"] for row in detected],
        },
        artifact_refs=[str(layout.registry)],
    )

    for row in created:
        append_event(
            layout=layout,
            event_type="module.added",
            actor="engine",
            module_id=str(row["module_id"]),
            payload={
                "module_id": row["module_id"],
                "root_path": row["path"],
                "source": "registry.detect",
            },
            artifact_refs=[str(layout.registry)],
        )

    return {
        "status": "ok",
        "detected": detected,
        "created": [_module_view(row) for row in created],
        "created_count": len(created),
        "module_count": len(registry["modules"]),
    }
