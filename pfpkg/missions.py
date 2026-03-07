"""Mission commands."""

from __future__ import annotations

from pathlib import Path

from pfpkg.artifacts import put_artifact
from pfpkg.errors import EXIT_NOT_FOUND, PfError
from pfpkg.events import append_event
from pfpkg.ids import next_mission_id
from pfpkg.templates_store import load_template
from pfpkg.util_fs import ensure_dir, path_to_repo_relative


def create_mission(conn, repo_root: Path, *, title: str, summary: str | None = None, spec_path: str | None = None) -> dict:
    mission_id = next_mission_id(conn)
    ensure_dir(repo_root / ".pf" / "missions")

    if spec_path:
        abs_spec = path_to_repo_relative(repo_root, spec_path)
        if not abs_spec.exists():
            raise PfError(f"mission spec file not found: {spec_path}", EXIT_NOT_FOUND)
        rel_spec = str(abs_spec.relative_to(repo_root))
    else:
        rel_spec = f".pf/missions/{mission_id}.md"
        template = load_template(repo_root, "mission_spec.md.template")
        content = (
            template.replace("<mission_id>", mission_id)
            .replace("<короткий заголовок>", title)
            .replace("<вставить текст пользователя>", summary or "")
        )
        (repo_root / rel_spec).write_text(content, encoding="utf-8")

    artifact = put_artifact(conn, repo_root, kind="plan", path_value=rel_spec)

    append_event(
        conn,
        event_type="mission.created",
        scope_type="root",
        scope_id="root",
        mission_id=mission_id,
        actor="assistant",
        summary=f"mission created: {title}",
        payload={"mission_id": mission_id, "title": title, "spec_path": rel_spec, "summary": summary or ""},
        artifact_ids=[artifact["artifact_id"]],
    )

    return {
        "mission_id": mission_id,
        "title": title,
        "summary": summary or "",
        "spec_path": rel_spec,
        "artifact_id": artifact["artifact_id"],
    }


def close_mission(conn, *, mission_id: str, summary: str) -> dict:
    cur = conn.execute(
        "SELECT event_id FROM events WHERE mission_id=? AND type='mission.created' ORDER BY event_id DESC LIMIT 1",
        (mission_id,),
    )
    if cur.fetchone() is None:
        raise PfError(f"mission not found: {mission_id}", EXIT_NOT_FOUND)

    event_id = append_event(
        conn,
        event_type="mission.closed",
        scope_type="root",
        scope_id="root",
        mission_id=mission_id,
        actor="assistant",
        summary=f"mission closed: {mission_id}",
        payload={"mission_id": mission_id, "summary": summary},
    )
    return {"mission_id": mission_id, "event_id": event_id}
