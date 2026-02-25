"""READY gate validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.schemas import validate_schema
from csk_next.io.files import read_json, write_json
from csk_next.runtime.proofs import proof_dir, write_proof
from csk_next.runtime.tasks import freeze_valid, plan_approval_path
from csk_next.runtime.time import utc_now_iso


def _load_proof(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return read_json(path)


def validate_ready(
    *,
    task_id: str,
    module_path: str,
    task_dir: Path,
    task_run_dir: Path,
    layout,
    profile: dict[str, Any],
) -> dict[str, Any]:
    checks: dict[str, Any] = {}

    freeze_ok, freeze_reason = freeze_valid(layout, module_path, task_id)
    checks["freeze_valid"] = {"passed": freeze_ok, "detail": freeze_reason}

    approval = plan_approval_path(layout, module_path, task_id)
    checks["plan_approval_exists"] = {"passed": approval.exists()}

    slices_doc = read_json(task_dir / "slices.json")
    all_slices: list[dict[str, Any]] = slices_doc.get("slices", [])

    scope_ok = True
    verify_ok = True
    review_ok = True
    e2e_ok = True

    for slice_entry in all_slices:
        slice_id = slice_entry["slice_id"]
        required_gates = set(str(item) for item in slice_entry.get("required_gates", []))
        slice_proofs = proof_dir(task_run_dir, slice_id)
        scope = _load_proof(slice_proofs / "scope.json")
        verify = _load_proof(slice_proofs / "verify.json")
        review = _load_proof(slice_proofs / "review.json")
        e2e = _load_proof(slice_proofs / "e2e.json")

        if "scope" in required_gates:
            scope_ok = scope_ok and bool(scope and scope.get("passed"))
        if "verify" in required_gates:
            verify_ok = verify_ok and bool(
                verify
                and verify.get("passed")
                and int(verify.get("executed_count", len(verify.get("commands", [])))) > 0
            )
        if "review" in required_gates:
            review_ok = review_ok and bool(
                review and review.get("passed") and review.get("p0") == 0 and review.get("p1") == 0
            )

        needs_e2e = bool(slice_entry.get("e2e_required", False)) or bool(profile.get("e2e", {}).get("required", False))
        if needs_e2e:
            e2e_ok = e2e_ok and bool(e2e and e2e.get("passed"))

    checks["latest_scope_proof_ok"] = {"passed": scope_ok}
    checks["verify_coverage_ok"] = {"passed": verify_ok}
    checks["review_ok"] = {"passed": review_ok}
    checks["e2e_ok_if_required"] = {"passed": e2e_ok}

    user_check_required = bool(profile.get("user_check_required", False))
    user_check_file = task_dir / "approvals" / "user_check.json"
    checks["user_check_recorded"] = {
        "required": user_check_required,
        "passed": (not user_check_required) or user_check_file.exists(),
    }

    all_passed = all(item.get("passed", False) for item in checks.values())
    proof = {
        "task_id": task_id,
        "passed": all_passed,
        "checks": checks,
        "checked_at": utc_now_iso(),
    }
    validate_schema("ready_proof", proof)
    write_proof(task_run_dir, "ready", proof)

    handoff = {
        "task_id": task_id,
        "summary": "READY handoff generated",
        "proof_references": {"ready": str(task_run_dir / "proofs" / "ready.json")},
        "manual_smoke_steps": [
            "Open changed module and run local app/tests.",
            "Validate primary user flow from task plan.",
            "Check logs for regressions.",
        ],
        "generated_at": utc_now_iso(),
    }
    ready_dir = proof_dir(task_run_dir) / "READY"
    ready_dir.mkdir(parents=True, exist_ok=True)
    handoff_md = ready_dir / "handoff.md"
    handoff_text = [
        f"# READY handoff for {task_id}",
        "",
        handoff["summary"],
        "",
        "## Proof references",
        f"- ready: {handoff['proof_references']['ready']}",
        "",
        "## Manual smoke steps",
    ]
    handoff_text.extend([f"- {step}" for step in handoff["manual_smoke_steps"]])
    handoff_text.append("")
    handoff_text.append(f"Generated at: {handoff['generated_at']}")
    handoff_md.write_text("\n".join(handoff_text) + "\n", encoding="utf-8")
    handoff["handoff_path"] = str(handoff_md)
    write_json(task_dir / "handoff.json", handoff)
    return proof
