"""Mission operations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.models import milestone_stub, mission_routing_stub, mission_stub, worktree_map_stub
from csk_next.domain.state import ensure_registry, find_module
from csk_next.io.files import ensure_dir, read_json, write_json, write_text
from csk_next.runtime.ids import next_mission_id
from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.paths import Layout
from csk_next.runtime.tasks_engine import task_new
from csk_next.runtime.time import utc_now_iso
from csk_next.runtime.worktrees import create_module_worktree


def mission_new(
    *,
    layout: Layout,
    title: str,
    summary: str,
    module_ids: list[str],
    create_worktrees: bool,
    create_task_stubs: bool,
    profile: str,
) -> dict[str, Any]:
    if not module_ids:
        raise ValueError("mission requires at least one module")

    registry = ensure_registry(layout.registry)
    validated_modules = [find_module(registry, module_id) for module_id in module_ids]
    mission_id = next_mission_id(layout.missions)
    mission_dir = layout.missions / mission_id
    ensure_dir(mission_dir)

    mission = mission_stub(mission_id, title, summary)
    write_json(mission_dir / "mission.json", mission)
    write_text(mission_dir / "spec.md", f"# {title}\n\n{summary}\n")

    routing = mission_routing_stub(mission_id, module_ids)
    write_json(mission_dir / "routing.json", routing)

    milestones = milestone_stub(mission_id)
    milestones["milestones"][0]["module_items"] = module_ids
    write_json(mission_dir / "milestones.json", milestones)

    worktrees = worktree_map_stub(mission_id)
    worktrees["create_status"] = {}
    if create_worktrees:
        for module_id in module_ids:
            worktree_info = create_module_worktree(
                repo_root=layout.root,
                mission_id=mission_id,
                module_id=module_id,
            )
            worktrees["module_worktrees"][module_id] = str(worktree_info["path"])
            worktrees["create_status"][module_id] = {
                "created": bool(worktree_info["created"]),
                "branch": str(worktree_info["branch"]),
                "fallback_reason": worktree_info["fallback_reason"],
            }
            if not bool(worktree_info["created"]):
                worktrees["opt_out_modules"].append(module_id)
                incident = make_incident(
                    severity="medium",
                    kind="worktree_create_failed",
                    phase="routing",
                    module_id=module_id,
                    message=f"Worktree not created for module {module_id}",
                    remediation="Continue with controlled no-worktree mode or create worktree manually.",
                    context={
                        "mission_id": mission_id,
                        "stderr": worktree_info["stderr"],
                        "fallback_reason": worktree_info["fallback_reason"],
                    },
                )
                log_incident(layout.app_incidents, incident)
    else:
        for module_id in module_ids:
            worktrees["module_worktrees"][module_id] = str(
                (layout.root / ".csk" / "worktrees" / mission_id / module_id).as_posix()
            )
            worktrees["opt_out_modules"].append(module_id)
            worktrees["create_status"][module_id] = {
                "created": False,
                "branch": f"csk/{mission_id}/{module_id}",
                "fallback_reason": "user_opt_out",
            }
    write_json(mission_dir / "worktrees.json", worktrees)

    tasks: list[dict[str, Any]] = []
    if create_task_stubs:
        for module in validated_modules:
            module_id = module["module_id"]
            result = task_new(
                layout=layout,
                module_id=module_id,
                module_path=module["path"],
                mission_id=mission_id,
                profile=profile,
                max_attempts=2,
                plan_template=f"# Plan for {module_id} in {mission_id}\n\n## Goal\n- TODO\n",
            )
            tasks.append(result)

    return {
        "status": "ok",
        "mission_id": mission_id,
        "path": str(mission_dir),
        "tasks_created": [task["task_id"] for task in tasks],
    }


def mission_status(*, layout: Layout, mission_id: str) -> dict[str, Any]:
    mission_dir = layout.missions / mission_id
    if not mission_dir.exists():
        raise FileNotFoundError(f"Mission not found: {mission_id}")

    mission = read_json(mission_dir / "mission.json")
    routing = read_json(mission_dir / "routing.json")
    milestones = read_json(mission_dir / "milestones.json")
    return {
        "status": "ok",
        "mission": mission,
        "routing": routing,
        "milestones": milestones,
    }


def spawn_milestone(
    *,
    layout: Layout,
    mission_id: str,
    title: str,
    module_items: list[str],
    depends_on: list[str],
    parallel_groups: list[list[str]],
    integration_checks: list[str],
) -> dict[str, Any]:
    mission_dir = layout.missions / mission_id
    milestones_path = mission_dir / "milestones.json"
    doc = read_json(milestones_path)

    existing = doc.get("milestones", [])
    milestone_id = f"MS-{len(existing) + 1:04d}"
    existing.append(
        {
            "milestone_id": milestone_id,
            "title": title,
            "status": "draft",
            "module_items": module_items,
            "depends_on": depends_on,
            "parallel_groups": parallel_groups,
            "integration_checks": integration_checks,
        }
    )
    doc["milestones"] = existing
    doc["updated_at"] = utc_now_iso()
    write_json(milestones_path, doc)

    return {"status": "ok", "milestone_id": milestone_id}
