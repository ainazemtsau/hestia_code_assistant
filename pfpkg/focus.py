"""Focus helpers."""

from __future__ import annotations

from pfpkg.errors import EXIT_NOT_FOUND, PfError
from pfpkg.events import append_event
from pfpkg.util_time import utc_now_iso
from pfpkg.validation import ensure_safe_module_id_or_raise, validate_module_id_strict


def get_focus(conn) -> dict:
    cur = conn.execute("SELECT module_id, task_id, worktree_id, updated_ts FROM focus WHERE id=1")
    row = cur.fetchone()
    if row is None:
        now = utc_now_iso()
        conn.execute(
            "INSERT INTO focus(id, module_id, task_id, worktree_id, updated_ts) VALUES(1,NULL,NULL,NULL,?)",
            (now,),
        )
        return {"module_id": None, "task_id": None, "worktree_id": None, "updated_ts": now}
    return dict(row)


def set_focus_module(conn, module_id: str) -> dict:
    module_id = validate_module_id_strict(module_id)
    cur = conn.execute("SELECT module_id FROM modules WHERE module_id=?", (module_id,))
    if cur.fetchone() is None:
        raise PfError(f"module not found: {module_id}", EXIT_NOT_FOUND)

    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO focus(id, module_id, task_id, worktree_id, updated_ts)
        VALUES(1, ?, NULL, NULL, ?)
        ON CONFLICT(id) DO UPDATE SET
          module_id=excluded.module_id,
          task_id=NULL,
          worktree_id=NULL,
          updated_ts=excluded.updated_ts
        """,
        (module_id, now),
    )

    append_event(
        conn,
        event_type="focus.changed",
        scope_type="module",
        scope_id=module_id,
        actor="pf",
        summary=f"focus module changed to {module_id}",
        payload={"module_id": module_id},
    )
    return get_focus(conn)


def set_focus_task(conn, module_id: str, task_id: str) -> None:
    ensure_safe_module_id_or_raise(module_id, source="focus.task module_id")
    now = utc_now_iso()
    conn.execute(
        "UPDATE focus SET module_id=?, task_id=?, updated_ts=? WHERE id=1",
        (module_id, task_id, now),
    )
