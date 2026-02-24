"""Environment diagnostics."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from csk_next.io.runner import run_argv
from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.paths import Layout


def _is_forbidden_git_path(path: str) -> bool:
    normalized = path.strip().replace("\\", "/")
    if not normalized:
        return False

    if normalized == "AGENTS.md":
        return True
    if normalized.startswith(".csk/") or normalized.startswith(".agents/"):
        return True
    if normalized.endswith("/.csk") or "/.csk/" in normalized:
        return True
    if normalized.endswith(".pyc"):
        return True
    if normalized.endswith("/__pycache__") or "/__pycache__/" in normalized:
        return True
    return False


def _git_boundary_report(repo_root: Path) -> dict[str, Any]:
    in_repo = run_argv(["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"], check=False)
    if in_repo.returncode != 0:
        return {
            "enabled": False,
            "passed": True,
            "reason": "not_a_git_repository",
            "tracked_violations": [],
            "pending_violations": [],
        }

    tracked_result = run_argv(["git", "-C", str(repo_root), "ls-files"], check=False)
    tracked_files = tracked_result.stdout.splitlines() if tracked_result.returncode == 0 else []
    tracked_violations = sorted({path for path in tracked_files if _is_forbidden_git_path(path)})

    status_result = run_argv(
        ["git", "-C", str(repo_root), "status", "--porcelain", "--untracked-files=all"],
        check=False,
    )
    pending_files: list[str] = []
    if status_result.returncode == 0:
        for line in status_result.stdout.splitlines():
            if len(line) < 4:
                continue
            candidate = line[3:].strip()
            if " -> " in candidate:
                candidate = candidate.split(" -> ", 1)[1]
            pending_files.append(candidate.strip('"'))
    pending_violations = sorted({path for path in pending_files if _is_forbidden_git_path(path)})

    return {
        "enabled": True,
        "passed": not tracked_violations and not pending_violations,
        "reason": None,
        "tracked_violations": tracked_violations,
        "pending_violations": pending_violations,
    }


def run_doctor(layout: Layout, commands: list[str], git_boundary: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    python_ok = sys.version_info >= (3, 12)
    checks.append(
        {
            "name": "python_version",
            "passed": python_ok,
            "detail": sys.version,
        }
    )

    missing: list[str] = []
    for command in commands:
        present = shutil.which(command) is not None
        checks.append({"name": f"command:{command}", "passed": present})
        if not present:
            missing.append(command)

    boundary_report: dict[str, Any] | None = None
    if git_boundary:
        boundary_report = _git_boundary_report(layout.repo_root)
        checks.append(
            {
                "name": "git_boundary",
                "passed": boundary_report["passed"],
                "detail": boundary_report,
            }
        )
        if boundary_report["enabled"] and not boundary_report["passed"]:
            warnings.append("git_boundary violations detected; clean up before push")

    if missing:
        incident = make_incident(
            severity="medium",
            kind="command_not_found",
            phase="doctor",
            module_id=None,
            message=f"Missing commands: {', '.join(missing)}",
            remediation="Install missing commands or update profile verify/e2e commands.",
            context={"missing": missing},
        )
        log_incident(layout.app_incidents, incident)
    return {
        "status": "ok" if not missing and python_ok else "failed",
        "checks": checks,
        "missing": missing,
        "warnings": warnings,
        "git_boundary": boundary_report,
    }
