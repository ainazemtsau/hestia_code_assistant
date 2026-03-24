"""Status and NEXT computation."""

from __future__ import annotations

from pathlib import Path

from pfpkg.focus import get_focus
from pfpkg.projections import (
    active_mission,
    last_incidents,
    last_verify,
    modules_summary,
    stale_docs_count,
    task_state,
    task_workflow,
)


def compute_next(
    *,
    is_initialized: bool,
    active_mission_id: str | None,
    focus_module: str | None,
    focus_task: dict | None,
) -> dict:
    if not is_initialized:
        return {
            "kind": "cli",
            "cmd": "pf init",
            "why": "initialize PowerFlow in this repo",
        }
    if focus_task:
        state = focus_task["state"]
        if state in {"NEW", "PLANNING", "BLOCKED"} or not focus_task["plan_approved"]:
            return {
                "kind": "skill",
                "cmd": "$pf-planner",
                "why": "create or refine the plan for the focused task",
            }
        if state == "DONE":
            return {
                "kind": "skill",
                "cmd": "$pf-intake",
                "why": "current task is done; capture the next request",
            }
        return {
            "kind": "skill",
            "cmd": "$pf-executor",
            "why": "execute approved task slices using bounded context",
        }

    if focus_module:
        return {
            "kind": "skill",
            "cmd": "$pf-planner",
            "why": "create an executable plan for this module",
        }

    if not active_mission_id:
        return {
            "kind": "skill",
            "cmd": "$pf-intake",
            "why": "capture the next request and route it to modules",
        }
    return {
        "kind": "cli",
        "cmd": "pf module list",
        "why": "pick a module to work on",
    }


def build_status(conn, db_path: Path) -> dict:
    is_init = db_path.exists()
    if not is_init:
        next_action = compute_next(
            is_initialized=False,
            active_mission_id=None,
            focus_module=None,
            plan_approved=False,
        )
        return {
            "initialized": False,
            "active_mission": None,
            "focus": {"module_id": None, "task_id": None, "worktree_id": None},
            "modules": [],
            "incidents": [],
            "stale_docs_count": 0,
            "next": next_action,
        }

    focus = get_focus(conn)
    mission = active_mission(conn)
    mod_list = modules_summary(conn)

    module_id = focus.get("module_id")
    flow = task_workflow(conn, focus.get("task_id"))
    next_action = compute_next(
        is_initialized=True,
        active_mission_id=mission["mission_id"] if mission else None,
        focus_module=module_id,
        focus_task=flow,
    )

    t_state = task_state(conn, focus.get("task_id"))

    return {
        "initialized": True,
        "active_mission": mission,
        "focus": focus,
        "focus_task_state": t_state,
        "modules": mod_list,
        "incidents": last_incidents(conn, limit=3),
        "stale_docs_count": stale_docs_count(conn),
        "plan_approved": bool(flow["plan_approved"]) if flow else False,
        "focus_task_flow": flow,
        "last_verify": last_verify(conn),
        "next": next_action,
    }


def render_status_human(status_data: dict) -> list[str]:
    lines: list[str] = []
    if not status_data["initialized"]:
        lines.extend(
            [
                "PowerFlow status: NOT INITIALIZED",
                "Init: no",
                "",
                f"NEXT (CLI): {status_data['next']['cmd']}",
                f"WHY: {status_data['next']['why']}",
            ]
        )
        return lines

    mission = status_data["active_mission"]
    focus = status_data["focus"]
    mods = status_data["modules"]
    mod_names = ", ".join(m["module_id"] for m in mods[:3])

    lines.append("PowerFlow status: OK")
    lines.append("Init: yes")
    lines.append(f"Active mission: {mission['mission_id'] if mission else 'none'}")
    lines.append(f"Focus module: {focus.get('module_id') or 'none'}")
    lines.append(f"Modules: {len(mods)} ({mod_names})")

    if focus.get("module_id"):
        lines.append(f"Plan approved: {'yes' if status_data['plan_approved'] else 'no'}")

    lines.append(f"Docs stale: {status_data['stale_docs_count']}")

    incidents = status_data["incidents"]
    if incidents:
        lines.append("Recent incidents:")
        for item in incidents:
            lines.append(f"- [{item['event_id']}] {item['summary']}")

    next_action = status_data["next"]
    label = "CLI" if next_action["kind"] == "cli" else "Codex"
    lines.extend(["", f"NEXT ({label}): {next_action['cmd']}", f"WHY: {next_action['why']}"])
    return lines
