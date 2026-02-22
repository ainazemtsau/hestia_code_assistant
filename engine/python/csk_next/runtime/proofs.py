"""Proof file helpers."""

from __future__ import annotations

from pathlib import Path

from csk_next.io.files import ensure_dir, write_json


def proof_dir(task_run_dir: Path, slice_id: str | None = None) -> Path:
    if slice_id is None:
        return task_run_dir / "proofs"
    return task_run_dir / "proofs" / slice_id


def write_proof(task_run_dir: Path, kind: str, payload: dict, slice_id: str | None = None) -> Path:
    target_dir = proof_dir(task_run_dir, slice_id)
    ensure_dir(target_dir)
    target_path = target_dir / f"{kind}.json"
    write_json(target_path, payload)
    return target_path
