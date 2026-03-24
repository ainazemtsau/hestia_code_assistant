"""SQLite connection and migrations."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from pfpkg.errors import EXIT_NOT_INITIALIZED, PfError
from pfpkg.util_time import utc_now_iso

SCHEMA_V1 = """
CREATE TABLE IF NOT EXISTS schema_meta (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  schema_version INTEGER NOT NULL,
  created_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  type TEXT NOT NULL,
  scope_type TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  mission_id TEXT,
  task_id TEXT,
  slice_id TEXT,
  worktree_id TEXT,
  actor TEXT NOT NULL,
  summary TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  artifact_ids_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_scope_ts
  ON events(scope_type, scope_id, ts);
CREATE INDEX IF NOT EXISTS idx_events_mission_task_ts
  ON events(mission_id, task_id, ts);
CREATE INDEX IF NOT EXISTS idx_events_type_ts
  ON events(type, ts);

CREATE TABLE IF NOT EXISTS artifacts (
  artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  created_ts TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_artifacts_path_sha
  ON artifacts(path, sha256);

CREATE TABLE IF NOT EXISTS modules (
  module_id TEXT PRIMARY KEY,
  root_path TEXT NOT NULL,
  display_name TEXT NOT NULL,
  initialized INTEGER NOT NULL,
  created_ts TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_modules_root_path
  ON modules(root_path);

CREATE TABLE IF NOT EXISTS worktrees (
  worktree_id TEXT PRIMARY KEY,
  module_id TEXT NOT NULL,
  path TEXT NOT NULL,
  branch TEXT,
  created_ts TEXT NOT NULL,
  active INTEGER NOT NULL,
  FOREIGN KEY(module_id) REFERENCES modules(module_id)
);
CREATE INDEX IF NOT EXISTS idx_worktrees_module_active
  ON worktrees(module_id, active);

CREATE TABLE IF NOT EXISTS focus (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  module_id TEXT,
  task_id TEXT,
  worktree_id TEXT,
  updated_ts TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pkm_items (
  pkm_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope_type TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  body_md TEXT NOT NULL,
  tags_json TEXT NOT NULL,
  fingerprint_json TEXT NOT NULL,
  confidence REAL NOT NULL,
  stale INTEGER NOT NULL,
  created_ts TEXT NOT NULL,
  updated_ts TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pkm_scope_kind
  ON pkm_items(scope_type, scope_id, kind);
CREATE INDEX IF NOT EXISTS idx_pkm_stale_conf
  ON pkm_items(stale, confidence DESC);

CREATE TABLE IF NOT EXISTS pkm_sources (
  pkm_id INTEGER NOT NULL,
  source_type TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  note TEXT,
  FOREIGN KEY(pkm_id) REFERENCES pkm_items(pkm_id)
);
CREATE INDEX IF NOT EXISTS idx_pkm_sources_pkm
  ON pkm_sources(pkm_id);

CREATE TABLE IF NOT EXISTS docs_index (
  doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
  scope_type TEXT NOT NULL,
  scope_id TEXT NOT NULL,
  path TEXT NOT NULL,
  sources_json TEXT NOT NULL,
  fingerprint_json TEXT NOT NULL,
  stale INTEGER NOT NULL,
  stale_reason TEXT,
  last_checked_ts TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_docs_scope_path
  ON docs_index(scope_type, scope_id, path);
"""

SCHEMA_V2 = """
CREATE TABLE IF NOT EXISTS runtime_counters (
  name TEXT PRIMARY KEY,
  value INTEGER NOT NULL
);
"""

SCHEMA_V3 = """
CREATE TABLE IF NOT EXISTS doctor_baseline (
  path TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  created_ts TEXT NOT NULL
);
"""

LATEST_SCHEMA_VERSION = 3


def connect_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn


def is_initialized(db_path: Path) -> bool:
    return db_path.exists()


def require_initialized(db_path: Path) -> None:
    if not db_path.exists():
        raise PfError("powerflow is not initialized, run: pf init", EXIT_NOT_INITIALIZED)


def _schema_version(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_meta'"
    )
    if cur.fetchone() is None:
        return 0
    cur = conn.execute("SELECT schema_version FROM schema_meta WHERE id=1")
    row = cur.fetchone()
    return int(row["schema_version"]) if row else 0


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row["name"] == column for row in cur.fetchall())


def migrate(conn: sqlite3.Connection) -> int:
    version = _schema_version(conn)
    now = utc_now_iso()

    if version < 1:
        conn.executescript(SCHEMA_V1)
        conn.execute(
            "INSERT OR REPLACE INTO schema_meta(id, schema_version, created_ts) VALUES(1, 1, ?)",
            (now,),
        )
        version = 1

    if version < 2:
        conn.executescript(SCHEMA_V2)
        conn.execute("UPDATE schema_meta SET schema_version=2 WHERE id=1")
        version = 2

    if version < 3:
        conn.executescript(SCHEMA_V3)
        if not _has_column(conn, "docs_index", "baseline_fingerprint_json"):
            conn.execute("ALTER TABLE docs_index ADD COLUMN baseline_fingerprint_json TEXT")
        if not _has_column(conn, "docs_index", "observed_fingerprint_json"):
            conn.execute("ALTER TABLE docs_index ADD COLUMN observed_fingerprint_json TEXT")
        conn.execute(
            """
            UPDATE docs_index
            SET baseline_fingerprint_json = COALESCE(baseline_fingerprint_json, fingerprint_json),
                observed_fingerprint_json = COALESCE(observed_fingerprint_json, fingerprint_json)
            """
        )
        conn.execute("UPDATE schema_meta SET schema_version=3 WHERE id=1")
        version = 3

    conn.commit()
    return version


def ensure_focus_row(conn: sqlite3.Connection) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO focus(id, module_id, task_id, worktree_id, updated_ts)
        VALUES(1, NULL, NULL, NULL, ?)
        ON CONFLICT(id) DO NOTHING
        """,
        (now,),
    )


def ensure_root_module(conn: sqlite3.Connection) -> None:
    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO modules(module_id, root_path, display_name, initialized, created_ts, updated_ts)
        VALUES('root', '.', 'Root', 1, ?, ?)
        ON CONFLICT(module_id) DO UPDATE SET
          root_path=excluded.root_path,
          display_name=excluded.display_name,
          updated_ts=excluded.updated_ts
        """,
        (now, now),
    )


@contextmanager
def db_session(db_path: Path, *, require_init: bool = True) -> Iterator[sqlite3.Connection]:
    if require_init:
        require_initialized(db_path)
    conn = connect_db(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def next_counter(conn: sqlite3.Connection, name: str) -> int:
    conn.execute(
        "INSERT INTO runtime_counters(name, value) VALUES(?, 0) ON CONFLICT(name) DO NOTHING",
        (name,),
    )
    conn.execute("UPDATE runtime_counters SET value = value + 1 WHERE name=?", (name,))
    cur = conn.execute("SELECT value FROM runtime_counters WHERE name=?", (name,))
    row = cur.fetchone()
    return int(row["value"])
