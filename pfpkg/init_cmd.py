"""Initialization command implementation."""

from __future__ import annotations

from pathlib import Path

from pfpkg.db import connect_db, ensure_focus_row, ensure_root_module, migrate
from pfpkg.doctor import seed_doctor_baseline
from pfpkg.events import append_event
from pfpkg.templates_store import SKILL_REL_PATHS, load_template
from pfpkg.util_fs import ensure_dir


def _copy_template_if_missing(repo_root: Path, template_rel: str, dest_rel: str) -> tuple[bool, str]:
    dest = repo_root / dest_rel
    if dest.exists():
        return False, dest_rel
    ensure_dir(dest.parent)
    content = load_template(repo_root, template_rel)
    dest.write_text(content, encoding="utf-8")
    return True, dest_rel


def init_project(repo_root: Path, db_path: Path) -> dict:
    created: list[str] = []
    skipped: list[str] = []

    for directory in (
        ".pf",
        ".pf/artifacts",
        ".pf/artifacts/bundles",
        ".pf/modules",
        ".pf/modules/root",
        ".pf/missions",
        ".pf/local",
        ".agents/skills/pf",
    ):
        p = repo_root / directory
        if not p.exists():
            ensure_dir(p)
            created.append(directory)

    conn = connect_db(db_path)
    try:
        migrate(conn)
        ensure_focus_row(conn)
        ensure_root_module(conn)
        seed_doctor_baseline(conn, repo_root)

        created_agents, rel = _copy_template_if_missing(repo_root, "AGENTS.md", "AGENTS.md")
        (created if created_agents else skipped).append(rel)

        for skill_rel in SKILL_REL_PATHS:
            created_skill, rel_path = _copy_template_if_missing(repo_root, skill_rel, f".agents/{skill_rel}")
            (created if created_skill else skipped).append(rel_path)

        # Emit init event only once.
        cur = conn.execute("SELECT 1 FROM events WHERE type='pf.init.completed' LIMIT 1")
        if cur.fetchone() is None:
            append_event(
                conn,
                event_type="pf.init.completed",
                scope_type="root",
                scope_id="root",
                actor="pf",
                summary="pf init completed",
                payload={"version": 1},
            )

        conn.commit()
    finally:
        conn.close()

    return {"created": created, "skipped": skipped, "db_path": str(db_path.relative_to(repo_root))}
