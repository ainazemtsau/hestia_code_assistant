"""Event log commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pfpkg.errors import EXIT_VALIDATION, PfError
from pfpkg.util_json import load_json_object_from_ref
from pfpkg.util_time import utc_now_iso

VALID_SCOPE_TYPES = {"root", "module"}
VALID_ACTORS = {"user", "assistant", "pf"}


def parse_artifact_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if not token.isdigit():
            raise PfError("artifact ids must be comma-separated integers", EXIT_VALIDATION)
        out.append(int(token))
    return out


def append_event(
    conn,
    *,
    event_type: str,
    scope_type: str,
    scope_id: str,
    summary: str,
    actor: str = "assistant",
    payload: dict[str, Any] | None = None,
    artifact_ids: list[int] | None = None,
    mission_id: str | None = None,
    task_id: str | None = None,
    slice_id: str | None = None,
    worktree_id: str | None = None,
) -> int:
    if scope_type not in VALID_SCOPE_TYPES:
        raise PfError("scope-type must be root|module", EXIT_VALIDATION)
    if actor not in VALID_ACTORS:
        raise PfError("actor must be user|assistant|pf", EXIT_VALIDATION)
    if not summary.strip():
        raise PfError("summary cannot be empty", EXIT_VALIDATION)

    payload_obj = payload or {}
    if not isinstance(payload_obj, dict):
        raise PfError("payload must be a json object", EXIT_VALIDATION)
    artifact_ids = artifact_ids or []

    if artifact_ids:
        placeholders = ",".join("?" for _ in artifact_ids)
        cur = conn.execute(
            f"SELECT COUNT(*) AS c FROM artifacts WHERE artifact_id IN ({placeholders})",
            tuple(artifact_ids),
        )
        found = int(cur.fetchone()["c"])
        if found != len(set(artifact_ids)):
            raise PfError("one or more artifact ids not found", EXIT_VALIDATION)

    ts = utc_now_iso()
    cur = conn.execute(
        """
        INSERT INTO events(
          ts, type, scope_type, scope_id,
          mission_id, task_id, slice_id, worktree_id,
          actor, summary, payload_json, artifact_ids_json
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            event_type,
            scope_type,
            scope_id,
            mission_id,
            task_id,
            slice_id,
            worktree_id,
            actor,
            summary,
            json.dumps(payload_obj, ensure_ascii=False, sort_keys=True),
            json.dumps(artifact_ids, ensure_ascii=False),
        ),
    )
    return int(cur.lastrowid)


def append_event_from_args(conn, args) -> dict:
    payload_ref = args.payload_json or args.payload
    if not payload_ref:
        raise PfError("payload is required (use --payload-json or --payload @file)", EXIT_VALIDATION)
    payload = load_json_object_from_ref(payload_ref, label="payload")

    event_id = append_event(
        conn,
        event_type=args.type,
        scope_type=args.scope_type,
        scope_id=args.scope_id,
        summary=args.summary,
        actor=args.actor,
        payload=payload,
        artifact_ids=parse_artifact_ids(args.artifact_ids),
        mission_id=args.mission_id,
        task_id=args.task_id,
        slice_id=args.slice_id,
        worktree_id=args.worktree_id,
    )
    return {"event_id": event_id}


def event_tail(conn, *, limit: int, scope_type: str | None = None, scope_id: str | None = None, mission_id: str | None = None) -> list[dict]:
    where = []
    params: list[Any] = []

    if scope_type:
        where.append("scope_type = ?")
        params.append(scope_type)
    if scope_id:
        where.append("scope_id = ?")
        params.append(scope_id)
    if mission_id:
        where.append("mission_id = ?")
        params.append(mission_id)

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    params.append(limit)

    cur = conn.execute(
        f"""
        SELECT event_id, ts, type, scope_type, scope_id, actor, summary,
               mission_id, task_id, slice_id, worktree_id
        FROM events
        {where_sql}
        ORDER BY event_id DESC
        LIMIT ?
        """,
        tuple(params),
    )
    return [dict(row) for row in cur.fetchall()]
