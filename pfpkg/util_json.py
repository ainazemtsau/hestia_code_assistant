"""JSON helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pfpkg.errors import PfError, EXIT_VALIDATION


JSON_OBJECT = dict[str, Any]


def dumps_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)


def loads_json_object(raw: str, *, label: str = "json") -> JSON_OBJECT:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PfError(f"invalid {label}: {exc}", EXIT_VALIDATION) from exc
    if not isinstance(value, dict):
        raise PfError(f"{label} must be a JSON object", EXIT_VALIDATION)
    return value


def load_json_object_from_ref(ref: str, *, label: str = "json") -> JSON_OBJECT:
    if ref.startswith("@"):
        path = Path(ref[1:])
        if not path.exists():
            raise PfError(f"{label} file not found: {path}", EXIT_VALIDATION)
        return loads_json_object(path.read_text(encoding="utf-8"), label=label)
    return loads_json_object(ref, label=label)
