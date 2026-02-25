"""Slice execution loop implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import append_event
from csk_next.gates.review import record_review
from csk_next.gates.scope import check_scope
from csk_next.gates.verify import parse_cmds, run_verify
from csk_next.io.files import write_json
from csk_next.io.runner import run_argv
from csk_next.profiles.manager import load_profile_from_paths
from csk_next.runtime.config import command_policy
from csk_next.runtime.paths import Layout
from csk_next.runtime.proofs import write_proof
from csk_next.runtime.slice_policies import fail_slice
from csk_next.runtime.snapshot import changed_files, take_snapshot
from csk_next.runtime.tasks import freeze_valid, plan_approval_path, task_run_dir
from csk_next.runtime.tasks_engine import (
    ensure_task_executable,
    load_slices,
    mark_task_blocked,
    mark_task_executing,
    read_task_state,
    update_slice_state,
)
from csk_next.runtime.time import utc_now_iso


def _find_slice(slices_doc: dict[str, Any], slice_id: str) -> dict[str, Any]:
    for item in slices_doc["slices"]:
        if item["slice_id"] == slice_id:
            return item
    raise KeyError(f"Slice not found: {slice_id}")


def _run_e2e(task_id: str, slice_id: str, task_run: Path, cwd: Path, commands: list[list[str]]) -> dict[str, Any]:
    passed = True
    command_results = []
    for argv in commands:
        result = run_argv(argv, cwd=cwd, check=False)
        command_results.append(
            {
                "argv": argv,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.returncode != 0:
            passed = False

    payload = {
        "task_id": task_id,
        "slice_id": slice_id,
        "passed": passed,
        "commands": command_results,
        "checked_at": utc_now_iso(),
    }
    write_proof(task_run, "e2e", payload, slice_id=slice_id)
    return payload


def execute_slice(
    *,
    layout: Layout,
    module_id: str,
    task_id: str,
    slice_id: str,
    implement_cmd: list[str] | None,
    verify_cmds_raw: list[str],
    e2e_cmds_raw: list[str],
    reviewer: str,
    p0: int,
    p1: int,
    p2: int,
    p3: int,
    review_notes: str,
) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    module_path = module["path"]

    state = read_task_state(layout, module_path, task_id)
    if state["status"] == "blocked":
        slice_state = state.get("slices", {}).get(slice_id, {})
        return {
            "status": "blocked",
            "slice_id": slice_id,
            "attempts": int(slice_state.get("attempts", 0)),
            "reason": state.get("blocked_reason") or "task blocked",
        }

    ensure_task_executable(layout, module_path, task_id)
    mark_task_executing(layout, module_path, task_id)

    if not plan_approval_path(layout, module_path, task_id).exists():
        raise ValueError("Task execution blocked: missing plan approval")

    freeze_ok, freeze_reason = freeze_valid(layout, module_path, task_id)
    if not freeze_ok:
        raise ValueError(f"Task execution blocked: {freeze_reason}")

    state = read_task_state(layout, module_path, task_id)
    slices_doc = load_slices(layout, module_path, task_id)
    slice_entry = _find_slice(slices_doc, slice_id)

    for dep in slice_entry.get("deps", []):
        dep_state = state["slices"].get(dep, {})
        if dep_state.get("status") != "done":
            raise ValueError(f"Dependency not done: {dep}")

    slice_state = state["slices"].setdefault(
        slice_id,
        {
            "status": "pending",
            "attempts": 0,
            "max_attempts": slice_entry.get("max_attempts", state["max_attempts"]),
        },
    )
    attempts = int(slice_state["attempts"])
    max_attempts = int(slice_state.get("max_attempts", state["max_attempts"]))
    if attempts >= max_attempts:
        update_slice_state(
            layout=layout,
            module_path=module_path,
            task_id=task_id,
            slice_id=slice_id,
            status="blocked",
            attempts=attempts,
            last_error="max attempts exceeded",
        )
        mark_task_blocked(layout, module_path, task_id, "max attempts exceeded")
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="token_waste",
            severity="high",
            phase="execution",
            message=f"Slice {slice_id} exceeded max attempts",
            remediation="Revise plan/profile/environment before rerun.",
            context={"task_id": task_id, "slice_id": slice_id, "attempts": attempts},
            status="blocked",
            gate="attempts",
            last_error="max attempts exceeded",
            block_task=True,
            blocked_reason="max attempts exceeded",
        )

    attempts += 1
    update_slice_state(
        layout=layout,
        module_path=module_path,
        task_id=task_id,
        slice_id=slice_id,
        status="running",
        attempts=attempts,
    )

    module_root = layout.module_root(module_path)
    before = take_snapshot(module_root)

    if implement_cmd:
        impl_result = run_argv(implement_cmd, cwd=module_root, check=False)
        if impl_result.returncode != 0:
            return fail_slice(
                layout=layout,
                module_path=module_path,
                module_id=module_id,
                task_id=task_id,
                slice_id=slice_id,
                attempts=attempts,
                kind="implement_fail",
                severity="high",
                phase="execution",
                message=f"Implement command failed: {' '.join(implement_cmd)}",
                remediation="Fix implementation command or environment and retry.",
                context={"task_id": task_id, "slice_id": slice_id, "stderr": impl_result.stderr},
                status="gate_failed",
                gate="implement",
                last_error="implement fail",
            )

    after = take_snapshot(module_root)
    changed = changed_files(before, after)
    task_run = task_run_dir(layout, module_path, task_id)

    required_gates = set(str(item) for item in slice_entry.get("required_gates", []))
    allowed_paths = list(slice_entry.get("allowed_paths", []))
    scope_required = "scope" in required_gates
    if scope_required and not allowed_paths:
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="scope_config_missing",
            severity="high",
            phase="execution",
            message=f"Scope gate requires allowed_paths for slice {slice_id}",
            remediation="Set non-empty allowed_paths in slices.json and re-freeze task plan.",
            context={"task_id": task_id, "slice_id": slice_id},
            status="gate_failed",
            gate="scope",
            last_error="scope config missing",
        )

    scope_proof = check_scope(
        task_id=task_id,
        slice_id=slice_id,
        task_run_dir=task_run,
        changed=changed,
        allowed_paths=allowed_paths,
    )
    append_event(
        layout=layout,
        event_type="scope.check.passed" if bool(scope_proof["passed"]) else "scope.check.failed",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        payload={
            "passed": bool(scope_proof["passed"]),
            "changed_count": len(changed),
            "violations": list(scope_proof.get("violations", [])),
        },
        artifact_refs=[str(task_run / "proofs" / slice_id / "scope.json")],
    )
    if scope_required and not bool(scope_proof["passed"]):
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="scope_violation",
            severity="high",
            phase="execution",
            message=f"Scope violation in slice {slice_id}",
            remediation="Revert out-of-scope changes or revise plan then re-freeze.",
            context={"task_id": task_id, "slice_id": slice_id, "violations": scope_proof["violations"]},
            status="blocked",
            gate="scope",
            last_error="scope violation",
            block_task=True,
            blocked_reason="scope violation",
        )

    verify_required = "verify" in required_gates
    verify_commands_raw = verify_cmds_raw or slice_entry.get("verify_commands", [])
    allowlist, denylist = command_policy(layout)

    def fail_verify_policy(error: ValueError) -> dict[str, Any]:
        block = attempts >= max_attempts
        append_event(
            layout=layout,
            event_type="verify.failed",
            actor="engine",
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            payload={
                "passed": False,
                "error": str(error),
                "commands_raw": [str(item) for item in verify_commands_raw],
            },
        )
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="verify_policy_reject",
            severity="high",
            phase="execution",
            message=f"Verify command policy rejected in slice {slice_id}: {error}",
            remediation="Adjust verify commands to satisfy policy/format rules and retry.",
            context={"task_id": task_id, "slice_id": slice_id, "error": str(error)},
            status="blocked" if block else "gate_failed",
            gate="verify",
            last_error="verify policy rejected max attempts" if block else "verify policy rejected",
            block_task=block,
            blocked_reason="verify policy retries exceeded" if block else None,
        )

    try:
        verify_commands = parse_cmds(verify_commands_raw)
    except ValueError as exc:
        return fail_verify_policy(exc)

    if verify_required and not verify_commands:
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="verify_config_missing",
            severity="high",
            phase="execution",
            message=f"Verify gate requires commands for slice {slice_id}",
            remediation="Provide verify commands in slices.json or slice run invocation.",
            context={"task_id": task_id, "slice_id": slice_id},
            status="gate_failed",
            gate="verify",
            last_error="verify config missing",
        )

    try:
        verify_proof = run_verify(
            task_id=task_id,
            slice_id=slice_id,
            task_run_dir=task_run,
            cwd=module_root,
            commands=verify_commands if verify_required else [],
            require_at_least_one=verify_required,
            allowlist=allowlist,
            denylist=denylist,
        )
    except ValueError as exc:
        return fail_verify_policy(exc)
    append_event(
        layout=layout,
        event_type="verify.passed" if bool(verify_proof["passed"]) else "verify.failed",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        payload={
            "passed": bool(verify_proof["passed"]),
            "commands": list(verify_proof.get("commands", [])),
            "cmd": " && ".join(" ".join(item.get("argv", [])) for item in verify_proof.get("commands", [])),
            "executed_count": int(verify_proof.get("executed_count", 0)),
            "duration_ms": int(verify_proof.get("duration_ms", 0)),
            "log_path": verify_proof.get("log_path"),
        },
        artifact_refs=[str(task_run / "proofs" / slice_id / "verify.json"), str(verify_proof.get("log_path", ""))],
    )
    if verify_required and not bool(verify_proof["passed"]):
        block = attempts >= max_attempts
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="verify_fail",
            severity="medium",
            phase="execution",
            message=f"Verify failed in slice {slice_id}",
            remediation="Fix failing checks and retry.",
            context={"task_id": task_id, "slice_id": slice_id},
            status="blocked" if block else "gate_failed",
            gate="verify",
            last_error="verify fail max attempts" if block else "verify fail",
            block_task=block,
            blocked_reason="verify retries exceeded" if block else None,
        )

    review_required = "review" in required_gates
    review_proof = record_review(
        task_id=task_id,
        slice_id=slice_id,
        task_run_dir=task_run,
        reviewer=reviewer,
        p0=p0,
        p1=p1,
        p2=p2,
        p3=p3,
        notes=review_notes,
    )
    if review_required and not bool(review_proof["passed"]):
        return fail_slice(
            layout=layout,
            module_path=module_path,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_id,
            attempts=attempts,
            kind="review_fail",
            severity="medium",
            phase="execution",
            message=f"Review failed in slice {slice_id}",
            remediation="Address review findings and retry.",
            context={"task_id": task_id, "slice_id": slice_id, "p0": p0, "p1": p1},
            status="review_failed",
            gate="review",
            last_error="review fail",
        )

    profile = load_profile_from_paths(layout.engine, layout.local, state["profile"])
    requires_e2e = bool(slice_entry.get("e2e_required", False) or profile.get("e2e", {}).get("required", False))
    if requires_e2e:
        e2e_raw = e2e_cmds_raw or list(profile.get("e2e", {}).get("commands", []))
        if not e2e_raw:
            return fail_slice(
                layout=layout,
                module_path=module_path,
                module_id=module_id,
                task_id=task_id,
                slice_id=slice_id,
                attempts=attempts,
                kind="e2e_missing",
                severity="high",
                phase="execution",
                message=f"E2E required but missing commands for slice {slice_id}",
                remediation="Provide e2e commands in profile or slice run args.",
                context={"task_id": task_id, "slice_id": slice_id},
                status="blocked",
                gate="e2e",
                last_error="e2e required",
                block_task=True,
                blocked_reason="required e2e missing",
            )

        e2e_proof = _run_e2e(task_id, slice_id, task_run, module_root, parse_cmds(e2e_raw))
        if not bool(e2e_proof["passed"]):
            return fail_slice(
                layout=layout,
                module_path=module_path,
                module_id=module_id,
                task_id=task_id,
                slice_id=slice_id,
                attempts=attempts,
                kind="e2e_fail",
                severity="medium",
                phase="execution",
                message=f"E2E failed in slice {slice_id}",
                remediation="Fix e2e failures and retry.",
                context={"task_id": task_id, "slice_id": slice_id},
                status="gate_failed",
                gate="e2e",
                last_error="e2e fail",
            )

    proof_pack = {
        "task_id": task_id,
        "slice_id": slice_id,
        "scope": str(task_run / "proofs" / slice_id / "scope.json"),
        "verify": str(task_run / "proofs" / slice_id / "verify.json"),
        "review": str(task_run / "proofs" / slice_id / "review.json"),
        "e2e": str(task_run / "proofs" / slice_id / "e2e.json") if requires_e2e else None,
        "written_at": utc_now_iso(),
    }
    write_proof(task_run, "proof_pack", proof_pack, slice_id=slice_id)
    manifest_path = task_run / "proofs" / slice_id / "manifest.json"
    write_json(
        manifest_path,
        {
            "task_id": task_id,
            "slice_id": slice_id,
            "gates": {
                "scope": bool(scope_proof["passed"]),
                "verify": bool(verify_proof["passed"]),
                "review": bool(review_proof["passed"]),
                "e2e": None if not requires_e2e else bool(e2e_proof["passed"]),
            },
            "proofs": proof_pack,
            "written_at": utc_now_iso(),
        },
    )
    append_event(
        layout=layout,
        event_type="proof.pack.written",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        payload={"manifest_path": str(manifest_path)},
        artifact_refs=[str(manifest_path)],
    )

    update_slice_state(
        layout=layout,
        module_path=module_path,
        task_id=task_id,
        slice_id=slice_id,
        status="done",
        attempts=attempts,
        last_error=None,
    )
    append_event(
        layout=layout,
        event_type="slice.completed",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        payload={"attempts": attempts},
        artifact_refs=[str(manifest_path)],
    )

    return {
        "status": "done",
        "slice_id": slice_id,
        "attempts": attempts,
        "proof_pack": proof_pack,
    }
