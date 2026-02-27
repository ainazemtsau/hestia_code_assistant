"""Engine update workflow."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from csk_next.io.files import copy_tree, ensure_dir
from csk_next.runtime.bootstrap import bundled_engine_pack_path
from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.paths import Layout
from csk_next.runtime.validation import ValidationError, validate_all
from csk_next.skills.generator import generate_skills


def update_engine(layout: Layout) -> dict[str, Any]:
    if not layout.engine.exists():
        raise FileNotFoundError("Engine is not initialized. Run csk bootstrap first.")

    backup = layout.csk / "engine.backup"
    if backup.exists():
        shutil.rmtree(backup)

    shutil.copytree(layout.engine, backup)

    try:
        shutil.rmtree(layout.engine)
        ensure_dir(layout.engine)
        copy_tree(bundled_engine_pack_path(), layout.engine)

        generate_skills(
            engine_skills_src=layout.engine / "skills_src",
            local_override=layout.local / "skills_override",
            output_dir=layout.agents_skills,
        )

        validate_all(layout, strict=True)
        shutil.rmtree(backup)
        return {
            "status": "ok",
            "engine_updated": True,
            "backup_path": str(backup),
            "backup_removed": True,
            "validate_status": "ok",
        }
    except Exception as exc:  # noqa: BLE001
        if layout.engine.exists():
            shutil.rmtree(layout.engine)
        shutil.copytree(backup, layout.engine)
        incident = make_incident(
            severity="high",
            kind="update_fail",
            phase="update",
            module_id=None,
            message=f"Engine update failed: {exc}",
            remediation="Rollback applied. Inspect validation output and retry.",
            context={},
        )
        log_incident(layout.app_incidents, incident)
        return {
            "status": "failed",
            "rolled_back": True,
            "error": str(exc),
            "incident": incident,
            "backup_path": str(backup),
        }
