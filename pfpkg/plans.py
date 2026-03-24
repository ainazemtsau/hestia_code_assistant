"""Plan and slices commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pfpkg.artifacts import put_artifact
from pfpkg.errors import EXIT_NOT_FOUND, EXIT_VALIDATION, PfError
from pfpkg.events import append_event
from pfpkg.ids import next_slice_id
from pfpkg.templates_store import load_template
from pfpkg.validation import ensure_safe_module_id_or_raise, validate_module_id_strict


def _module_exists(conn, module_id: str) -> None:
    ensure_safe_module_id_or_raise(module_id, source="plan command module_id")
    cur = conn.execute("SELECT 1 FROM modules WHERE module_id=?", (module_id,))
    if cur.fetchone() is None:
        raise PfError(f"module not found: {module_id}", EXIT_NOT_FOUND)


def _validate_task_scope(conn, task_id: str, module_id: str) -> None:
    cur = conn.execute(
        """
        SELECT scope_id AS module_id
        FROM events
        WHERE type='task.created' AND task_id=?
        ORDER BY event_id ASC
        LIMIT 1
        """,
        (task_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise PfError(f"task not found: {task_id}", EXIT_NOT_FOUND)
    if row["module_id"] != module_id:
        raise PfError(
            f"task {task_id} belongs to module {row['module_id']}, not {module_id}",
            EXIT_VALIDATION,
        )


def mark_plan_saved(conn, repo_root: Path, *, module_id: str, task_id: str | None = None) -> dict:
    module_id = validate_module_id_strict(module_id)
    _module_exists(conn, module_id)
    if task_id:
        _validate_task_scope(conn, task_id, module_id)
    plan_rel = f".pf/modules/{module_id}/PLAN.md"
    plan_path = repo_root / plan_rel
    if not plan_path.exists():
        raise PfError(f"plan file not found: {plan_rel}", EXIT_NOT_FOUND)

    plan_artifact = put_artifact(conn, repo_root, kind="plan", path_value=plan_rel)
    slices_artifact_id = None
    slices_rel = f".pf/modules/{module_id}/SLICES.json"
    if (repo_root / slices_rel).exists():
        slices_artifact = put_artifact(conn, repo_root, kind="plan", path_value=slices_rel)
        slices_artifact_id = slices_artifact["artifact_id"]

    artifact_ids = [plan_artifact["artifact_id"]]
    if slices_artifact_id is not None:
        artifact_ids.append(slices_artifact_id)

    event_id = append_event(
        conn,
        event_type="plan.saved",
        scope_type="module",
        scope_id=module_id,
        task_id=task_id,
        actor="assistant",
        summary=f"plan saved for {module_id}",
        payload={
            "module_id": module_id,
            "task_id": task_id,
            "plan_artifact_id": plan_artifact["artifact_id"],
            "slices_artifact_id": slices_artifact_id,
        },
        artifact_ids=artifact_ids,
    )

    if task_id:
        append_event(
            conn,
            event_type="task.state_changed",
            scope_type="module",
            scope_id=module_id,
            task_id=task_id,
            actor="assistant",
            summary=f"task {task_id} -> PLANNING",
            payload={"task_id": task_id, "new_state": "PLANNING"},
        )

    return {
        "event_id": event_id,
        "plan_artifact_id": plan_artifact["artifact_id"],
        "slices_artifact_id": slices_artifact_id,
    }


def approve_plan(conn, *, module_id: str, task_id: str | None = None, note: str = "approved") -> dict:
    module_id = validate_module_id_strict(module_id)
    _module_exists(conn, module_id)
    if task_id:
        _validate_task_scope(conn, task_id, module_id)
    event_id = append_event(
        conn,
        event_type="plan.approved",
        scope_type="module",
        scope_id=module_id,
        task_id=task_id,
        actor="user",
        summary=f"plan approved for {module_id}",
        payload={"module_id": module_id, "task_id": task_id, "note": note},
    )
    if task_id:
        append_event(
            conn,
            event_type="task.state_changed",
            scope_type="module",
            scope_id=module_id,
            task_id=task_id,
            actor="assistant",
            summary=f"task {task_id} -> PLAN_APPROVED",
            payload={"task_id": task_id, "new_state": "PLAN_APPROVED"},
        )
    return {"event_id": event_id, "module_id": module_id, "task_id": task_id}


def _load_slices(path: Path, template_text: str) -> dict[str, Any]:
    if not path.exists():
        return json.loads(template_text)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PfError(f"invalid json in SLICES file: {path}", EXIT_VALIDATION) from exc
    if not isinstance(data, dict):
        raise PfError("SLICES.json must be an object", EXIT_VALIDATION)
    if "slices" not in data or not isinstance(data["slices"], list):
        raise PfError("SLICES.json must have array field 'slices'", EXIT_VALIDATION)
    return data


def create_slice(
    conn,
    repo_root: Path,
    *,
    task_id: str,
    title: str,
    allowed_paths: list[str],
    verify: list[str] | None = None,
) -> dict:
    cur = conn.execute(
        "SELECT scope_id AS module_id FROM events WHERE task_id=? ORDER BY event_id ASC LIMIT 1",
        (task_id,),
    )
    row = cur.fetchone()
    if row is None:
        raise PfError(f"task not found: {task_id}", EXIT_NOT_FOUND)
    module_id = ensure_safe_module_id_or_raise(str(row["module_id"]), source="task.created scope_id")

    rel = f".pf/modules/{module_id}/SLICES.json"
    path = repo_root / rel
    template = load_template(repo_root, "SLICES.json.template")
    payload = _load_slices(path, template)

    slice_id = next_slice_id(conn)
    entry = {
        "slice_id": slice_id,
        "task_id": task_id,
        "title": title,
        "allowed_paths": allowed_paths,
        "verify": verify or [],
    }
    payload.setdefault("version", 1)
    payload.setdefault("slices", [])
    payload["slices"].append(entry)
    payload["slices"] = sorted(payload["slices"], key=lambda x: x["slice_id"])

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    append_event(
        conn,
        event_type="slice.created",
        scope_type="module",
        scope_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        actor="assistant",
        summary=f"slice created: {title}",
        payload=entry,
    )

    return {"module_id": module_id, "task_id": task_id, "slice": entry, "path": rel}


def validate_slices(repo_root: Path, module_id: str) -> dict:
    module_id = validate_module_id_strict(module_id)
    path = repo_root / ".pf" / "modules" / module_id / "SLICES.json"
    if not path.exists():
        raise PfError(f"SLICES.json not found for module {module_id}", EXIT_NOT_FOUND)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PfError("SLICES.json is not valid JSON", EXIT_VALIDATION) from exc

    if not isinstance(payload, dict):
        raise PfError("SLICES.json must be an object", EXIT_VALIDATION)

    slices = payload.get("slices")
    if not isinstance(slices, list):
        raise PfError("SLICES.json missing slices array", EXIT_VALIDATION)

    problems: list[str] = []
    for index, item in enumerate(slices, start=1):
        if not isinstance(item, dict):
            problems.append(f"slice #{index} must be object")
            continue
        if not item.get("slice_id"):
            problems.append(f"slice #{index} missing slice_id")
        if not item.get("task_id"):
            problems.append(f"slice #{index} missing task_id")
        allowed = item.get("allowed_paths")
        if not isinstance(allowed, list) or not allowed:
            problems.append(f"slice #{index} must have non-empty allowed_paths")

    return {"ok": len(problems) == 0, "problems": problems, "slice_count": len(slices)}
