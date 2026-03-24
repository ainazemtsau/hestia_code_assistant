"""Worktree mapping commands."""

from __future__ import annotations

from pfpkg.errors import EXIT_NOT_FOUND, PfError
from pfpkg.events import append_event
from pfpkg.util_time import utc_now_iso
from pfpkg.validation import ensure_safe_module_id_or_raise, validate_module_id_strict


def upsert_worktree(conn, *, worktree_id: str, module_id: str, path: str, branch: str | None) -> dict:
    module_id = validate_module_id_strict(module_id)
    cur = conn.execute("SELECT 1 FROM modules WHERE module_id=?", (module_id,))
    if cur.fetchone() is None:
        raise PfError(f"module not found: {module_id}", EXIT_NOT_FOUND)

    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO worktrees(worktree_id, module_id, path, branch, created_ts, active)
        VALUES(?, ?, ?, ?, ?, 1)
        ON CONFLICT(worktree_id) DO UPDATE SET
          module_id=excluded.module_id,
          path=excluded.path,
          branch=excluded.branch,
          active=1
        """,
        (worktree_id, module_id, path, branch, now),
    )

    append_event(
        conn,
        event_type="worktree.upserted",
        scope_type="module",
        scope_id=module_id,
        actor="pf",
        summary=f"worktree mapped: {worktree_id}",
        payload={"worktree_id": worktree_id, "module_id": module_id, "path": path, "branch": branch},
    )

    cur = conn.execute(
        "SELECT worktree_id, module_id, path, branch, created_ts, active FROM worktrees WHERE worktree_id=?",
        (worktree_id,),
    )
    return dict(cur.fetchone())


def list_worktrees(conn, module_id: str | None = None) -> list[dict]:
    if module_id:
        module_id = validate_module_id_strict(module_id)
        cur = conn.execute(
            "SELECT worktree_id, module_id, path, branch, created_ts, active FROM worktrees WHERE module_id=? ORDER BY worktree_id",
            (module_id,),
        )
    else:
        cur = conn.execute(
            "SELECT worktree_id, module_id, path, branch, created_ts, active FROM worktrees ORDER BY worktree_id"
        )
    out = [dict(r) for r in cur.fetchall()]
    for row in out:
        ensure_safe_module_id_or_raise(row["module_id"], source="worktrees table")
    return out
