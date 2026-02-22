"""Environment diagnostics."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.paths import Layout


def run_doctor(layout: Layout, commands: list[str]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

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
    }
