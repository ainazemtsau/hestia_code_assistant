"""Incident logging."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

from csk_next.domain.schemas import validate_schema
from csk_next.io.jsonl import append_jsonl
from csk_next.runtime.time import utc_now_iso


def make_incident(
    severity: str,
    kind: str,
    phase: str,
    message: str,
    remediation: str,
    module_id: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    incident = {
        "id": f"INC-{uuid.uuid4().hex[:12]}",
        "severity": severity,
        "kind": kind,
        "phase": phase,
        "module_id": module_id,
        "message": message,
        "remediation": remediation,
        "context": context or {},
        "created_at": utc_now_iso(),
    }
    validate_schema("incident", incident)
    return incident


def log_incident(path: Path, incident: dict[str, Any]) -> None:
    validate_schema("incident", incident)
    append_jsonl(path, incident)
