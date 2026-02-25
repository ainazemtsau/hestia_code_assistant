"""Status projections for root and module dashboards."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import tail_events
from csk_next.io.files import read_json
from csk_next.runtime.paths import Layout


_PHASE_BY_TASK_STATUS: dict[str, str] = {
    "draft": "PLANNING",
    "critic_passed": "PLANNING",
    "frozen": "PLAN_FROZEN",
    "plan_approved": "EXECUTING",
    "executing": "EXECUTING",
    "ready_validated": "READY_VALIDATED",
    "ready_approved": "RETRO_REQUIRED",
    "blocked": "BLOCKED",
    "retro_done": "RETRO_DONE",
    "closed": "CLOSED",
}


def _bootstrapped(layout: Layout) -> bool:
    return layout.engine.exists() and layout.local.exists() and layout.registry.exists()


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return read_json(path)
    except Exception:  # noqa: BLE001
        return None


def _task_sort_key(state: dict[str, Any]) -> tuple[str, str]:
    return (str(state.get("updated_at", "")), str(state.get("task_id", "")))


def _collect_task_states(layout: Layout, module_path: str) -> list[dict[str, Any]]:
    tasks_root = layout.module_tasks(module_path)
    if not tasks_root.exists():
        return []

    states: list[dict[str, Any]] = []
    for task_dir in sorted(entry for entry in tasks_root.iterdir() if entry.is_dir()):
        task_state = _safe_read_json(task_dir / "task.json")
        if not task_state:
            continue
        states.append(task_state)
    return sorted(states, key=_task_sort_key, reverse=True)


def _active_task_state(states: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not states:
        return None
    for state in states:
        if str(state.get("status", "")) not in {"closed", "retro_done"}:
            return state
    return states[0]


def _active_slice_id(task_state: dict[str, Any] | None) -> str | None:
    if task_state is None:
        return None
    slices = task_state.get("slices", {})
    if not isinstance(slices, dict):
        return None
    for slice_id in sorted(slices):
        slice_state = slices.get(slice_id, {})
        if not isinstance(slice_state, dict):
            continue
        if str(slice_state.get("status", "pending")) != "done":
            return str(slice_id)
    return None


def _mission_sort_key(mission_row: dict[str, Any]) -> tuple[str, str]:
    return (str(mission_row.get("updated_at", "")), str(mission_row.get("mission_id", "")))


def _collect_missions(layout: Layout) -> list[dict[str, Any]]:
    if not layout.missions.exists():
        return []
    rows: list[dict[str, Any]] = []
    for mission_dir in sorted(entry for entry in layout.missions.iterdir() if entry.is_dir()):
        mission = _safe_read_json(mission_dir / "mission.json")
        if not mission:
            continue
        milestones = _safe_read_json(mission_dir / "milestones.json") or {}
        active_milestone = None
        for milestone in milestones.get("milestones", []):
            if str(milestone.get("status", "")) == "active":
                active_milestone = milestone
                break
        if active_milestone is None and milestones.get("milestones"):
            active_milestone = milestones["milestones"][0]
        rows.append(
            {
                "mission_id": str(mission.get("mission_id", mission_dir.name)),
                "status": str(mission.get("status", "draft")),
                "updated_at": str(mission.get("updated_at", mission.get("created_at", ""))),
                "active_milestone_id": (
                    str(active_milestone.get("milestone_id")) if isinstance(active_milestone, dict) else None
                ),
            }
        )
    return sorted(rows, key=_mission_sort_key, reverse=True)


def _active_mission(layout: Layout) -> dict[str, Any] | None:
    missions = _collect_missions(layout)
    if not missions:
        return None
    for mission in missions:
        if mission["status"] in {"draft", "active", "milestone_done", "ready"}:
            return mission
    return missions[0]


def _worktree_map(layout: Layout, mission_id: str | None) -> dict[str, str]:
    if mission_id is None:
        return {}
    worktrees_doc = _safe_read_json(layout.missions / mission_id / "worktrees.json")
    if not worktrees_doc:
        return {}
    module_worktrees = worktrees_doc.get("module_worktrees", {})
    if isinstance(module_worktrees, dict):
        return {str(key): str(value) for key, value in module_worktrees.items()}
    return {}


def _module_projection(layout: Layout, module_row: dict[str, Any], worktrees: dict[str, str]) -> dict[str, Any]:
    module_id = str(module_row["module_id"])
    module_path = str(module_row["path"])
    task_states = _collect_task_states(layout, module_path)
    active = _active_task_state(task_states)
    task_status = str(active.get("status")) if active else None
    phase = _PHASE_BY_TASK_STATUS.get(task_status or "", "IDLE")
    projection = {
        "module_id": module_id,
        "path": module_path,
        "phase": phase,
        "active_task_id": str(active["task_id"]) if active else None,
        "active_slice_id": _active_slice_id(active),
        "task_status": task_status,
        "blocked_reason": str(active.get("blocked_reason")) if active and active.get("blocked_reason") else None,
        "worktree_path": worktrees.get(module_id),
    }
    return projection


def _status_next(modules: list[dict[str, Any]], mission: dict[str, Any] | None, bootstrapped: bool) -> dict[str, Any]:
    if not bootstrapped:
        return {"recommended": "csk bootstrap", "alternatives": ["csk status --json"]}

    for module in modules:
        if module["phase"] == "PLAN_FROZEN" and module["active_task_id"]:
            task_id = module["active_task_id"]
            module_id = module["module_id"]
            return {
                "recommended": (
                    f"csk task approve-plan --module-id {module_id} --task-id {task_id} --approved-by <human>"
                ),
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    for module in modules:
        if module["phase"] == "PLANNING" and module["active_task_id"]:
            task_id = module["active_task_id"]
            module_id = module["module_id"]
            if module.get("task_status") == "critic_passed":
                recommended = f"csk task freeze --module-id {module_id} --task-id {task_id}"
            else:
                recommended = f"csk task critic --module-id {module_id} --task-id {task_id}"
            return {
                "recommended": recommended,
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    for module in modules:
        if module["phase"] == "EXECUTING" and module["active_task_id"]:
            task_id = module["active_task_id"]
            slice_id = module["active_slice_id"] or "S-0001"
            module_id = module["module_id"]
            return {
                "recommended": f"csk slice run --module-id {module_id} --task-id {task_id} --slice-id {slice_id}",
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    for module in modules:
        if module["phase"] == "READY_VALIDATED" and module["active_task_id"]:
            task_id = module["active_task_id"]
            module_id = module["module_id"]
            return {
                "recommended": (
                    f"csk gate approve-ready --module-id {module_id} --task-id {task_id} --approved-by <human>"
                ),
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    for module in modules:
        if module["phase"] == "RETRO_REQUIRED" and module["active_task_id"]:
            task_id = module["active_task_id"]
            module_id = module["module_id"]
            return {
                "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    for module in modules:
        if module["phase"] == "BLOCKED" and module["active_task_id"]:
            task_id = module["active_task_id"]
            module_id = module["module_id"]
            return {
                "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
                "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
            }

    if mission is None:
        return {"recommended": "csk run", "alternatives": ["csk mission new --help", "csk module list"]}

    return {"recommended": "csk run", "alternatives": ["csk module list", "csk event tail --n 20"]}


def project_root_status(layout: Layout) -> dict[str, Any]:
    bootstrapped = _bootstrapped(layout)
    registry = ensure_registry(layout.registry) if bootstrapped else {"modules": []}
    mission = _active_mission(layout) if bootstrapped else None
    worktrees = _worktree_map(layout, mission["mission_id"] if mission else None)
    modules = [_module_projection(layout, row, worktrees) for row in registry["modules"]]
    latest_events = tail_events(layout=layout, n=1)
    next_block = _status_next(modules, mission, bootstrapped)

    return {
        "status": "ok",
        "summary": {
            "bootstrapped": bootstrapped,
            "active_mission_id": mission["mission_id"] if mission else None,
            "active_milestone_id": mission["active_milestone_id"] if mission else None,
            "modules_total": len(modules),
        },
        "modules": modules,
        "latest_event": latest_events[0] if latest_events else None,
        "next": next_block,
    }


def _module_next(module_projection: dict[str, Any]) -> dict[str, Any]:
    module_id = module_projection["module_id"]
    task_id = module_projection["active_task_id"]
    phase = module_projection["phase"]
    if phase == "PLANNING" and task_id:
        if module_projection.get("task_status") == "critic_passed":
            recommended = f"csk task freeze --module-id {module_id} --task-id {task_id}"
        else:
            recommended = f"csk task critic --module-id {module_id} --task-id {task_id}"
        return {
            "recommended": recommended,
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    if phase == "PLAN_FROZEN" and task_id:
        return {
            "recommended": f"csk task approve-plan --module-id {module_id} --task-id {task_id} --approved-by <human>",
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    if phase == "EXECUTING" and task_id:
        slice_id = module_projection["active_slice_id"] or "S-0001"
        return {
            "recommended": f"csk slice run --module-id {module_id} --task-id {task_id} --slice-id {slice_id}",
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    if phase == "READY_VALIDATED" and task_id:
        return {
            "recommended": f"csk gate approve-ready --module-id {module_id} --task-id {task_id} --approved-by <human>",
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    if phase == "RETRO_REQUIRED" and task_id:
        return {
            "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    if phase == "BLOCKED" and task_id:
        return {
            "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk task status --module-id {module_id} --task-id {task_id}"],
        }
    return {"recommended": "csk run", "alternatives": ["csk module list"]}


def project_module_status(layout: Layout, module_id: str) -> dict[str, Any]:
    root_projection = project_root_status(layout)
    registry = ensure_registry(layout.registry)
    module_row = find_module(registry, module_id)
    module_proj = None
    for row in root_projection["modules"]:
        if row["module_id"] == module_id:
            module_proj = row
            break
    if module_proj is None:
        module_proj = {
            "module_id": module_id,
            "path": module_row["path"],
            "phase": "IDLE",
            "active_task_id": None,
            "active_slice_id": None,
            "task_status": None,
            "blocked_reason": None,
            "worktree_path": None,
        }

    return {
        "status": "ok",
        "module": module_proj,
        "cd_hint": f"cd {module_proj['worktree_path']}" if module_proj.get("worktree_path") else None,
        "next": _module_next(module_proj),
    }
