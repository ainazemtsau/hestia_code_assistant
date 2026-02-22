"""Review proof recording."""

from __future__ import annotations

from pathlib import Path

from csk_next.domain.schemas import validate_schema
from csk_next.runtime.proofs import write_proof
from csk_next.runtime.time import utc_now_iso


def record_review(
    *,
    task_id: str,
    slice_id: str,
    task_run_dir: Path,
    reviewer: str,
    p0: int,
    p1: int,
    p2: int,
    p3: int,
    notes: str,
) -> dict[str, object]:
    passed = p0 == 0 and p1 == 0
    proof = {
        "task_id": task_id,
        "slice_id": slice_id,
        "reviewer": reviewer,
        "p0": p0,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "passed": passed,
        "notes": notes,
        "recorded_at": utc_now_iso(),
    }
    validate_schema("review_proof", proof)
    write_proof(task_run_dir, "review", proof, slice_id=slice_id)
    return proof
