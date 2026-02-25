"""SQLite-backed event log."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from csk_next.domain.schemas import validate_schema
from csk_next.io.files import ensure_dir
from csk_next.io.runner import run_argv
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso


_SCHEMA_VERSION = 1


def _eventlog_path(layout: Layout) -> Path:
    return layout.app / "eventlog.sqlite"


def _engine_version(layout: Layout) -> str:
    version_path = layout.engine / "VERSION"
    if not version_path.exists():
        return "unknown"
    return version_path.read_text(encoding="utf-8").strip() or "unknown"


def _run_git(repo_root: Path, *git_args: str):
    try:
        return run_argv(["git", "-C", str(repo_root), *git_args], check=False)
    except OSError:
        return None


def _git_head(repo_root: Path) -> str | None:
    inside = _run_git(repo_root, "rev-parse", "--is-inside-work-tree")
    if inside is None or inside.returncode != 0:
        return None

    head = _run_git(repo_root, "rev-parse", "HEAD")
    if head is None or head.returncode != 0:
        return None
    value = head.stdout.strip()
    if not value:
        return None

    dirty = _run_git(repo_root, "status", "--porcelain")
    if dirty is not None and dirty.returncode == 0 and dirty.stdout.strip():
        return f"{value}:dirty"
    return value


def _connect(path: Path) -> sqlite3.Connection:
    ensure_dir(path.parent)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def _init_db(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            type TEXT NOT NULL,
            actor TEXT NOT NULL,
            mission_id TEXT NULL,
            module_id TEXT NULL,
            task_id TEXT NULL,
            slice_id TEXT NULL,
            repo_git_head TEXT NULL,
            worktree_path TEXT NULL,
            payload_json TEXT NOT NULL,
            artifact_refs_json TEXT NOT NULL,
            engine_version TEXT NOT NULL
        )
        """
    )
    connection.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
    connection.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_events_scope
        ON events(mission_id, module_id, task_id, slice_id)
        """
    )
    user_version = int(connection.execute("PRAGMA user_version").fetchone()[0])
    if user_version < _SCHEMA_VERSION:
        connection.execute(f"PRAGMA user_version={_SCHEMA_VERSION}")
    connection.commit()


def _row_to_event(row: sqlite3.Row) -> dict[str, Any]:
    payload: dict[str, Any] = json.loads(str(row["payload_json"]))
    artifact_refs: list[str] = json.loads(str(row["artifact_refs_json"]))
    event = {
        "id": str(row["id"]),
        "ts": str(row["ts"]),
        "type": str(row["type"]),
        "actor": str(row["actor"]),
        "mission_id": row["mission_id"],
        "module_id": row["module_id"],
        "task_id": row["task_id"],
        "slice_id": row["slice_id"],
        "repo_git_head": row["repo_git_head"],
        "worktree_path": row["worktree_path"],
        "payload": payload,
        "artifact_refs": artifact_refs,
        "engine_version": str(row["engine_version"]),
    }
    validate_schema("event_envelope", event)
    return event


def append_event(
    *,
    layout: Layout,
    event_type: str,
    actor: str,
    payload: dict[str, Any] | None = None,
    artifact_refs: list[str] | None = None,
    mission_id: str | None = None,
    module_id: str | None = None,
    task_id: str | None = None,
    slice_id: str | None = None,
    repo_git_head: str | None = None,
    worktree_path: str | None = None,
    engine_version: str | None = None,
    event_id: str | None = None,
    ts: str | None = None,
) -> dict[str, Any]:
    event = {
        "id": event_id or str(uuid4()),
        "ts": ts or utc_now_iso(),
        "type": event_type,
        "actor": actor,
        "mission_id": mission_id,
        "module_id": module_id,
        "task_id": task_id,
        "slice_id": slice_id,
        "repo_git_head": repo_git_head if repo_git_head is not None else _git_head(layout.repo_root),
        "worktree_path": worktree_path,
        "payload": payload or {},
        "artifact_refs": artifact_refs or [],
        "engine_version": engine_version or _engine_version(layout),
    }
    validate_schema("event_envelope", event)

    db_path = _eventlog_path(layout)
    with _connect(db_path) as connection:
        _init_db(connection)
        connection.execute(
            """
            INSERT INTO events (
                id, ts, type, actor, mission_id, module_id, task_id, slice_id,
                repo_git_head, worktree_path, payload_json, artifact_refs_json, engine_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["id"],
                event["ts"],
                event["type"],
                event["actor"],
                event["mission_id"],
                event["module_id"],
                event["task_id"],
                event["slice_id"],
                event["repo_git_head"],
                event["worktree_path"],
                json.dumps(event["payload"], ensure_ascii=False, sort_keys=True),
                json.dumps(event["artifact_refs"], ensure_ascii=False, sort_keys=True),
                event["engine_version"],
            ),
        )
        connection.commit()
    return event


def query_events(
    *,
    layout: Layout,
    limit: int = 20,
    event_type: str | None = None,
    mission_id: str | None = None,
    module_id: str | None = None,
    task_id: str | None = None,
    slice_id: str | None = None,
) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("limit must be > 0")

    db_path = _eventlog_path(layout)
    if not db_path.exists():
        return []

    where: list[str] = []
    params: list[Any] = []
    for field, value in [
        ("type", event_type),
        ("mission_id", mission_id),
        ("module_id", module_id),
        ("task_id", task_id),
        ("slice_id", slice_id),
    ]:
        if value is None:
            continue
        where.append(f"{field} = ?")
        params.append(value)

    statement = """
        SELECT id, ts, type, actor, mission_id, module_id, task_id, slice_id,
               repo_git_head, worktree_path, payload_json, artifact_refs_json, engine_version
        FROM events
    """
    if where:
        statement += " WHERE " + " AND ".join(where)
    statement += " ORDER BY ts DESC, rowid DESC LIMIT ?"
    params.append(limit)

    with _connect(db_path) as connection:
        _init_db(connection)
        rows = connection.execute(statement, params).fetchall()
    return [_row_to_event(row) for row in rows]


def tail_events(
    *,
    layout: Layout,
    n: int = 20,
    event_type: str | None = None,
    mission_id: str | None = None,
    module_id: str | None = None,
    task_id: str | None = None,
    slice_id: str | None = None,
) -> list[dict[str, Any]]:
    return query_events(
        layout=layout,
        limit=n,
        event_type=event_type,
        mission_id=mission_id,
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
    )
