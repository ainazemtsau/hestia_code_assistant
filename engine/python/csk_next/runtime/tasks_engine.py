"""Task operations and state transitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.models import default_slice_entry, ensure_task_transition, task_state_stub
from csk_next.domain.schemas import validate_schema
from csk_next.eventlog.store import append_event
from csk_next.io.files import ensure_dir, read_json, write_json, write_text
from csk_next.io.hashing import sha256_text
from csk_next.io.jsonl import append_jsonl
from csk_next.runtime.ids import next_task_id
from csk_next.runtime.paths import Layout
from csk_next.runtime.tasks import (
    calculate_plan_hashes,
    critic_path,
    ensure_task_dirs,
    freeze_path,
    plan_approval_path,
    plan_path,
    read_task_state,
    slices_path,
    task_dir,
    task_state_path,
    write_task_state,
)
from csk_next.runtime.time import utc_now_iso


def _set_task_status(layout: Layout, module_path: str, task_id: str, new_status: str) -> dict[str, Any]:
    state = read_task_state(layout, module_path, task_id)
    ensure_task_transition(state["status"], new_status)
    state["status"] = new_status
    if new_status != "blocked":
        state["blocked_reason"] = None
    write_task_state(layout, module_path, task_id, state)
    return state


def task_new(
    *,
    layout: Layout,
    module_id: str,
    module_path: str,
    mission_id: str | None,
    profile: str,
    max_attempts: int,
    slice_count: int = 1,
    plan_template: str | None = None,
) -> dict[str, Any]:
    if slice_count <= 0:
        raise ValueError("slice_count must be > 0")

    tasks_dir = layout.module_tasks(module_path)
    ensure_dir(tasks_dir)
    task_id = next_task_id(tasks_dir)

    ensure_task_dirs(layout, module_path, task_id)
    task_folder = task_dir(layout, module_path, task_id)

    template_path = layout.engine / "templates" / "artifacts" / "plan.md"
    if plan_template:
        plan_body = plan_template
    elif template_path.exists():
        plan_body = template_path.read_text(encoding="utf-8")
    else:
        plan_body = (
            f"# Plan for {task_id}\n\n"
            "## Goal\n- TODO\n\n"
            "## Scope\n- TODO\n\n"
            "## Non-scope\n- TODO\n\n"
            "## Checks\n- TODO\n\n"
            "## Slices\n- S-0001\n"
        )
    write_text(plan_path(layout, module_path, task_id), plan_body)

    slices_doc = {"slices": [default_slice_entry(f"S-{index:04d}") for index in range(1, slice_count + 1)]}
    validate_schema("slices", slices_doc)
    write_json(slices_path(layout, module_path, task_id), slices_doc)

    write_text(task_folder / "decisions.jsonl", "")

    state = task_state_stub(task_id, mission_id, module_id, profile, max_attempts)
    for slice_entry in slices_doc["slices"]:
        state["slices"][slice_entry["slice_id"]] = {
            "status": slice_entry["status"],
            "attempts": slice_entry["attempts"],
            "max_attempts": slice_entry.get("max_attempts", max_attempts),
        }
    write_task_state(layout, module_path, task_id, state)

    append_event(
        layout=layout,
        event_type="task.created",
        actor="engine",
        mission_id=mission_id,
        module_id=module_id,
        task_id=task_id,
        payload={"task_id": task_id, "module_id": module_id, "module_path": module_path},
        artifact_refs=[str(task_folder / "plan.md"), str(task_folder / "slices.json")],
    )
    for slice_entry in slices_doc["slices"]:
        append_event(
            layout=layout,
            event_type="slice.created",
            actor="engine",
            mission_id=mission_id,
            module_id=module_id,
            task_id=task_id,
            slice_id=slice_entry["slice_id"],
            payload={
                "task_id": task_id,
                "slice_id": slice_entry["slice_id"],
                "required_gates": list(slice_entry.get("required_gates", [])),
            },
            artifact_refs=[str(task_folder / "slices.json")],
        )

    return {
        "status": "ok",
        "task_id": task_id,
        "module_id": module_id,
        "module_path": module_path,
        "task_path": str(task_folder),
    }


def task_record_critic(
    *,
    layout: Layout,
    module_path: str,
    task_id: str,
    critic: str,
    p0: int,
    p1: int,
    p2: int,
    p3: int,
    notes: str,
) -> dict[str, Any]:
    payload = {
        "task_id": task_id,
        "critic": critic,
        "p0": p0,
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "notes": notes,
        "passed": p0 == 0 and p1 == 0,
        "reviewed_at": utc_now_iso(),
    }
    write_json(critic_path(layout, module_path, task_id), payload)

    append_event(
        layout=layout,
        event_type="task.critic_passed" if payload["passed"] else "task.critic_failed",
        actor=critic,
        module_id=state_module_id(layout, module_path),
        task_id=task_id,
        payload=payload,
        artifact_refs=[str(critic_path(layout, module_path, task_id))],
    )

    if payload["passed"]:
        _set_task_status(layout, module_path, task_id, "critic_passed")

    return {"status": "ok", "critic": payload}


def task_freeze(*, layout: Layout, module_path: str, task_id: str) -> dict[str, Any]:
    critic_file = critic_path(layout, module_path, task_id)
    if not critic_file.exists():
        raise ValueError("Cannot freeze without critic review")

    critic = read_json(critic_file)
    if critic.get("p0", 1) > 0 or critic.get("p1", 1) > 0:
        raise ValueError("Cannot freeze with critic P0/P1 findings")

    plan_hash, slices_hash = calculate_plan_hashes(layout, module_path, task_id)
    payload = {
        "task_id": task_id,
        "plan_sha256": plan_hash,
        "slices_sha256": slices_hash,
        "frozen_at": utc_now_iso(),
    }
    validate_schema("freeze", payload)
    write_json(freeze_path(layout, module_path, task_id), payload)
    append_event(
        layout=layout,
        event_type="task.frozen",
        actor="engine",
        module_id=state_module_id(layout, module_path),
        task_id=task_id,
        payload=payload,
        artifact_refs=[str(freeze_path(layout, module_path, task_id))],
    )

    _set_task_status(layout, module_path, task_id, "frozen")
    return {"status": "ok", "freeze": payload}


def task_approve_plan(
    *,
    layout: Layout,
    module_path: str,
    task_id: str,
    approved_by: str,
) -> dict[str, Any]:
    freeze_file = freeze_path(layout, module_path, task_id)
    if not freeze_file.exists():
        raise ValueError("Cannot approve plan without freeze")

    current_plan_hash, current_slices_hash = calculate_plan_hashes(layout, module_path, task_id)
    freeze_doc = read_json(freeze_file)
    if freeze_doc["plan_sha256"] != current_plan_hash or freeze_doc["slices_sha256"] != current_slices_hash:
        raise ValueError("Cannot approve plan with freeze drift")

    approval = {
        "approved_by": approved_by,
        "approved_at": utc_now_iso(),
    }
    validate_schema("approval", approval)
    write_json(plan_approval_path(layout, module_path, task_id), approval)
    append_event(
        layout=layout,
        event_type="task.plan_approved",
        actor=approved_by,
        module_id=state_module_id(layout, module_path),
        task_id=task_id,
        payload=approval,
        artifact_refs=[str(plan_approval_path(layout, module_path, task_id))],
    )

    _set_task_status(layout, module_path, task_id, "plan_approved")
    return {"status": "ok", "approval": approval}


def state_module_id(layout: Layout, module_path: str) -> str | None:
    registry_path = layout.registry
    if not registry_path.exists():
        return None
    registry = read_json(registry_path)
    for item in registry.get("modules", []):
        if str(item.get("path")) == module_path:
            return str(item.get("module_id"))
    return None


def task_status(*, layout: Layout, module_path: str, task_id: str) -> dict[str, Any]:
    task_state = read_task_state(layout, module_path, task_id)
    freeze_file = freeze_path(layout, module_path, task_id)
    approvals = {
        "plan": plan_approval_path(layout, module_path, task_id).exists(),
        "ready": (task_dir(layout, module_path, task_id) / "approvals" / "ready.json").exists(),
    }
    return {
        "status": "ok",
        "task": task_state,
        "freeze_exists": freeze_file.exists(),
        "approvals": approvals,
    }


def add_decision(
    *,
    layout: Layout,
    module_path: str,
    task_id: str,
    decision: str,
    rationale: str,
    decided_by: str,
) -> None:
    row = {
        "decision": decision,
        "rationale": rationale,
        "decided_by": decided_by,
        "decided_at": utc_now_iso(),
    }
    append_jsonl(task_dir(layout, module_path, task_id) / "decisions.jsonl", row)


def load_slices(layout: Layout, module_path: str, task_id: str) -> dict[str, Any]:
    doc = read_json(slices_path(layout, module_path, task_id))
    validate_schema("slices", doc)
    return doc


def update_slice_state(
    *,
    layout: Layout,
    module_path: str,
    task_id: str,
    slice_id: str,
    status: str,
    attempts: int | None = None,
    last_error: str | None = None,
) -> None:
    state = read_task_state(layout, module_path, task_id)
    slice_state = state["slices"].setdefault(slice_id, {"status": "pending", "attempts": 0, "max_attempts": state["max_attempts"]})
    slice_state["status"] = status
    if attempts is not None:
        slice_state["attempts"] = attempts
    if last_error is not None:
        slice_state["last_error"] = last_error
    write_task_state(layout, module_path, task_id, state)


def ensure_task_executable(layout: Layout, module_path: str, task_id: str) -> None:
    state = read_task_state(layout, module_path, task_id)
    if state["status"] not in {"plan_approved", "executing", "ready_validated"}:
        raise ValueError(f"Task is not executable in status '{state['status']}'")


def mark_task_executing(layout: Layout, module_path: str, task_id: str) -> None:
    state = read_task_state(layout, module_path, task_id)
    if state["status"] == "plan_approved":
        state["status"] = "executing"
        write_task_state(layout, module_path, task_id, state)


def mark_task_status(layout: Layout, module_path: str, task_id: str, status: str) -> None:
    _set_task_status(layout, module_path, task_id, status)


def mark_task_blocked(layout: Layout, module_path: str, task_id: str, reason: str) -> None:
    state = read_task_state(layout, module_path, task_id)
    ensure_task_transition(state["status"], "blocked")
    state["status"] = "blocked"
    state["blocked_reason"] = reason
    write_task_state(layout, module_path, task_id, state)
