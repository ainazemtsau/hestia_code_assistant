"""Docs freshness management for pf_doc managed documents."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pfpkg.errors import PfError
from pfpkg.events import append_event
from pfpkg.util_hash import sha256_bytes, sha256_file
from pfpkg.util_time import utc_now_iso
from pfpkg.util_git import git_tree_hash


def _extract_front_matter(text: str) -> str | None:
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end == -1:
        return None
    return text[4:end]


def parse_pf_doc_frontmatter(text: str) -> dict[str, Any] | None:
    fm = _extract_front_matter(text)
    if fm is None or "pf_doc:" not in fm:
        return None

    lines = fm.splitlines()
    in_pf = False
    scope: str | None = None
    sources: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue

        if re.match(r"^\s*pf_doc:\s*$", line):
            in_pf = True
            continue
        if not in_pf:
            continue

        scope_m = re.match(r"^\s*scope:\s*(.+?)\s*$", line)
        if scope_m:
            scope = scope_m.group(1).strip()
            continue

        src_m = re.match(r"^\s*-\s*path:\s*(.+?)\s*$", line)
        if src_m:
            current = {"path": src_m.group(1).strip()}
            sources.append(current)
            continue

        mode_m = re.match(r"^\s*mode:\s*(.+?)\s*$", line)
        if mode_m and current is not None:
            current["mode"] = mode_m.group(1).strip()
            continue

    if not scope or not sources:
        return None

    return {"scope": scope, "sources": sources}


def _compute_source(repo_root: Path, source: dict[str, str]) -> dict[str, Any]:
    path = source["path"]
    mode = source.get("mode", "file-sha")

    if mode == "file-sha":
        abs_path = (repo_root / path).resolve()
        if abs_path.exists() and abs_path.is_file():
            return {"path": path, "mode": mode, "sha256": sha256_file(abs_path)}
        return {"path": path, "mode": mode, "sha256": "missing"}

    if mode == "git-tree":
        tree, dirty = git_tree_hash(repo_root, path)
        return {"path": path, "mode": mode, "tree": tree or "missing", "dirty": dirty}

    return {"path": path, "mode": mode, "error": "unsupported_mode"}


def compute_fingerprint(repo_root: Path, sources: list[dict[str, str]]) -> dict[str, Any]:
    normalized = [_compute_source(repo_root, src) for src in sources]
    norm_sorted = sorted(normalized, key=lambda x: (x.get("path", ""), x.get("mode", "")))
    blob = json.dumps(norm_sorted, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "algo": "pf-v1",
        "sources": norm_sorted,
        "combined": sha256_bytes(blob),
    }


def _find_doc_candidates(repo_root: Path, scope: str | None = None, module_id: str | None = None) -> list[Path]:
    candidates: list[Path] = []

    if scope in (None, "module"):
        modules_root = repo_root / ".pf" / "modules"
        if modules_root.exists():
            module_dirs = [modules_root / module_id] if module_id else sorted([p for p in modules_root.iterdir() if p.is_dir()])
            for mod_dir in module_dirs:
                docs_dir = mod_dir / "DOCS"
                if not docs_dir.exists():
                    continue
                candidates.extend(sorted(docs_dir.glob("**/*.md")))

    if scope in (None, "root"):
        root_docs = repo_root / ".pf" / "DOCS"
        if root_docs.exists():
            candidates.extend(sorted(root_docs.glob("**/*.md")))

    return sorted(set(candidates), key=lambda p: str(p))


def _scope_from_meta(meta_scope: str) -> tuple[str, str]:
    if meta_scope == "root":
        return "root", "root"
    if meta_scope.startswith("module:"):
        return "module", meta_scope.split(":", 1)[1]
    return "root", "root"


def scan_docs(conn, repo_root: Path, *, scope: str | None = None, module_id: str | None = None) -> dict:
    docs = _find_doc_candidates(repo_root, scope=scope, module_id=module_id)
    scanned: list[str] = []

    for path in docs:
        text = path.read_text(encoding="utf-8")
        meta = parse_pf_doc_frontmatter(text)
        if meta is None:
            continue
        scope_type, scope_id = _scope_from_meta(meta["scope"])
        rel_path = str(path.relative_to(repo_root))
        fingerprint = compute_fingerprint(repo_root, meta["sources"])
        now = utc_now_iso()

        cur = conn.execute(
            """
            SELECT stale, baseline_fingerprint_json
            FROM docs_index
            WHERE scope_type=? AND scope_id=? AND path=?
            """,
            (scope_type, scope_id, rel_path),
        )
        row = cur.fetchone()
        stale = int(row["stale"]) if row else 0
        baseline = json.dumps(fingerprint, ensure_ascii=False, sort_keys=True)
        observed = baseline

        conn.execute(
            """
            INSERT INTO docs_index(
              scope_type, scope_id, path, sources_json, fingerprint_json,
              stale, stale_reason, last_checked_ts,
              baseline_fingerprint_json, observed_fingerprint_json
            )
            VALUES(?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
            ON CONFLICT(scope_type, scope_id, path) DO UPDATE SET
              sources_json=excluded.sources_json,
              observed_fingerprint_json=excluded.observed_fingerprint_json,
              last_checked_ts=excluded.last_checked_ts,
              baseline_fingerprint_json=COALESCE(docs_index.baseline_fingerprint_json, excluded.baseline_fingerprint_json),
              stale=docs_index.stale,
              stale_reason=docs_index.stale_reason
            """,
            (
                scope_type,
                scope_id,
                rel_path,
                json.dumps(meta["sources"], ensure_ascii=False, sort_keys=True),
                baseline,
                stale,
                now,
                baseline,
                observed,
            ),
        )

        append_event(
            conn,
            event_type="doc.scanned",
            scope_type=scope_type,
            scope_id=scope_id,
            actor="pf",
            summary=f"doc scanned: {rel_path}",
            payload={"path": rel_path},
        )
        scanned.append(rel_path)

    return {"scanned": scanned, "count": len(scanned)}


def check_docs(conn, repo_root: Path, *, scope: str | None = None, module_id: str | None = None) -> dict:
    where = []
    params: list[Any] = []
    if scope == "module" and module_id:
        where.append("scope_type='module' AND scope_id=?")
        params.append(module_id)
    elif scope == "root":
        where.append("scope_type='root' AND scope_id='root'")

    where_sql = f"WHERE {' AND '.join(where)}" if where else ""

    cur = conn.execute(
        f"""
        SELECT doc_id, scope_type, scope_id, path, sources_json, fingerprint_json,
               baseline_fingerprint_json, observed_fingerprint_json, stale
        FROM docs_index
        {where_sql}
        """,
        tuple(params),
    )

    checked = 0
    for row in cur.fetchall():
        checked += 1
        sources = json.loads(row["sources_json"])
        current = compute_fingerprint(repo_root, sources)
        baseline_json = row["baseline_fingerprint_json"] or row["fingerprint_json"]
        baseline = json.loads(baseline_json)
        now = utc_now_iso()
        current_json = json.dumps(current, ensure_ascii=False, sort_keys=True)

        if current.get("combined") != baseline.get("combined"):
            conn.execute(
                """
                UPDATE docs_index
                SET observed_fingerprint_json=?,
                    last_checked_ts=?
                WHERE doc_id=?
                """,
                (current_json, now, row["doc_id"]),
            )
            if int(row["stale"]) == 0:
                conn.execute(
                    """
                    UPDATE docs_index
                    SET stale=1,
                        stale_reason='fingerprint_changed',
                        last_checked_ts=?
                    WHERE doc_id=?
                    """,
                    (now, row["doc_id"]),
                )
                append_event(
                    conn,
                    event_type="doc.stale_detected",
                    scope_type=row["scope_type"],
                    scope_id=row["scope_id"],
                    actor="pf",
                    summary=f"doc stale: {row['path']}",
                    payload={"path": row["path"], "reason": "fingerprint_changed"},
                )
        else:
            conn.execute(
                """
                UPDATE docs_index
                SET observed_fingerprint_json=?,
                    last_checked_ts=?
                WHERE doc_id=?
                """,
                (current_json, now, row["doc_id"]),
            )

    stale_where_sql = where_sql
    if stale_where_sql:
        stale_where_sql = f"{stale_where_sql} AND stale=1"
    else:
        stale_where_sql = "WHERE stale=1"

    stale_rows = conn.execute(
        f"SELECT path, stale_reason FROM docs_index {stale_where_sql} ORDER BY path",
        tuple(params),
    ).fetchall()
    stale_docs = [{"path": row["path"], "reason": row["stale_reason"]} for row in stale_rows]
    return {"checked": checked, "stale_docs": stale_docs, "stale_count": len(stale_docs)}


def mark_doc_fixed(conn, repo_root: Path, *, path: str, reason: str | None = None) -> dict:
    rel_path = path
    cur = conn.execute(
        "SELECT doc_id, scope_type, scope_id, sources_json FROM docs_index WHERE path=?",
        (rel_path,),
    )
    row = cur.fetchone()
    if row is None:
        raise PfError(f"doc not indexed: {path}")

    fingerprint = compute_fingerprint(repo_root, json.loads(row["sources_json"]))
    now = utc_now_iso()
    conn.execute(
        """
        UPDATE docs_index
        SET stale=0,
            stale_reason=NULL,
            fingerprint_json=?,
            baseline_fingerprint_json=?,
            observed_fingerprint_json=?,
            last_checked_ts=?
        WHERE doc_id=?
        """,
        (
            json.dumps(fingerprint, ensure_ascii=False, sort_keys=True),
            json.dumps(fingerprint, ensure_ascii=False, sort_keys=True),
            json.dumps(fingerprint, ensure_ascii=False, sort_keys=True),
            now,
            row["doc_id"],
        ),
    )

    append_event(
        conn,
        event_type="doc.mark_fixed",
        scope_type=row["scope_type"],
        scope_id=row["scope_id"],
        actor="assistant",
        summary=f"doc fixed: {path}",
        payload={"path": path, "reason": reason or "manual_fix"},
    )

    return {"path": path, "stale": 0}
