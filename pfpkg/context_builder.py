"""Deterministic bounded context bundle builder."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from pfpkg.artifacts import put_artifact
from pfpkg.docs_freshness import check_docs
from pfpkg.errors import EXIT_NOT_FOUND, EXIT_VALIDATION, PfError
from pfpkg.events import append_event
from pfpkg.focus import get_focus
from pfpkg.ids import next_bundle_id
from pfpkg.pkm import refresh_pkm_staleness
from pfpkg.util_fs import ensure_dir, path_to_repo_relative
from pfpkg.util_hash import sha256_file
from pfpkg.util_time import utc_now_iso
from pfpkg.validation import ensure_safe_module_id_or_raise, validate_module_id_strict


def _resolve_scope(conn, module: str | None) -> tuple[dict[str, str], Path]:
    if module:
        module = validate_module_id_strict(module)
        cur = conn.execute("SELECT module_id, root_path FROM modules WHERE module_id=?", (module,))
        row = cur.fetchone()
        if row is None:
            raise PfError(f"module not found: {module}", EXIT_NOT_FOUND)
        safe_module_id = ensure_safe_module_id_or_raise(row["module_id"], source="modules table")
        return {"type": "module", "id": safe_module_id}, Path(row["root_path"])

    focus = get_focus(conn)
    if focus.get("module_id"):
        cur = conn.execute("SELECT module_id, root_path FROM modules WHERE module_id=?", (focus["module_id"],))
        row = cur.fetchone()
        if row:
            safe_module_id = ensure_safe_module_id_or_raise(row["module_id"], source="focus/modules table")
            return {"type": "module", "id": safe_module_id}, Path(row["root_path"])

    return {"type": "root", "id": "root"}, Path(".")


def _task_id_from_args_or_focus(conn, task: str | None) -> str | None:
    if task:
        return task
    focus = get_focus(conn)
    return focus.get("task_id")


def _resolve_allowed_roots(
    repo_root: Path,
    module_root: Path,
    *,
    module_id: str | None,
    task_id: str | None,
) -> list[Path]:
    default = [module_root]
    if not module_id or not task_id:
        return default
    module_id = ensure_safe_module_id_or_raise(module_id, source="context allowed roots module_id")

    slices_path = repo_root / f".pf/modules/{module_id}/SLICES.json"
    if not slices_path.exists():
        return default

    try:
        payload = json.loads(slices_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default
    if not isinstance(payload, dict):
        return default
    slices = payload.get("slices")
    if not isinstance(slices, list):
        return default

    resolved: list[Path] = []
    for entry in slices:
        if not isinstance(entry, dict):
            continue
        if entry.get("task_id") != task_id:
            continue
        allowed_paths = entry.get("allowed_paths")
        if not isinstance(allowed_paths, list):
            continue
        for raw in allowed_paths:
            if not isinstance(raw, str):
                continue
            candidate = raw.strip()
            if not candidate:
                continue
            if "<module_root>" in candidate:
                candidate = candidate.replace("<module_root>", str(module_root))
            try:
                abs_path = path_to_repo_relative(repo_root, candidate)
            except PfError:
                continue
            if abs_path.exists() and abs_path.is_dir():
                resolved.append(Path(abs_path.relative_to(repo_root)))
            elif abs_path.exists() and abs_path.is_file():
                resolved.append(Path(abs_path.relative_to(repo_root)).parent)
            else:
                # Keep deterministic behavior and allow pre-created targets.
                resolved.append(Path(abs_path.relative_to(repo_root)))

    unique = sorted(set(resolved), key=lambda p: str(p))
    return unique or default


def _select_documents(repo_root: Path, scope: dict[str, str], task_id: str | None) -> list[dict[str, Any]]:
    docs: list[tuple[str, str]] = []
    if scope["type"] == "module":
        module_id = ensure_safe_module_id_or_raise(scope["id"], source="context scope id")
        if task_id:
            docs.append(("task", f".pf/modules/{module_id}/TASKS/{task_id}.md"))
        docs.extend(
            [
                ("plan", f".pf/modules/{module_id}/PLAN.md"),
                ("knowledge", f".pf/modules/{module_id}/KNOWLEDGE.md"),
                ("decisions", f".pf/modules/{module_id}/DECISIONS.md"),
            ]
        )
    else:
        docs.append(("agents", "AGENTS.md"))

    selected: list[dict[str, Any]] = []
    for kind, rel_path in docs:
        path = repo_root / rel_path
        if not path.exists() or not path.is_file():
            continue
        selected.append(
            {
                "kind": kind,
                "path": rel_path,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    return selected


def _recent_events(conn, scope: dict[str, str]) -> list[dict[str, Any]]:
    params: list[Any] = []
    where = ""
    if scope["type"] == "module":
        where = "WHERE scope_type='module' AND scope_id=?"
        params.append(scope["id"])

    cur = conn.execute(
        f"""
        SELECT event_id, ts, type, summary
        FROM events
        {where}
        ORDER BY event_id DESC
        LIMIT 20
        """,
        tuple(params),
    )
    selected = [dict(r) for r in cur.fetchall()]

    cur = conn.execute(
        """
        SELECT event_id, ts, type, summary
        FROM events
        WHERE type LIKE 'incident.%' OR type='incident.logged'
        ORDER BY event_id DESC
        LIMIT 10
        """
    )
    incidents = [dict(r) for r in cur.fetchall()]

    cur = conn.execute(
        """
        SELECT event_id, ts, type, summary
        FROM events
        WHERE type LIKE 'doc.%'
        ORDER BY event_id DESC
        LIMIT 10
        """
    )
    docs = [dict(r) for r in cur.fetchall()]

    merged = {e["event_id"]: e for e in [*selected, *incidents, *docs]}
    return [merged[k] for k in sorted(merged.keys(), reverse=True)]


def _select_pkm(conn, scope: dict[str, str], *, limit_module: int = 5, limit_global: int = 3) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []

    if scope["type"] == "module":
        cur = conn.execute(
            """
            SELECT pkm_id, title, kind, confidence, stale
            FROM pkm_items
            WHERE scope_type='module' AND scope_id=? AND stale=0
            ORDER BY confidence DESC, pkm_id DESC
            LIMIT ?
            """,
            (scope["id"], limit_module),
        )
        selected.extend([dict(r) for r in cur.fetchall()])

    cur = conn.execute(
        """
        SELECT pkm_id, title, kind, confidence, stale
        FROM pkm_items
        WHERE scope_type='global' AND scope_id='root' AND stale=0
        ORDER BY confidence DESC, pkm_id DESC
        LIMIT ?
        """,
        (limit_global,),
    )
    selected.extend([dict(r) for r in cur.fetchall()])
    return selected


def _extract_patterns(query: str | None, docs: list[dict[str, Any]], repo_root: Path) -> list[str]:
    patterns: list[str] = []

    if query:
        for token in re.findall(r"[A-Za-z0-9_./-]{3,}", query):
            patterns.append(token)

    for item in docs:
        path = repo_root / item["path"]
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        for token in re.findall(r"[A-Za-z0-9_./-]+\.[A-Za-z0-9]+", text):
            patterns.append(token)

    seen: set[str] = set()
    unique: list[str] = []
    for token in patterns:
        if token in seen:
            continue
        seen.add(token)
        unique.append(token)
        if len(unique) >= 6:
            break
    return unique


def _rg_hits(repo_root: Path, allowed_roots: list[Path], patterns: list[str]) -> list[tuple[str, int, str]]:
    if not patterns:
        return []
    if shutil.which("rg") is None:
        return []

    hits: list[tuple[str, int, str]] = []
    abs_allowed_roots = [(repo_root / root).resolve() for root in allowed_roots]
    for abs_allowed in abs_allowed_roots:
        for pat in patterns:
            cmd = [
                "rg",
                "-n",
                "--no-heading",
                "--color",
                "never",
                "--max-count",
                "60",
                "-e",
                pat,
                str(abs_allowed),
            ]
            proc = subprocess.run(
                cmd,
                cwd=repo_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if proc.returncode not in (0, 1):
                continue
            for raw in proc.stdout.splitlines():
                m = re.match(r"^(.+?):(\d+):(.*)$", raw)
                if not m:
                    continue
                path = Path(m.group(1)).resolve()
                try:
                    rel = str(path.relative_to(repo_root))
                except ValueError:
                    continue
                line_no = int(m.group(2))
                text = m.group(3)
                hits.append((rel, line_no, text))
                if len(hits) >= 200:
                    return sorted(hits)
    return sorted(hits)


def _snippets_from_hits(repo_root: Path, hits: list[tuple[str, int, str]], max_files: int = 8, windows_per_file: int = 3, window: int = 12) -> list[dict[str, Any]]:
    by_file: dict[str, list[int]] = {}
    for rel, line_no, _ in hits:
        by_file.setdefault(rel, []).append(line_no)

    ranked = sorted(by_file.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:max_files]

    snippets: list[dict[str, Any]] = []
    for rel, line_numbers in ranked:
        abs_path = repo_root / rel
        if not abs_path.exists() or not abs_path.is_file():
            continue
        lines = abs_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for target in sorted(set(line_numbers))[:windows_per_file]:
            start = max(1, target - window)
            end = min(len(lines), target + window)
            content = "\n".join(lines[start - 1 : end])
            snippets.append(
                {
                    "path": rel,
                    "start_line": start,
                    "end_line": end,
                    "reason": f"query hit near line {target}",
                    "content": content,
                }
            )
    return snippets


def _freshness_for_scope(conn, scope: dict[str, str]) -> dict[str, Any]:
    if scope["type"] == "module":
        cur = conn.execute(
            "SELECT path, stale_reason FROM docs_index WHERE scope_type='module' AND scope_id=? AND stale=1 ORDER BY path",
            (scope["id"],),
        )
    else:
        cur = conn.execute(
            "SELECT path, stale_reason FROM docs_index WHERE stale=1 ORDER BY path"
        )
    return {"stale_docs": [{"path": row["path"], "reason": row["stale_reason"]} for row in cur.fetchall()]}


def _bundle_size(selected: dict[str, Any]) -> int:
    return len(json.dumps(selected, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def _enforce_budget(selected: dict[str, Any], budget: int) -> None:
    while _bundle_size(selected) > budget and selected["code_snippets"]:
        selected["code_snippets"].pop()
    while _bundle_size(selected) > budget and len(selected["events"]) > 10:
        selected["events"] = selected["events"][:10]
    while _bundle_size(selected) > budget and len(selected["pkm"]) > 3:
        selected["pkm"] = selected["pkm"][:3]
    while _bundle_size(selected) > budget and len(selected["events"]) > 3:
        selected["events"] = selected["events"][: max(1, len(selected["events"]) - 1)]


def _min_required_selected(selected: dict[str, Any]) -> dict[str, Any]:
    return {
        "documents": selected["documents"],
        "pkm": [],
        "events": [],
        "code_snippets": [],
        "freshness": selected["freshness"],
    }


def _render_md(bundle: dict[str, Any]) -> str:
    selected = bundle["selected"]
    lines = [
        f"# Context Bundle {bundle['bundle_id']}",
        "",
        f"- intent: {bundle['intent']}",
        f"- scope: {bundle['scope']['type']}:{bundle['scope']['id']}",
        f"- budget_bytes: {bundle['budget_bytes']}",
        "",
        "## Documents",
    ]
    if selected["documents"]:
        for doc in selected["documents"]:
            lines.append(f"- {doc['kind']}: {doc['path']} ({doc['bytes']} bytes)")
    else:
        lines.append("- none")

    lines.append("\n## PKM")
    if selected["pkm"]:
        for item in selected["pkm"]:
            lines.append(f"- [{item['pkm_id']}] {item['title']} (confidence={item['confidence']})")
    else:
        lines.append("- none")

    lines.append("\n## Recent events")
    if selected["events"]:
        for event in selected["events"]:
            lines.append(f"- [{event['event_id']}] {event['type']}: {event['summary']}")
    else:
        lines.append("- none")

    lines.append("\n## Code snippets")
    if selected["code_snippets"]:
        for snippet in selected["code_snippets"]:
            lines.append(f"- {snippet['path']}:{snippet['start_line']}-{snippet['end_line']} ({snippet['reason']})")
    else:
        lines.append("- none")

    lines.append("\n## Freshness report")
    stale = selected["freshness"]["stale_docs"]
    if stale:
        for doc in stale:
            lines.append(f"- {doc['path']}: {doc['reason']}")
    else:
        lines.append("- no stale docs")

    return "\n".join(lines) + "\n"


def build_context_bundle(
    conn,
    repo_root: Path,
    *,
    intent: str,
    module: str | None,
    task: str | None,
    budget: int,
    query: str | None,
) -> dict:
    refresh_pkm_staleness(conn, repo_root)

    scope, module_root = _resolve_scope(conn, module)
    task_id = _task_id_from_args_or_focus(conn, task)
    allowed_roots = _resolve_allowed_roots(
        repo_root,
        module_root,
        module_id=scope["id"] if scope["type"] == "module" else None,
        task_id=task_id,
    )

    # Keep docs_index freshness up-to-date for this scope.
    if scope["type"] == "module":
        check_docs(conn, repo_root, scope="module", module_id=scope["id"])
    else:
        check_docs(conn, repo_root)

    documents = _select_documents(repo_root, scope, task_id)
    events = _recent_events(conn, scope)
    pkm = _select_pkm(conn, scope)

    patterns = _extract_patterns(query, documents, repo_root)
    hits = _rg_hits(repo_root, allowed_roots, patterns)
    snippets = _snippets_from_hits(repo_root, hits)

    selected = {
        "documents": documents,
        "pkm": pkm,
        "events": events,
        "code_snippets": snippets,
        "freshness": _freshness_for_scope(conn, scope),
    }

    min_required_budget = _bundle_size(_min_required_selected(selected))
    if budget < min_required_budget:
        raise PfError(
            f"budget too small: minimum required is {min_required_budget} bytes",
            EXIT_VALIDATION,
            details={"min_required_budget": min_required_budget},
        )
    _enforce_budget(selected, budget)
    if _bundle_size(selected) > budget:
        raise PfError(
            f"unable to fit bundle into budget {budget} bytes",
            EXIT_VALIDATION,
            details={"min_required_budget": _bundle_size(selected)},
        )

    bundle_id = next_bundle_id(conn)
    bundle = {
        "bundle_id": bundle_id,
        "ts": utc_now_iso(),
        "intent": intent,
        "scope": scope,
        "budget_bytes": budget,
        "selected": selected,
        "provenance": [
            {"section": "documents", "source": "filesystem:.pf/modules/..."},
            {
                "section": "events",
                "source": f"db:events(scope={scope['type']}:{scope['id']}, last=20)",
            },
            {"section": "pkm", "source": "db:pkm_items(stale=0, confidence desc)"},
            {"section": "freshness", "source": "db:docs_index + fingerprint check"},
            {
                "section": "code_snippets",
                "source": "rg within " + ", ".join(str(root) for root in allowed_roots),
            },
        ],
    }

    bundles_dir = repo_root / ".pf" / "artifacts" / "bundles"
    ensure_dir(bundles_dir)

    json_rel = f".pf/artifacts/bundles/{bundle_id}.json"
    md_rel = f".pf/artifacts/bundles/{bundle_id}.md"

    (repo_root / json_rel).write_text(json.dumps(bundle, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (repo_root / md_rel).write_text(_render_md(bundle), encoding="utf-8")

    json_art = put_artifact(conn, repo_root, kind="bundle", path_value=json_rel)
    md_art = put_artifact(conn, repo_root, kind="bundle", path_value=md_rel)

    append_event(
        conn,
        event_type="context.bundle_built",
        scope_type=scope["type"],
        scope_id=scope["id"],
        task_id=task_id,
        actor="pf",
        summary=f"context bundle built ({intent})",
        payload={
            "bundle_id": bundle_id,
            "intent": intent,
            "scope": scope,
            "task_id": task_id,
            "bytes": (repo_root / json_rel).stat().st_size,
            "budget": budget,
        },
        artifact_ids=[json_art["artifact_id"], md_art["artifact_id"]],
    )

    return {
        "bundle": bundle,
        "bundle_json": json_rel,
        "bundle_md": md_rel,
        "artifact_ids": [json_art["artifact_id"], md_art["artifact_id"]],
    }
