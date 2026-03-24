"""Read-model helpers for status and reports."""

from __future__ import annotations

from typing import Any


def initialized(db_path) -> bool:
    return db_path.exists()


def active_mission(conn) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT mission_id, type, summary, ts, event_id
        FROM events
        WHERE mission_id IS NOT NULL
          AND type IN ('mission.created', 'mission.closed')
        ORDER BY event_id ASC
        """
    )
    state: dict[str, dict[str, Any]] = {}
    for row in cur.fetchall():
        mid = row["mission_id"]
        if row["type"] == "mission.created":
            state[mid] = {
                "mission_id": mid,
                "summary": row["summary"],
                "created_ts": row["ts"],
                "created_event_id": int(row["event_id"]),
                "active": True,
            }
        elif row["type"] == "mission.closed" and mid in state:
            state[mid]["active"] = False
    active = [v for v in state.values() if v["active"]]
    if not active:
        return None
    active.sort(key=lambda x: x["created_event_id"], reverse=True)
    return active[0]


def latest_task_for_focus(conn, module_id: str | None) -> dict[str, Any] | None:
    if not module_id:
        return None
    cur = conn.execute(
        """
        SELECT task_id, mission_id, summary, ts, event_id
        FROM events
        WHERE scope_type='module' AND scope_id=? AND task_id IS NOT NULL
          AND type='task.created'
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (module_id,),
    )
    row = cur.fetchone()
    return dict(row) if row else None


def task_state(conn, task_id: str | None) -> str | None:
    if not task_id:
        return None
    cur = conn.execute(
        """
        SELECT payload_json
        FROM events
        WHERE type='task.state_changed' AND task_id=?
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (task_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    import json

    payload = json.loads(row["payload_json"])
    return payload.get("new_state")


def task_workflow(conn, task_id: str | None) -> dict[str, Any] | None:
    if not task_id:
        return None

    cur = conn.execute(
        """
        SELECT scope_id AS module_id, mission_id
        FROM events
        WHERE type='task.created' AND task_id=?
        ORDER BY event_id ASC
        LIMIT 1
        """,
        (task_id,),
    )
    created = cur.fetchone()
    if created is None:
        return None

    cur = conn.execute(
        """
        SELECT payload_json
        FROM events
        WHERE type='task.state_changed' AND task_id=?
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (task_id,),
    )
    row = cur.fetchone()
    state = "NEW"
    if row:
        import json

        payload = json.loads(row["payload_json"])
        state = payload.get("new_state") or "NEW"

    cur = conn.execute(
        """
        SELECT 1
        FROM events
        WHERE type='plan.saved' AND task_id=?
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (task_id,),
    )
    plan_saved = cur.fetchone() is not None

    cur = conn.execute(
        """
        SELECT 1
        FROM events
        WHERE type='plan.approved' AND task_id=?
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (task_id,),
    )
    plan_approved = cur.fetchone() is not None

    return {
        "task_id": task_id,
        "module_id": created["module_id"],
        "mission_id": created["mission_id"],
        "state": state,
        "plan_saved": plan_saved,
        "plan_approved": plan_approved,
    }


def modules_summary(conn) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT module_id, root_path, display_name, initialized, updated_ts
        FROM modules
        ORDER BY module_id ASC
        """
    )
    return [dict(r) for r in cur.fetchall()]


def stale_docs_count(conn) -> int:
    cur = conn.execute("SELECT COUNT(*) AS c FROM docs_index WHERE stale=1")
    return int(cur.fetchone()["c"])


def last_incidents(conn, limit: int = 3) -> list[dict[str, Any]]:
    cur = conn.execute(
        """
        SELECT event_id, ts, type, scope_type, scope_id, summary
        FROM events
        WHERE type LIKE 'incident.%' OR type='incident.logged'
        ORDER BY event_id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return [dict(r) for r in cur.fetchall()]


def last_verify(conn) -> dict[str, Any] | None:
    cur = conn.execute(
        """
        SELECT event_id, ts, summary, payload_json
        FROM events
        WHERE type='command.completed'
        ORDER BY event_id DESC
        LIMIT 1
        """
    )
    row = cur.fetchone()
    if not row:
        return None
    import json

    payload = json.loads(row["payload_json"])
    return {
        "event_id": row["event_id"],
        "ts": row["ts"],
        "summary": row["summary"],
        "exit_code": payload.get("exit_code"),
        "cmd": payload.get("cmd"),
    }


def has_plan_approved(conn, module_id: str) -> bool:
    cur = conn.execute(
        """
        SELECT 1 FROM events
        WHERE type='plan.approved' AND scope_type='module' AND scope_id=?
        ORDER BY event_id DESC
        LIMIT 1
        """,
        (module_id,),
    )
    return cur.fetchone() is not None


def event_count(conn) -> int:
    cur = conn.execute("SELECT COUNT(*) AS c FROM events")
    return int(cur.fetchone()["c"])
