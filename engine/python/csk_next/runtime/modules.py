"""Module lifecycle operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from csk_next.domain.models import new_module_record
from csk_next.domain.state import ensure_registry, find_module, find_module_by_path, save_registry
from csk_next.io.files import ensure_dir, write_json, write_text
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso


def _slugify(value: str) -> str:
    result = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return result or "module"


def module_add(layout: Layout, module_path: str, module_id: str | None = None) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    normalized = str(Path(module_path).as_posix()).lstrip("./") or "."

    existing = find_module_by_path(registry, normalized)
    if existing is not None:
        return {"status": "ok", "module": existing, "created": False}

    if module_id is None:
        module_id = _slugify(normalized.replace("/", "-"))

    for item in registry["modules"]:
        if item["module_id"] == module_id:
            raise ValueError(f"module_id already exists: {module_id}")

    record = new_module_record(module_id, normalized).to_dict()
    registry["modules"].append(record)
    save_registry(layout.registry, registry)

    return {"status": "ok", "module": record, "created": True}


def module_init(layout: Layout, module_id: str) -> dict[str, Any]:
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
