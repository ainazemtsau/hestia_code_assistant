"""Task commands."""

from __future__ import annotations

from pathlib import Path

from pfpkg.artifacts import put_artifact
from pfpkg.errors import EXIT_NOT_FOUND, EXIT_VALIDATION, PfError
from pfpkg.events import append_event
from pfpkg.focus import set_focus_task
from pfpkg.ids import next_task_id
from pfpkg.templates_store import load_template
from pfpkg.util_fs import ensure_dir
from pfpkg.validation import ensure_safe_module_id_or_raise, validate_module_id_strict

VALID_TASK_STATES = {
    "NEW",
    "PLANNING",
    "PLAN_APPROVED",
    "EXECUTING",
    "READY",
    "DONE",
    "BLOCKED",
}


def create_task(conn, repo_root: Path, *, module_id: str, title: str, mission_id: str | None = None) -> dict:
    module_id = validate_module_id_strict(module_id)
    cur = conn.execute("SELECT module_id, root_path FROM modules WHERE module_id=?", (module_id,))
    module_row = cur.fetchone()
    if module_row is None:
        raise PfError(f"module not found: {module_id}", EXIT_NOT_FOUND)

    task_id = next_task_id(conn)
    tasks_dir = repo_root / ".pf" / "modules" / module_id / "TASKS"
    ensure_dir(tasks_dir)

    rel_path = f".pf/modules/{module_id}/TASKS/{task_id}.md"
    template = load_template(repo_root, "task.md.template")
    content = (
        template.replace("<task_id>", task_id)
        .replace("...", title, 1)
        .replace("module_id: ...", f"module_id: {module_id}")
        .replace("root_path: ...", f"root_path: {module_row['root_path']}")
    )
    (repo_root / rel_path).write_text(content, encoding="utf-8")

    artifact = put_artifact(conn, repo_root, kind="plan", path_value=rel_path)

    append_event(
        conn,
        event_type="task.created",
        scope_type="module",
        scope_id=module_id,
        mission_id=mission_id,
        task_id=task_id,
        actor="assistant",
        summary=f"task created: {title}",
        payload={
            "task_id": task_id,
            "module_id": module_id,
            "title": title,
            "mission_id": mission_id,
            "task_path": rel_path,
        },
        artifact_ids=[artifact["artifact_id"]],
    )

    append_event(
        conn,
        event_type="task.state_changed",
        scope_type="module",
        scope_id=module_id,
        mission_id=mission_id,
        task_id=task_id,
        actor="assistant",
        summary=f"task {task_id} -> NEW",
        payload={"task_id": task_id, "new_state": "NEW"},
    )

    set_focus_task(conn, module_id, task_id)

    return {
        "task_id": task_id,
        "module_id": module_id,
        "title": title,
        "mission_id": mission_id,
        "path": rel_path,
    }


def set_task_state(conn, *, task_id: str, state: str, actor: str = "assistant") -> dict:
    state = state.upper()
    if state not in VALID_TASK_STATES:
        raise PfError(f"invalid task state: {state}", EXIT_VALIDATION)

    cur = conn.execute(
        "SELECT scope_id AS module_id, mission_id FROM events WHERE task_id=? ORDER BY event_id ASC LIMIT 1",
        (task_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise PfError(f"task not found: {task_id}", EXIT_NOT_FOUND)
    module_id = ensure_safe_module_id_or_raise(row["module_id"], source="task.state_changed event scope")

    event_id = append_event(
        conn,
        event_type="task.state_changed",
        scope_type="module",
        scope_id=module_id,
        mission_id=row["mission_id"],
        task_id=task_id,
        actor=actor,
        summary=f"task {task_id} -> {state}",
        payload={"task_id": task_id, "new_state": state},
    )
    return {"task_id": task_id, "state": state, "event_id": event_id}
