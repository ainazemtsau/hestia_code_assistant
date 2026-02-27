"""Validation routines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.models import TASK_STATUSES
from csk_next.domain.state import ensure_registry
from csk_next.domain.schemas import validate_schema
from csk_next.io.files import read_json
from csk_next.profiles.manager import load_profile_from_paths
from csk_next.runtime.paths import Layout
from csk_next.runtime.tasks import freeze_valid, task_dir, task_run_dir, resolve_critic_report_path


class ValidationError(RuntimeError):
    """Raised on strict validation failures."""


def _validate_registry(layout: Layout, errors: list[str]) -> dict[str, Any] | None:
    if not layout.registry.exists():
        errors.append("missing .csk/app/registry.json")
        return None
    try:
        registry = ensure_registry(layout.registry)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid registry: {exc}")
        return None
    return registry


def _validate_slice_proofs(
    *,
    layout: Layout,
    module_path: str,
    task_id: str,
    slices_doc: dict[str, Any],
    task_state: dict[str, Any],
    profile: dict[str, Any],
    strict: bool,
    errors: list[str],
) -> None:
    if not strict:
        return

    task_proof_root = task_run_dir(layout, module_path, task_id) / "proofs"
    for slice_entry in slices_doc.get("slices", []):
        slice_id = str(slice_entry.get("slice_id"))
        required_gates = set(str(item) for item in slice_entry.get("required_gates", []))
        slice_status = str(task_state.get("slices", {}).get(slice_id, {}).get("status", "pending"))
        slice_is_done = slice_status == "done"
        require_complete = task_state["status"] in {"ready_validated", "ready_approved", "retro_done", "closed"}
        slice_root = task_proof_root / slice_id

        if "scope" in required_gates and (slice_is_done or require_complete):
            scope = slice_root / "scope.json"
            if not scope.exists():
                errors.append(f"missing scope proof for {task_id}:{slice_id}")
            else:
                scope_doc = read_json(scope)
                if not bool(scope_doc.get("passed")):
                    errors.append(f"scope proof failed for {task_id}:{slice_id}")

        if "verify" in required_gates and (slice_is_done or require_complete):
            verify = slice_root / "verify.json"
            if not verify.exists():
                errors.append(f"missing verify proof for {task_id}:{slice_id}")
            else:
                verify_doc = read_json(verify)
                executed = int(verify_doc.get("executed_count", len(verify_doc.get("commands", []))))
                if not bool(verify_doc.get("passed")) or executed <= 0:
                    errors.append(f"verify proof failed/incomplete for {task_id}:{slice_id}")

        if "review" in required_gates and (slice_is_done or require_complete):
            review = slice_root / "review.json"
            if not review.exists():
                errors.append(f"missing review proof for {task_id}:{slice_id}")
            else:
                review_doc = read_json(review)
                if not (
                    bool(review_doc.get("passed"))
                    and int(review_doc.get("p0", 1)) == 0
                    and int(review_doc.get("p1", 1)) == 0
                ):
                    errors.append(f"review proof failed for {task_id}:{slice_id}")

        requires_e2e = bool(slice_entry.get("e2e_required", False)) or bool(
            profile.get("e2e", {}).get("required", False)
        )
        if requires_e2e and (slice_is_done or require_complete):
            e2e = slice_root / "e2e.json"
            if not e2e.exists():
                errors.append(f"missing e2e proof for {task_id}:{slice_id}")
            else:
                e2e_doc = read_json(e2e)
                if not bool(e2e_doc.get("passed")):
                    errors.append(f"e2e proof failed for {task_id}:{slice_id}")


def _validate_task(layout: Layout, module_path: str, task_id: str, strict: bool, errors: list[str]) -> None:
    task_root = task_dir(layout, module_path, task_id)
    task_state_path = task_root / "task.json"
    slices_path = task_root / "slices.json"
    plan_path = task_root / "plan.md"
    critic_path = resolve_critic_report_path(layout, module_path, task_id)
    freeze_path = task_root / "freeze.json"
    plan_approval_path = task_root / "approvals" / "plan.json"
    ready_approval_path = task_root / "approvals" / "ready.json"
    retro_path = task_root / "retro.md"

    if not task_state_path.exists():
        errors.append(f"missing task state: {task_state_path}")
        return

    state = read_json(task_state_path)
    try:
        validate_schema("task_state", state)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid task state {task_id}: {exc}")
        return

    status = str(state.get("status", ""))
    if status not in TASK_STATUSES:
        errors.append(f"invalid task status {task_id}: {status}")

    if not slices_path.exists():
        errors.append(f"missing slices: {slices_path}")
        return
    slices_doc = read_json(slices_path)
    try:
        validate_schema("slices", slices_doc)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid slices {task_id}: {exc}")
        return

    slice_entries: dict[str, dict[str, Any]] = {
        str(item["slice_id"]): item for item in slices_doc.get("slices", [])
    }
    slice_states = state.get("slices", {})
    if strict:
        if set(slice_entries) != set(slice_states):
            errors.append(f"task slice state mismatch for {task_id}: task.json vs slices.json")
        for slice_id, slice_state in slice_states.items():
            attempts = int(slice_state.get("attempts", 0))
            max_attempts = int(slice_state.get("max_attempts", state.get("max_attempts", 1)))
            if attempts > max_attempts:
                errors.append(f"slice attempts overflow for {task_id}:{slice_id}")
        for slice_id, slice_entry in slice_entries.items():
            required_gates = set(str(item) for item in slice_entry.get("required_gates", []))
            if "scope" in required_gates and not list(slice_entry.get("allowed_paths", [])):
                errors.append(f"scope config missing for {task_id}:{slice_id}")
            if "verify" in required_gates and not list(slice_entry.get("verify_commands", [])):
                errors.append(f"verify config missing for {task_id}:{slice_id}")

    if not plan_path.exists():
        errors.append(f"missing plan: {plan_path}")

    critic_doc: dict[str, Any] | None = None
    critic_doc_is_valid = False
    if critic_path.exists():
        critic_doc = read_json(critic_path)
        try:
            validate_schema("critic_report", critic_doc)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"invalid critic report {task_id}: {exc}")
        else:
            critic_doc_is_valid = True

    if status in {"critic_passed", "frozen", "plan_approved", "executing", "ready_validated", "ready_approved", "blocked", "retro_done", "closed"} and not critic_path.exists():
        errors.append(f"missing critic record for {task_id}")
    if (
        status in {
            "critic_passed",
            "frozen",
            "plan_approved",
            "executing",
            "ready_validated",
            "ready_approved",
            "blocked",
            "retro_done",
            "closed",
        }
        and isinstance(critic_doc, dict)
        and critic_doc_is_valid
    ):
        try:
            p0 = int(critic_doc.get("p0", 1))
            p1 = int(critic_doc.get("p1", 1))
        except (TypeError, ValueError):
            errors.append(f"invalid critic severity values for {task_id}: expected integers in p0/p1")
        else:
            if p0 > 0 or p1 > 0:
                errors.append(f"critic report contains P0/P1 findings for {task_id}")

    if status in {"frozen", "plan_approved", "executing", "ready_validated", "ready_approved", "blocked", "retro_done", "closed"}:
        if not freeze_path.exists():
            errors.append(f"missing freeze for {task_id}")
        ok, reason = freeze_valid(layout, module_path, task_id)
        if not ok:
            errors.append(f"freeze invalid for {task_id}: {reason}")

    if status in {"plan_approved", "executing", "ready_validated", "ready_approved", "blocked", "retro_done", "closed"} and not plan_approval_path.exists():
        errors.append(f"missing plan approval for {task_id}")

    profile_name = str(state.get("profile", "default"))
    try:
        profile = load_profile_from_paths(layout.engine, layout.local, profile_name)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"invalid profile '{profile_name}' for {task_id}: {exc}")
        profile = {
            "name": profile_name,
            "required_gates": ["scope", "verify", "review"],
            "e2e": {"required": False, "commands": []},
            "user_check_required": False,
        }

    if status == "blocked" and not state.get("blocked_reason"):
        errors.append(f"blocked task missing blocked_reason for {task_id}")

    if status in {"ready_validated", "ready_approved", "retro_done", "closed"}:
        for slice_id, slice_state in slice_states.items():
            if slice_state.get("status") != "done":
                errors.append(f"ready-stage task has non-done slice {task_id}:{slice_id}")

    _validate_slice_proofs(
        layout=layout,
        module_path=module_path,
        task_id=task_id,
        slices_doc=slices_doc,
        task_state=state,
        profile=profile,
        strict=strict,
        errors=errors,
    )

    ready_proof = task_run_dir(layout, module_path, task_id) / "proofs" / "ready.json"
    if status in {"ready_validated", "ready_approved", "retro_done", "closed"}:
        if not ready_proof.exists():
            errors.append(f"missing ready proof for {task_id}")
        else:
            ready_doc = read_json(ready_proof)
            if not bool(ready_doc.get("passed")):
                errors.append(f"ready proof failed for {task_id}")
            if strict and bool(profile.get("user_check_required", False)):
                user_check = task_root / "approvals" / "user_check.json"
                if not user_check.exists():
                    errors.append(f"missing user check approval for {task_id}")

    if status in {"ready_approved", "retro_done", "closed"} and not ready_approval_path.exists():
        errors.append(f"missing ready approval for {task_id}")

    if status in {"retro_done", "closed"} and not retro_path.exists():
        errors.append(f"missing retro.md for {task_id}")


def _validate_mission(layout: Layout, mission_path: Path, module_ids: set[str], strict: bool, errors: list[str]) -> None:
    mission_json = mission_path / "mission.json"
    spec_md = mission_path / "spec.md"
    routing_json = mission_path / "routing.json"
    milestones_json = mission_path / "milestones.json"
    worktrees_json = mission_path / "worktrees.json"

    for required in [mission_json, spec_md, routing_json, milestones_json, worktrees_json]:
        if not required.exists():
            errors.append(f"missing mission artifact: {required}")
            return

    mission = read_json(mission_json)
    routing = read_json(routing_json)
    milestones = read_json(milestones_json)
    worktrees = read_json(worktrees_json)
    try:
        validate_schema("mission", mission)
        validate_schema("mission_routing", routing)
        validate_schema("mission_milestones", milestones)
        validate_schema("mission_worktrees", worktrees)
    except Exception as exc:  # noqa: BLE001
        errors.append(f"mission schema error in {mission_path.name}: {exc}")
        return

    for route in routing.get("module_routes", []):
        module_id = str(route.get("module_id", ""))
        if module_id not in module_ids:
            errors.append(f"mission {mission_path.name} references unknown module {module_id}")

    for milestone in milestones.get("milestones", []):
        for module_id in milestone.get("module_items", []):
            if str(module_id) not in module_ids:
                errors.append(f"milestone in {mission_path.name} references unknown module {module_id}")

    opt_out = set(str(item) for item in worktrees.get("opt_out_modules", []))
    create_status = worktrees.get("create_status", {})
    for module_id in routing.get("module_routes", []):
        module_name = str(module_id.get("module_id", ""))
        if module_name not in worktrees.get("module_worktrees", {}):
            errors.append(f"worktree mapping missing for {mission_path.name}:{module_name}")
            continue

        if strict:
            if module_name not in create_status:
                errors.append(f"worktree create_status missing for {mission_path.name}:{module_name}")
                continue
            status = create_status[module_name]
            created = bool(status.get("created", False))
            fallback = status.get("fallback_reason")
            mapped_path = Path(worktrees["module_worktrees"][module_name])
            if created and not mapped_path.exists():
                errors.append(f"worktree path does not exist for {mission_path.name}:{module_name}")
            if (not created) and module_name not in opt_out:
                errors.append(f"worktree create_status inconsistent for {mission_path.name}:{module_name}")
            if (not created) and not fallback:
                errors.append(f"worktree fallback_reason missing for {mission_path.name}:{module_name}")


def _validate_modules(layout: Layout, registry: dict[str, Any], strict: bool, errors: list[str]) -> None:
    for module in registry["modules"]:
        module_id = str(module["module_id"])
        module_path = str(module["path"])
        module_root = layout.module_root(module_path)
        if bool(module.get("initialized", False)) and not module_root.exists():
            errors.append(f"module path missing for {module_id}: {module_path}")
        if strict and bool(module.get("initialized", False)):
            kernel = layout.module_kernel(module_path) / "kernel.json"
            if not kernel.exists():
                errors.append(f"initialized module missing kernel: {module_id}")


def validate_all(layout: Layout, strict: bool) -> dict[str, Any]:
    errors: list[str] = []

    if not layout.csk.exists():
        errors.append("missing .csk directory")

    registry = _validate_registry(layout, errors)
    if registry is None:
        result = {"status": "failed", "strict": strict, "errors": errors}
        if strict:
            raise ValidationError("; ".join(errors))
        return result

    module_ids = set(str(module["module_id"]) for module in registry["modules"])
    _validate_modules(layout, registry, strict, errors)

    if layout.missions.exists():
        for mission_dir in sorted(path for path in layout.missions.iterdir() if path.is_dir()):
            _validate_mission(layout, mission_dir, module_ids, strict, errors)

    for module in registry["modules"]:
        module_path = module["path"]
        tasks_root = layout.module_tasks(module_path)
        if not tasks_root.exists():
            continue
        for child in sorted(tasks_root.iterdir()):
            if child.is_dir() and child.name.startswith("T-"):
                _validate_task(layout, module_path, child.name, strict, errors)

    status = "ok" if not errors else "failed"
    result = {
        "status": status,
        "strict": strict,
        "errors": errors,
    }

    if strict and errors:
        raise ValidationError("; ".join(errors))
    return result
