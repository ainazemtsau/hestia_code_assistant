"""Task path and state helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.schemas import validate_schema
from csk_next.io.files import ensure_dir, read_json, read_text, write_json, write_text
from csk_next.io.hashing import sha256_text
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso


def task_dir(layout: Layout, module_path: str, task_id: str) -> Path:
    return layout.module_tasks(module_path) / task_id


def task_run_dir(layout: Layout, module_path: str, task_id: str) -> Path:
    return layout.module_run(module_path) / "tasks" / task_id


def task_state_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "task.json"


def slices_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "slices.json"


def plan_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "plan.md"


def freeze_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "freeze.json"


def plan_approval_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "approvals" / "plan.json"


def ready_approval_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "approvals" / "ready.json"


def critic_report_path(layout: Layout, module_path: str, task_id: str) -> Path:
    return task_dir(layout, module_path, task_id) / "critic_report.json"


def legacy_critic_report_path(layout: Layout, module_path: str, task_id: str) -> Path:
    """Backward-compatible artifact path used by older engine versions."""
    return task_dir(layout, module_path, task_id) / "critic.json"


def resolve_critic_report_path(
    layout: Layout,
    module_path: str,
    task_id: str,
    *,
    migrate: bool = False,
) -> Path:
    """Resolve the active critic report path, optionally migrating legacy `critic.json`."""
    primary = critic_report_path(layout, module_path, task_id)
    if primary.exists():
        return primary

    legacy = legacy_critic_report_path(layout, module_path, task_id)
    if not legacy.exists():
        return primary

    if migrate:
        write_json(primary, read_json(legacy))
        return primary
    return legacy


def ensure_task_dirs(layout: Layout, module_path: str, task_id: str) -> None:
    ensure_dir(task_dir(layout, module_path, task_id))
    ensure_dir(task_run_dir(layout, module_path, task_id))
    ensure_dir(task_run_dir(layout, module_path, task_id) / "proofs")
    ensure_dir(task_run_dir(layout, module_path, task_id) / "logs")
    ensure_dir(task_run_dir(layout, module_path, task_id) / "context")
    ensure_dir(task_dir(layout, module_path, task_id) / "approvals")
    incidents = task_dir(layout, module_path, task_id) / "incidents.jsonl"
    if not incidents.exists():
        write_text(incidents, "")


def read_task_state(layout: Layout, module_path: str, task_id: str) -> dict[str, Any]:
    state = read_json(task_state_path(layout, module_path, task_id))
    validate_schema("task_state", state)
    return state


def write_task_state(layout: Layout, module_path: str, task_id: str, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now_iso()
    validate_schema("task_state", state)
    write_json(task_state_path(layout, module_path, task_id), state)


def calculate_plan_hashes(layout: Layout, module_path: str, task_id: str) -> tuple[str, str]:
    plan_hash = sha256_text(read_text(plan_path(layout, module_path, task_id)))
    slices_hash = sha256_text(read_text(slices_path(layout, module_path, task_id)))
    return plan_hash, slices_hash


def freeze_valid(layout: Layout, module_path: str, task_id: str) -> tuple[bool, str]:
    freeze_file = freeze_path(layout, module_path, task_id)
    if not freeze_file.exists():
        return False, "missing freeze"
    freeze = read_json(freeze_file)
    validate_schema("freeze", freeze)
    current_plan, current_slices = calculate_plan_hashes(layout, module_path, task_id)
    if freeze["plan_sha256"] != current_plan:
        return False, "plan drift"
    if freeze["slices_sha256"] != current_slices:
        return False, "slices drift"
    return True, "ok"
