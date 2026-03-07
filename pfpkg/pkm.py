"""PKM storage and stale detection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pfpkg.docs_freshness import compute_fingerprint
from pfpkg.errors import EXIT_VALIDATION, PfError
from pfpkg.events import append_event
from pfpkg.util_json import load_json_object_from_ref
from pfpkg.util_time import utc_now_iso

VALID_SCOPE_TYPES = {"global", "module", "cross"}
VALID_KINDS = {"runbook", "pitfall", "decision", "convention"}


def _read_body_md(value: str) -> str:
    if value.startswith("@"):
        path = Path(value[1:])
        if not path.exists():
            raise PfError(f"body-md file not found: {path}", EXIT_VALIDATION)
        return path.read_text(encoding="utf-8")
    return value


def upsert_pkm(
    conn,
    *,
    scope_type: str,
    scope_id: str,
    kind: str,
    title: str,
    body_md: str,
    fingerprint_json: dict[str, Any],
    confidence: float,
    tags: list[str] | None = None,
) -> dict:
    if scope_type not in VALID_SCOPE_TYPES:
        raise PfError("scope-type must be global|module|cross", EXIT_VALIDATION)
    if kind not in VALID_KINDS:
        raise PfError("kind must be runbook|pitfall|decision|convention", EXIT_VALIDATION)
    if not (0.0 <= confidence <= 1.0):
        raise PfError("confidence must be between 0 and 1", EXIT_VALIDATION)

    now = utc_now_iso()
    tags = tags or []

    cur = conn.execute(
        "SELECT pkm_id FROM pkm_items WHERE scope_type=? AND scope_id=? AND kind=? AND title=?",
        (scope_type, scope_id, kind, title),
    )
    row = cur.fetchone()

    if row:
        pkm_id = int(row["pkm_id"])
        conn.execute(
            """
            UPDATE pkm_items
            SET body_md=?, tags_json=?, fingerprint_json=?, confidence=?, updated_ts=?
            WHERE pkm_id=?
            """,
            (
                body_md,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(fingerprint_json, ensure_ascii=False, sort_keys=True),
                confidence,
                now,
                pkm_id,
            ),
        )
    else:
        cur = conn.execute(
            """
            INSERT INTO pkm_items(scope_type, scope_id, kind, title, body_md, tags_json, fingerprint_json, confidence, stale, created_ts, updated_ts)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """,
            (
                scope_type,
                scope_id,
                kind,
                title,
                body_md,
                json.dumps(tags, ensure_ascii=False),
                json.dumps(fingerprint_json, ensure_ascii=False, sort_keys=True),
                confidence,
                now,
                now,
            ),
        )
        pkm_id = int(cur.lastrowid)

    append_event(
        conn,
        event_type="pkm.upserted",
        scope_type="module" if scope_type == "module" else "root",
        scope_id=scope_id if scope_type == "module" else "root",
        actor="assistant",
        summary=f"pkm upserted: {title}",
        payload={
            "pkm_id": pkm_id,
            "scope_type": scope_type,
            "scope_id": scope_id,
            "kind": kind,
            "title": title,
            "confidence": confidence,
        },
    )

    return {"pkm_id": pkm_id, "scope_type": scope_type, "scope_id": scope_id, "kind": kind, "title": title}


def list_pkm(conn, *, scope_type: str, scope_id: str, kind: str | None = None) -> list[dict]:
    if kind:
        cur = conn.execute(
            """
            SELECT pkm_id, scope_type, scope_id, kind, title, body_md, tags_json, fingerprint_json, confidence, stale, created_ts, updated_ts
            FROM pkm_items
            WHERE scope_type=? AND scope_id=? AND kind=?
            ORDER BY stale ASC, confidence DESC, pkm_id DESC
            """,
            (scope_type, scope_id, kind),
        )
    else:
        cur = conn.execute(
            """
            SELECT pkm_id, scope_type, scope_id, kind, title, body_md, tags_json, fingerprint_json, confidence, stale, created_ts, updated_ts
            FROM pkm_items
            WHERE scope_type=? AND scope_id=?
            ORDER BY stale ASC, confidence DESC, pkm_id DESC
            """,
            (scope_type, scope_id),
        )
    out = []
    for row in cur.fetchall():
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        item["fingerprint"] = json.loads(item.pop("fingerprint_json"))
        out.append(item)
    return out


def refresh_pkm_staleness(conn, repo_root: Path) -> int:
    cur = conn.execute("SELECT pkm_id, fingerprint_json, stale FROM pkm_items")
    changed = 0
    for row in cur.fetchall():
        fp = json.loads(row["fingerprint_json"])
        sources = fp.get("sources")
        if not isinstance(sources, list) or not sources:
            continue

        source_specs = []
        for src in sources:
            if isinstance(src, dict) and src.get("path") and src.get("mode"):
                source_specs.append({"path": src["path"], "mode": src["mode"]})

        if not source_specs:
            continue

        recomputed = compute_fingerprint(repo_root, source_specs)
        is_stale = 1 if recomputed.get("combined") != fp.get("combined") else 0
        if is_stale != int(row["stale"]):
            changed += 1
            conn.execute(
                "UPDATE pkm_items SET stale=?, updated_ts=? WHERE pkm_id=?",
                (is_stale, utc_now_iso(), row["pkm_id"]),
            )
    return changed


def upsert_pkm_from_args(conn, args) -> dict:
    body = _read_body_md(args.body_md)
    fingerprint = load_json_object_from_ref(args.fingerprint_json, label="fingerprint-json")
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    return upsert_pkm(
        conn,
        scope_type=args.scope_type,
        scope_id=args.scope_id,
        kind=args.kind,
        title=args.title,
        body_md=body,
        fingerprint_json=fingerprint,
        confidence=args.confidence,
        tags=tags,
    )
