"""Validation helpers shared across CLI modules."""

from __future__ import annotations

import re

from pfpkg.errors import EXIT_VALIDATION, PfError

MODULE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,62}$")


def suggest_safe_module_id(value: str) -> str:
    candidate = re.sub(r"[^a-z0-9_-]+", "-", value.strip().lower())
    candidate = re.sub(r"-+", "-", candidate).strip("-")
    if not candidate:
        return "module"
    if not re.match(r"^[a-z0-9]", candidate):
        candidate = f"m-{candidate}"
    return candidate[:63]


def is_safe_module_id(value: str) -> bool:
    return MODULE_ID_PATTERN.fullmatch(value) is not None


def validate_module_id_strict(value: str) -> str:
    if is_safe_module_id(value):
        return value
    suggested = suggest_safe_module_id(value)
    raise PfError(
        "invalid module_id: use lowercase letters, digits, '_' or '-', length 1..63",
        EXIT_VALIDATION,
        details={
            "module_id": value,
            "rule": MODULE_ID_PATTERN.pattern,
            "suggested_module_id": suggested,
        },
    )


def ensure_safe_module_id_or_raise(value: str, *, source: str = "module_id") -> str:
    if is_safe_module_id(value):
        return value
    raise PfError(
        f"unsafe module_id found in {source}: {value}",
        EXIT_VALIDATION,
        details={"module_id": value, "source": source},
    )
