"""Module registry and scaffolding."""

from __future__ import annotations

from pathlib import Path

from pfpkg.errors import EXIT_NOT_FOUND, EXIT_VALIDATION, PfError
from pfpkg.events import append_event
from pfpkg.templates_store import load_template
from pfpkg.util_fs import ensure_dir, path_to_repo_relative
from pfpkg.util_time import utc_now_iso
from pfpkg.validation import (
    ensure_safe_module_id_or_raise,
    suggest_safe_module_id,
    validate_module_id_strict,
)


def sanitize_module_id(value: str) -> str:
    cleaned = suggest_safe_module_id(value)
    if not cleaned:
        raise PfError("unable to derive module id", EXIT_VALIDATION)
    return cleaned


def module_exists(conn, module_id: str) -> bool:
    cur = conn.execute("SELECT 1 FROM modules WHERE module_id=?", (module_id,))
    return cur.fetchone() is not None


def get_module(conn, module_id: str) -> dict:
    ensure_safe_module_id_or_raise(module_id, source="module lookup argument")
    cur = conn.execute("SELECT * FROM modules WHERE module_id=?", (module_id,))
    row = cur.fetchone()
    if row is None:
        raise PfError(f"module not found: {module_id}", EXIT_NOT_FOUND)
    module = dict(row)
    ensure_safe_module_id_or_raise(module["module_id"], source="modules table")
    return module


def upsert_module(conn, repo_root: Path, *, module_id: str, root_path: str, display_name: str) -> dict:
    module_id = validate_module_id_strict(module_id)
    if module_id == "root":
        root_path = "."
        display_name = display_name or "Root"

    abs_root = path_to_repo_relative(repo_root, root_path)
    rel_root = str(abs_root.relative_to(repo_root)) if abs_root != repo_root else "."

    cur = conn.execute(
        "SELECT module_id FROM modules WHERE root_path=? AND module_id<>?",
        (rel_root, module_id),
    )
    existing = cur.fetchone()
    if existing is not None:
        raise PfError(
            f"root_path '{rel_root}' already assigned to module '{existing['module_id']}'",
            EXIT_VALIDATION,
        )

    now = utc_now_iso()
    conn.execute(
        """
        INSERT INTO modules(module_id, root_path, display_name, initialized, created_ts, updated_ts)
        VALUES(?, ?, ?, 0, ?, ?)
        ON CONFLICT(module_id) DO UPDATE SET
          root_path=excluded.root_path,
          display_name=excluded.display_name,
          updated_ts=excluded.updated_ts
        """,
        (module_id, rel_root, display_name, now, now),
    )

    append_event(
        conn,
        event_type="module.upserted",
        scope_type="module",
        scope_id=module_id,
        actor="pf",
        summary=f"module upserted: {module_id}",
        payload={"module_id": module_id, "root_path": rel_root, "display_name": display_name},
    )

    return get_module(conn, module_id)


def list_modules(conn) -> list[dict]:
    cur = conn.execute(
        """
        SELECT module_id, root_path, display_name, initialized, created_ts, updated_ts
        FROM modules
        ORDER BY module_id ASC
        """
    )
    return [dict(r) for r in cur.fetchall()]


def detect_modules(repo_root: Path) -> list[dict]:
    candidates: list[dict] = []
    for prefix in ("services", "apps", "packages"):
        base = repo_root / prefix
        if not base.exists() or not base.is_dir():
            continue
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or child.name.startswith("."):
                continue
            rel = str(child.relative_to(repo_root))
            candidates.append(
                {
                    "module_id": sanitize_module_id(child.name),
                    "root_path": rel,
                    "reason": f"top-level candidate under {prefix}/",
                }
            )
    if not candidates:
        candidates.append(
            {
                "module_id": "root",
                "root_path": ".",
                "reason": "no conventional module folders found",
            }
        )
    return candidates


def _render(text: str, replacements: dict[str, str]) -> str:
    out = text
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def module_scaffold_paths(module_id: str) -> dict[str, str]:
    ensure_safe_module_id_or_raise(module_id, source="module scaffold path builder")
    return {
        "module_yaml": f".pf/modules/{module_id}/MODULE.yaml",
        "plan": f".pf/modules/{module_id}/PLAN.md",
        "knowledge": f".pf/modules/{module_id}/KNOWLEDGE.md",
        "decisions": f".pf/modules/{module_id}/DECISIONS.md",
        "docs_dir": f".pf/modules/{module_id}/DOCS",
        "retro_dir": f".pf/modules/{module_id}/RETRO",
        "tasks_dir": f".pf/modules/{module_id}/TASKS",
    }


def init_module(conn, repo_root: Path, *, module_id: str, write_scaffold: bool) -> dict:
    ensure_safe_module_id_or_raise(module_id, source="module init argument")
    module = get_module(conn, module_id)
    now = utc_now_iso()

    created_files: list[str] = []
    created_dirs: list[str] = []
    if write_scaffold:
        paths = module_scaffold_paths(module_id)
        for key in ("docs_dir", "retro_dir", "tasks_dir"):
            p = repo_root / paths[key]
            if not p.exists():
                ensure_dir(p)
                created_dirs.append(str(p.relative_to(repo_root)))

        module_yaml = repo_root / paths["module_yaml"]
        if not module_yaml.exists():
            module_yaml.write_text(
                (
                    "module_id: {module_id}\n"
                    "root_path: {root_path}\n"
                    "display_name: {display_name}\n"
                ).format(
                    module_id=module_id,
                    root_path=module["root_path"],
                    display_name=module["display_name"],
                ),
                encoding="utf-8",
            )
            created_files.append(str(module_yaml.relative_to(repo_root)))

        repl = {"<module_id>": module_id, "<root_path>": module["root_path"]}
        for rel_path, template_name in (
            (paths["plan"], "PLAN.md.template"),
            (paths["knowledge"], "KNOWLEDGE.md.template"),
            (paths["decisions"], "DECISIONS.md.template"),
        ):
            dest = repo_root / rel_path
            if not dest.exists():
                text = _render(load_template(repo_root, template_name), repl)
                dest.write_text(text, encoding="utf-8")
                created_files.append(rel_path)

    conn.execute(
        "UPDATE modules SET initialized=1, updated_ts=? WHERE module_id=?",
        (now, module_id),
    )

    append_event(
        conn,
        event_type="module.initialized",
        scope_type="module",
        scope_id=module_id,
        actor="pf",
        summary=f"module initialized: {module_id}",
        payload={
            "module_id": module_id,
            "write_scaffold": bool(write_scaffold),
            "created_files": created_files,
            "created_dirs": created_dirs,
        },
    )

    return {
        "module": get_module(conn, module_id),
        "created_files": created_files,
        "created_dirs": created_dirs,
    }
