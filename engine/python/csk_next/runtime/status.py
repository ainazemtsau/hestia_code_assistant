"""Status projections for root and module dashboards."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import tail_events
from csk_next.io.files import read_json
from csk_next.runtime.paths import Layout
from csk_next.skills.generator import validate_generated_skills


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

_PHASE_PRIORITY: dict[str, int] = {
    "BLOCKED": 0,
    "PLAN_FROZEN": 1,
    "READY_VALIDATED": 2,
    "RETRO_REQUIRED": 3,
    "EXECUTING": 4,
    "PLANNING": 5,
    "IDLE": 6,
    "RETRO_DONE": 7,
    "CLOSED": 8,
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
    slices_total = 0
    slices_done = 0
    if active:
        slices = active.get("slices", {})
        if isinstance(slices, dict):
            slices_total = len(slices)
            slices_done = sum(1 for row in slices.values() if isinstance(row, dict) and row.get("status") == "done")
    active_task_id = str(active["task_id"]) if active else None
    projection = {
        "module_id": module_id,
        "path": module_path,
        "initialized": bool(module_row.get("initialized", False)),
        "phase": phase,
        "active_task_id": active_task_id,
        "active_task_updated_at": str(active.get("updated_at")) if active else None,
        "active_slice_id": _active_slice_id(active),
        "slices_done": slices_done,
        "slices_total": slices_total,
        "task_status": task_status,
        "blocked_reason": str(active.get("blocked_reason")) if active and active.get("blocked_reason") else None,
        "worktree_path": worktrees.get(module_id),
        "active_plan_path": (
            str(layout.module_tasks(module_path) / active_task_id / "plan.md") if active_task_id is not None else None
        ),
        "active_slices_path": (
            str(layout.module_tasks(module_path) / active_task_id / "slices.json")
            if active_task_id is not None
            else None
        ),
    }
    return projection


def _active_module(modules: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not modules:
        return None

    best: dict[str, Any] | None = None
    best_rank = 10**9
    best_updated = ""
    best_module_id = ""
    for module in modules:
        rank = _PHASE_PRIORITY.get(str(module.get("phase", "")), 10**9)
        updated = str(module.get("active_task_updated_at") or "")
        module_id = str(module.get("module_id", ""))
        if best is None:
            best = module
            best_rank = rank
            best_updated = updated
            best_module_id = module_id
            continue
        if rank < best_rank:
            best = module
            best_rank = rank
            best_updated = updated
            best_module_id = module_id
            continue
        if rank == best_rank and updated > best_updated:
            best = module
            best_updated = updated
            best_module_id = module_id
            continue
        if rank == best_rank and updated == best_updated and module_id < best_module_id:
            best = module
            best_module_id = module_id
    return best


def _tasks_by_status(layout: Layout, modules: list[dict[str, Any]]) -> dict[str, int]:
    counters: dict[str, int] = defaultdict(int)
    for module in modules:
        for state in _collect_task_states(layout, str(module["path"])):
            task_status = str(state.get("status", "unknown"))
            counters[task_status] = counters[task_status] + 1
    return dict(sorted(counters.items(), key=lambda item: item[0]))


def _proof_manifest_count(layout: Layout, modules: list[dict[str, Any]]) -> int:
    total = 0
    for module in modules:
        task_runs = layout.module_run(str(module["path"])) / "tasks"
        if not task_runs.exists():
            continue
        total += sum(1 for path in task_runs.rglob("manifest.json") if path.is_file())
    return total


def _retro_count(layout: Layout, modules: list[dict[str, Any]]) -> int:
    total = 0
    for module in modules:
        module_path = str(module["path"])
        for state in _collect_task_states(layout, module_path):
            task_id = state.get("task_id")
            if isinstance(task_id, str) and (layout.module_tasks(module_path) / task_id / "retro.md").exists():
                total += 1
    return total


def _project_phase(bootstrapped: bool, skills: dict[str, Any], active_module: dict[str, Any] | None) -> str:
    if not bootstrapped:
        return "BOOTSTRAP_REQUIRED"
    if str(skills.get("status")) != "ok":
        return "SKILLS_DRIFT"
    if active_module is None:
        return "IDLE"
    return str(active_module.get("phase", "IDLE"))


def _skills_projection(layout: Layout, bootstrapped: bool) -> dict[str, Any]:
    if not bootstrapped:
        return {
            "status": "failed",
            "missing": [],
            "modified": [],
            "stale": [],
            "recommended": "csk bootstrap",
        }
    check = validate_generated_skills(
        engine_skills_src=layout.engine / "skills_src",
        local_override=layout.local / "skills_override",
        output_dir=layout.agents_skills,
    )
    status = str(check.get("status", "failed"))
    return {
        "status": status,
        "missing": list(check.get("missing", [])),
        "modified": list(check.get("modified", [])),
        "stale": list(check.get("stale", [])),
        "recommended": "csk skills generate" if status != "ok" else None,
    }


def _status_next(
    modules: list[dict[str, Any]],
    active_module: dict[str, Any] | None,
    bootstrapped: bool,
    skills: dict[str, Any],
) -> dict[str, Any]:
    if not bootstrapped:
        return {"recommended": "csk bootstrap", "alternatives": ["csk status --json"]}

    if str(skills.get("status")) != "ok":
        return {
            "recommended": str(skills.get("recommended") or "csk skills generate"),
            "alternatives": ["csk status --json"],
        }

    if active_module is None:
        return {"recommended": "csk run", "alternatives": ["csk new \"<request>\" --modules <id>", "csk status --json"]}

    module_id = str(active_module["module_id"])
    task_id = active_module.get("active_task_id")
    phase = str(active_module.get("phase", "IDLE"))

    if phase in {"PLAN_FROZEN", "READY_VALIDATED"} and task_id:
        return {
            "recommended": f"csk approve --module-id {module_id} --task-id {task_id} --approved-by <human>",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if phase in {"RETRO_REQUIRED", "BLOCKED"} and task_id:
        return {
            "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if phase in {"PLANNING", "EXECUTING"}:
        return {"recommended": "csk run", "alternatives": [f"csk module {module_id}", "csk status --json"]}
    return {"recommended": "csk run", "alternatives": ["csk status --json"]}


def project_root_status(layout: Layout) -> dict[str, Any]:
    bootstrapped = _bootstrapped(layout)
    registry = ensure_registry(layout.registry) if bootstrapped else {"modules": []}
    mission = _active_mission(layout) if bootstrapped else None
    worktrees = _worktree_map(layout, mission["mission_id"] if mission else None)
    modules = [_module_projection(layout, row, worktrees) for row in registry["modules"]]
    latest_events = tail_events(layout=layout, n=1)
    skills = _skills_projection(layout, bootstrapped)
    active_module = _active_module(modules)
    project_phase = _project_phase(bootstrapped, skills, active_module)
    counters = {
        "tasks_by_status": _tasks_by_status(layout, registry["modules"]) if bootstrapped else {},
        "proof_packs_total": _proof_manifest_count(layout, registry["modules"]) if bootstrapped else 0,
        "retro_total": _retro_count(layout, registry["modules"]) if bootstrapped else 0,
    }
    next_block = _status_next(modules, active_module, bootstrapped, skills)

    return {
        "status": "ok",
        "project_phase": project_phase,
        "summary": {
            "bootstrapped": bootstrapped,
            "project_phase": project_phase,
            "active_mission_id": mission["mission_id"] if mission else None,
            "active_milestone_id": mission["active_milestone_id"] if mission else None,
            "active_module_id": active_module["module_id"] if active_module else None,
            "active_task_id": active_module["active_task_id"] if active_module else None,
            "active_slice_id": active_module["active_slice_id"] if active_module else None,
            "modules_total": len(modules),
            "counters": counters,
        },
        "counters": counters,
        "modules": modules,
        "skills": skills,
        "latest_event": latest_events[0] if latest_events else None,
        "next": next_block,
    }


def _module_next(module_projection: dict[str, Any]) -> dict[str, Any]:
    module_id = module_projection["module_id"]
    task_id = module_projection["active_task_id"]
    phase = module_projection["phase"]
    if phase in {"PLAN_FROZEN", "READY_VALIDATED"} and task_id:
        return {
            "recommended": f"csk approve --module-id {module_id} --task-id {task_id} --approved-by <human>",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if phase in {"RETRO_REQUIRED", "BLOCKED"} and task_id:
        return {
            "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if phase in {"PLANNING", "EXECUTING"}:
        return {
            "recommended": "csk run",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    return {"recommended": "csk run", "alternatives": ["csk status --json"]}


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
            "initialized": bool(module_row.get("initialized", False)),
            "phase": "IDLE",
            "active_task_id": None,
            "active_task_updated_at": None,
            "active_slice_id": None,
            "slices_done": 0,
            "slices_total": 0,
            "task_status": None,
            "blocked_reason": None,
            "worktree_path": None,
            "active_plan_path": None,
            "active_slices_path": None,
        }

    return {
        "status": "ok",
        "module": module_proj,
        "cd_hint": f"cd {module_proj['worktree_path']}" if module_proj.get("worktree_path") else None,
        "next": _module_next(module_proj),
    }
