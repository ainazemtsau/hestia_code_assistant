"""Doctor checks for local pf health."""

from __future__ import annotations

from pathlib import Path

from pfpkg.db import connect_db, require_initialized
from pfpkg.templates_store import SKILL_REL_PATHS
from pfpkg.util_time import utc_now_iso


def _collect_guardrail_files(repo_root: Path) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for root_name in ("scripts", "tools"):
        root = repo_root / root_name
        if not root.exists() or not root.is_dir():
            continue
        for file_path in sorted(root.rglob("*")):
            if file_path.is_file():
                out.append((str(file_path.relative_to(repo_root)), root_name))
    return out


def seed_doctor_baseline(conn, repo_root: Path) -> None:
    cur = conn.execute("SELECT COUNT(*) AS c FROM doctor_baseline")
    if int(cur.fetchone()["c"]) > 0:
        return
    now = utc_now_iso()
    rows = _collect_guardrail_files(repo_root)
    conn.executemany(
        "INSERT OR IGNORE INTO doctor_baseline(path, kind, created_ts) VALUES(?, ?, ?)",
        [(path, kind, now) for path, kind in rows],
    )


def run_doctor(repo_root: Path, db_path: Path) -> dict:
    checks: list[dict] = []

    try:
        require_initialized(db_path)
        checks.append({"name": "initialized", "ok": True, "message": ".pf/state.db exists"})
    except Exception as exc:
        checks.append({"name": "initialized", "ok": False, "message": str(exc)})
        return {"ok": False, "checks": checks, "warnings": []}

    conn = None
    baseline: set[str] = set()
    db_access_ok = False
    try:
        conn = connect_db(db_path)
        conn.execute("SELECT 1")
        seed_doctor_baseline(conn, repo_root)
        conn.commit()
        baseline = {
            row["path"]
            for row in conn.execute("SELECT path FROM doctor_baseline ORDER BY path").fetchall()
        }
        db_access_ok = True
        checks.append({"name": "db_access", "ok": True, "message": "sqlite reachable"})
    except Exception as exc:
        checks.append({"name": "db_access", "ok": False, "message": str(exc)})
    finally:
        if conn is not None:
            conn.close()
            conn = None

    missing_skills = []
    for rel in SKILL_REL_PATHS:
        path = repo_root / ".agents" / rel
        if not path.exists():
            missing_skills.append(str(path.relative_to(repo_root)))
    checks.append(
        {
            "name": "skills_pack",
            "ok": not missing_skills,
            "message": "all skills present" if not missing_skills else f"missing {len(missing_skills)} skill files",
            "missing": missing_skills,
        }
    )

    warnings: list[str] = []
    if db_access_ok:
        current = _collect_guardrail_files(repo_root)
        for path, kind in current:
            if path not in baseline:
                warnings.append(f"new file under {kind}/ not in baseline: {path}")
    else:
        warnings.append("guardrail baseline comparison skipped: db_access check failed")

    overall_ok = all(c.get("ok") for c in checks)
    return {"ok": overall_ok, "checks": checks, "warnings": warnings}
