"""Artifact registry commands."""

from __future__ import annotations

from pathlib import Path

from pfpkg.errors import EXIT_NOT_FOUND, EXIT_VALIDATION, PfError
from pfpkg.util_fs import path_to_repo_relative
from pfpkg.util_hash import sha256_file
from pfpkg.util_time import utc_now_iso


def put_artifact(conn, repo_root: Path, *, kind: str, path_value: str) -> dict:
    abs_path = path_to_repo_relative(repo_root, path_value)
    if not abs_path.exists() or not abs_path.is_file():
        raise PfError(f"artifact file not found: {path_value}", EXIT_NOT_FOUND)

    rel_path = str(abs_path.relative_to(repo_root))
    sha256 = sha256_file(abs_path)
    size = abs_path.stat().st_size
    now = utc_now_iso()

    cur = conn.execute(
        """
        SELECT artifact_id, kind, path, sha256, bytes, created_ts
        FROM artifacts
        WHERE path=? AND sha256=?
        """,
        (rel_path, sha256),
    )
    row = cur.fetchone()
    if row:
        if row["kind"] != kind:
            raise PfError(
                f"artifact already exists with kind='{row['kind']}', requested kind='{kind}'",
                EXIT_VALIDATION,
                details={
                    "artifact_id": int(row["artifact_id"]),
                    "existing_kind": row["kind"],
                    "requested_kind": kind,
                    "path": rel_path,
                },
            )
        return {
            "artifact_id": int(row["artifact_id"]),
            "kind": row["kind"],
            "path": row["path"],
            "sha256": row["sha256"],
            "bytes": int(row["bytes"]),
            "created_ts": row["created_ts"],
            "reused": True,
        }
    else:
        cur = conn.execute(
            """
            INSERT INTO artifacts(kind, path, sha256, bytes, created_ts)
            VALUES(?, ?, ?, ?, ?)
            """,
            (kind, rel_path, sha256, size, now),
        )
        artifact_id = int(cur.lastrowid)

    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "path": rel_path,
        "sha256": sha256,
        "bytes": size,
        "created_ts": now,
        "reused": False,
    }
