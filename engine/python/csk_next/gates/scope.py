"""Scope gate implementation."""

from __future__ import annotations

from pathlib import Path

from csk_next.domain.schemas import validate_schema
from csk_next.runtime.proofs import write_proof
from csk_next.runtime.time import utc_now_iso


def check_scope(
    *,
    task_id: str,
    slice_id: str,
    task_run_dir: Path,
    changed: list[str],
    allowed_paths: list[str],
) -> dict[str, object]:
    """Validate changed files stay within allowed paths."""
    normalized = [entry.strip("/") for entry in allowed_paths]
    violations: list[str] = []
    if normalized:
        for path in changed:
            if not any(path == prefix or path.startswith(prefix + "/") for prefix in normalized):
                violations.append(path)

    proof = {
        "task_id": task_id,
        "slice_id": slice_id,
        "passed": len(violations) == 0,
        "allowed_paths": normalized,
        "changed_files": changed,
        "violations": violations,
        "checked_at": utc_now_iso(),
    }
    validate_schema("scope_proof", proof)
    write_proof(task_run_dir, "scope", proof, slice_id=slice_id)
    return proof
