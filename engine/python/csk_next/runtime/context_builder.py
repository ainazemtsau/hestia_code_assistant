"""Context Builder v1 (lexical + provenance)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import append_event, query_events
from csk_next.io.files import ensure_dir, read_json, read_text, write_json
from csk_next.io.runner import run_argv
from csk_next.runtime.paths import Layout
from csk_next.runtime.tasks import slices_path, task_dir, task_run_dir
from csk_next.runtime.time import utc_now_iso


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z0-9_]{3,}", text.lower())
    return words


def _plan_brief(plan_text: str, max_lines: int = 120) -> dict[str, Any]:
    lines = plan_text.splitlines()
    selected = lines[:max_lines]
    headings = [line.strip() for line in selected if line.strip().startswith("#")]
    return {"headings": headings, "excerpt": "\n".join(selected)}


def _collect_allowed_paths(slices_doc: dict[str, Any]) -> list[str]:
    allowed: set[str] = set()
    for item in slices_doc.get("slices", []):
        for path in item.get("allowed_paths", []):
            value = _normalize_allowed_path(str(path))
            if value:
                allowed.add(value)
    return sorted(allowed)


def _normalize_allowed_path(raw_path: str) -> str:
    value = raw_path.strip().replace("\\", "/")
    if not value:
        return ""
    if value in {".", "./"}:
        return "."
    while value.startswith("./"):
        value = value[2:]
    value = value.strip("/")
    return value or "."


def _is_allowed_relpath(rel_path: str, allowed_paths: list[str]) -> bool:
    if not allowed_paths:
        return True
    for prefix in allowed_paths:
        if prefix == ".":
            return True
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            return True
    return False


def _candidate_files(module_root: Path, allowed_paths: list[str]) -> list[Path]:
    candidates: list[Path] = []
    git = run_argv(["git", "-C", str(module_root), "ls-files"], check=False)
    if git.returncode == 0:
        for raw in git.stdout.splitlines():
            rel = raw.strip()
            if not rel:
                continue
            if not _is_allowed_relpath(rel, allowed_paths):
                continue
            path = module_root / rel
            if path.exists() and path.is_file():
                candidates.append(path)
    else:
        for path in sorted(module_root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(module_root).as_posix()
            if not _is_allowed_relpath(rel, allowed_paths):
                continue
            candidates.append(path)
    return candidates


def _read_head(path: Path, max_lines: int = 300, max_bytes: int = 64000) -> tuple[str, int]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return "", 0
    if len(text.encode("utf-8", errors="ignore")) > max_bytes:
        text = text[:max_bytes]
    lines = text.splitlines()
    return "\n".join(lines[:max_lines]), min(len(lines), max_lines)


def _file_score(rel: str, head: str, keywords: list[str]) -> int:
    rel_l = rel.lower()
    head_l = head.lower()
    score = 0
    for word in keywords:
        if word in rel_l:
            score += 3
        if word in head_l:
            score += 1
    return score


def _recent_evidence(layout: Layout, module_id: str, task_id: str, limit: int = 20) -> list[dict[str, Any]]:
    rows = query_events(layout=layout, limit=limit, module_id=module_id, task_id=task_id)
    selected: list[dict[str, Any]] = []
    for row in rows:
        if row["type"] in {
            "verify.failed",
            "verify.passed",
            "scope.check.failed",
            "scope.check.passed",
            "proof.pack.written",
            "slice.completed",
        }:
            selected.append(
                {
                    "event_id": row["id"],
                    "type": row["type"],
                    "ts": row["ts"],
                    "payload": row["payload"],
                    "source": {"event_id": row["id"]},
                }
            )
    return selected


def _runbook_items(layout: Layout, module_id: str, top_n: int = 3) -> list[dict[str, Any]]:
    pkm_path = layout.app / "pkm" / "items.json"
    if not pkm_path.exists():
        return []
    doc = read_json(pkm_path)
    items = doc.get("items", [])
    selected = [item for item in items if str(item.get("module_id", module_id)) == module_id][:top_n]
    result: list[dict[str, Any]] = []
    for item in selected:
        result.append(
            {
                "id": item.get("id"),
                "claim": item.get("claim"),
                "confidence": item.get("confidence"),
                "staleness": item.get("staleness"),
                "source": {"event_ids": list(item.get("justifications", []))},
            }
        )
    return result


def _freshness(layout: Layout, module_root: Path, allowed_paths: list[str], created_ts: str) -> dict[str, Any]:
    head = run_argv(["git", "-C", str(module_root), "rev-parse", "HEAD"], check=False)
    repo_head = head.stdout.strip() if head.returncode == 0 else None
    diff = run_argv(["git", "-C", str(module_root), "diff", "--name-only"], check=False)
    changed = [line.strip() for line in diff.stdout.splitlines() if line.strip()] if diff.returncode == 0 else []
    changed_allowed = changed
    if allowed_paths:
        changed_allowed = [p for p in changed if _is_allowed_relpath(p, allowed_paths)]
    hint = "possibly_stale" if changed_allowed else "fresh"
    return {"repo_head": repo_head, "bundle_created_ts": created_ts, "staleness_hint": hint}


def build_context_bundle(*, layout: Layout, module_id: str, task_id: str, budget: int = 3200) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    module_path = str(module["path"])
    module_root = layout.module_root(module_path)
    task_root = task_dir(layout, module_path, task_id)
    run_dir = task_run_dir(layout, module_path, task_id)
    context_dir = run_dir / "context"
    ensure_dir(context_dir)

    plan = read_text(task_root / "plan.md")
    slices_doc = read_json(slices_path(layout, module_path, task_id))
    plan_brief = _plan_brief(plan)
    allowed_paths = _collect_allowed_paths(slices_doc)
    evidence = _recent_evidence(layout, module_id, task_id, limit=30)

    keywords = _tokenize(plan_brief["excerpt"])
    for row in evidence:
        keywords.extend(_tokenize(json_payload_text(row.get("payload"))))
    keywords = keywords[:200]

    scored: list[tuple[int, dict[str, Any]]] = []
    for path in _candidate_files(module_root, allowed_paths):
        rel = path.relative_to(module_root).as_posix()
        head_text, line_count = _read_head(path)
        score = _file_score(rel, head_text, keywords)
        if score <= 0:
            continue
        scored.append(
            (
                score,
                {
                    "path": rel,
                    "score": score,
                    "excerpt": head_text[:2000],
                    "source": {"path": rel, "start_line": 1, "end_line": line_count},
                },
            )
        )
    scored.sort(key=lambda row: (row[0], row[1]["path"]), reverse=True)
    relevant_files = [row[1] for row in scored[:10]]

    now = utc_now_iso()
    bundle = {
        "algo_version": "cb.v1",
        "module_id": module_id,
        "task_id": task_id,
        "budget": budget,
        "task_brief": {
            "headings": plan_brief["headings"],
            "excerpt": plan_brief["excerpt"][: max(500, budget)],
            "source": {"path": str(task_root / "plan.md"), "start_line": 1, "end_line": len(plan.splitlines())},
        },
        "allowed_paths": [{"path": item, "source": {"path": str(task_root / "slices.json")}} for item in allowed_paths],
        "relevant_files": relevant_files,
        "recent_evidence": evidence,
        "runbook": _runbook_items(layout, module_id, top_n=5),
        "freshness": _freshness(layout, module_root, allowed_paths, now),
        "created_at": now,
    }

    bundle_path = context_dir / f"bundle-{now.replace(':', '').replace('-', '')}.json"
    write_json(bundle_path, bundle)
    append_event(
        layout=layout,
        event_type="context.bundle.built",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        payload={"algo_version": "cb.v1", "budget": budget, "bundle_path": str(bundle_path)},
        artifact_refs=[str(bundle_path)],
    )
    return {"status": "ok", "bundle": bundle, "bundle_path": str(bundle_path)}


def json_payload_text(payload: Any) -> str:
    if isinstance(payload, dict):
        parts: list[str] = []
        for key, value in payload.items():
            parts.append(str(key))
            parts.append(str(value))
        return " ".join(parts)
    return str(payload)
