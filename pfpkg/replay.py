"""Replay and consistency checks."""

from __future__ import annotations

import json


def replay_check(conn) -> dict:
    issues: list[str] = []

    # Required tables exist.
    required = {
        "schema_meta",
        "events",
        "artifacts",
        "modules",
        "worktrees",
        "focus",
        "pkm_items",
        "docs_index",
    }
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row["name"] for row in cur.fetchall()}
    for table in sorted(required - existing):
        issues.append(f"missing table: {table}")

    # Events timestamps monotonic by event_id (non-decreasing lexical ISO8601).
    cur = conn.execute("SELECT event_id, ts FROM events ORDER BY event_id ASC")
    prev_ts = None
    for row in cur.fetchall():
        ts = row["ts"]
        if prev_ts is not None and ts < prev_ts:
            issues.append(f"events ts not monotonic at event_id={row['event_id']}")
            break
        prev_ts = ts

    # Scope/module references and artifact references.
    cur = conn.execute(
        "SELECT event_id, scope_type, scope_id, worktree_id, artifact_ids_json FROM events ORDER BY event_id"
    )
    for row in cur.fetchall():
        event_id = row["event_id"]
        if row["scope_type"] == "module":
            c2 = conn.execute("SELECT 1 FROM modules WHERE module_id=?", (row["scope_id"],))
            if c2.fetchone() is None:
                issues.append(f"event {event_id}: module scope_id missing in modules: {row['scope_id']}")

        if row["worktree_id"]:
            c2 = conn.execute("SELECT 1 FROM worktrees WHERE worktree_id=?", (row["worktree_id"],))
            if c2.fetchone() is None:
                issues.append(f"event {event_id}: worktree_id not found: {row['worktree_id']}")

        try:
            artifact_ids = json.loads(row["artifact_ids_json"])
        except json.JSONDecodeError:
            issues.append(f"event {event_id}: artifact_ids_json is not valid json")
            continue
        if not isinstance(artifact_ids, list):
            issues.append(f"event {event_id}: artifact_ids_json must be array")
            continue
        for artifact_id in artifact_ids:
            c2 = conn.execute("SELECT 1 FROM artifacts WHERE artifact_id=?", (artifact_id,))
            if c2.fetchone() is None:
                issues.append(f"event {event_id}: artifact_id missing: {artifact_id}")

    # Worktree references to modules.
    cur = conn.execute("SELECT worktree_id, module_id FROM worktrees")
    for row in cur.fetchall():
        c2 = conn.execute("SELECT 1 FROM modules WHERE module_id=?", (row["module_id"],))
        if c2.fetchone() is None:
            issues.append(f"worktree {row['worktree_id']}: module not found: {row['module_id']}")

    return {"ok": len(issues) == 0, "issues": issues}
