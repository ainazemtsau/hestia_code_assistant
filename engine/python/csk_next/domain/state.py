"""State loading and saving utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from csk_next.domain.models import Registry, new_registry
from csk_next.domain.schemas import SchemaValidationError, validate_schema
from csk_next.io.files import ensure_dir, read_json, write_json
from csk_next.runtime.time import utc_now_iso


def _upgrade_registry(registry: dict[str, Any]) -> bool:
    changed = False
    modules = registry.get("modules")
    if not isinstance(modules, list):
        return changed

    for module in modules:
        if not isinstance(module, dict):
            continue
        if "registered" not in module:
            module["registered"] = True
            changed = True
    return changed


def load_json_validated(path: Path, schema_name: str | None = None) -> dict[str, Any]:
    data = read_json(path)
    if schema_name is not None:
        validate_schema(schema_name, data)
    return data


def save_json_validated(path: Path, data: dict[str, Any], schema_name: str | None = None) -> None:
    if schema_name is not None:
        validate_schema(schema_name, data)
    write_json(path, data)


def ensure_registry(path: Path) -> dict[str, Any]:
    if path.exists():
        registry = read_json(path)
        if _upgrade_registry(registry):
            save_json_validated(path, registry, "registry")
            return registry
        validate_schema("registry", registry)
        return registry
    ensure_dir(path.parent)
    registry = new_registry().to_dict()
    save_json_validated(path, registry, "registry")
    return registry


def save_registry(path: Path, registry: dict[str, Any]) -> None:
    registry["updated_at"] = utc_now_iso()
    save_json_validated(path, registry, "registry")


def find_module(registry: dict[str, Any], module_id: str) -> dict[str, Any]:
    for module in registry["modules"]:
        if module["module_id"] == module_id:
            return module
    raise KeyError(f"Module not found: {module_id}")


def find_module_by_path(registry: dict[str, Any], module_path: str) -> dict[str, Any] | None:
    for module in registry["modules"]:
        if module["path"] == module_path:
            return module
    return None


def require_file(path: Path, description: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Missing {description}: {path}")


def load_profile(path: Path) -> dict[str, Any]:
    profile = load_json_validated(path, "profile")
    if not isinstance(profile["required_gates"], list):
        raise SchemaValidationError("Profile 'required_gates' must be list")
    return profile
