"""Slice failure and status policies."""

from __future__ import annotations

from typing import Any

from csk_next.eventlog.store import append_event
from csk_next.io.jsonl import append_jsonl
from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.tasks import task_dir
from csk_next.runtime.tasks_engine import mark_task_blocked, update_slice_state


def fail_slice(
    *,
    layout,
    module_path: str,
    module_id: str,
    task_id: str,
    slice_id: str,
    attempts: int,
    kind: str,
    severity: str,
    phase: str,
    message: str,
    remediation: str,
    context: dict[str, Any],
    status: str,
    gate: str,
    last_error: str,
    block_task: bool = False,
    blocked_reason: str | None = None,
) -> dict[str, Any]:
    incident = make_incident(
        severity=severity,
        kind=kind,
        phase=phase,
        module_id=module_id,
        message=message,
        remediation=remediation,
        context=context,
    )
    log_incident(layout.app_incidents, incident)
    append_jsonl(task_dir(layout, module_path, task_id) / "incidents.jsonl", incident)
    append_event(
        layout=layout,
        event_type="incident.logged",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        slice_id=slice_id,
        payload={"incident_id": incident["id"], "kind": kind, "severity": severity, "phase": phase},
        artifact_refs=[str(layout.app_incidents), str(task_dir(layout, module_path, task_id) / "incidents.jsonl")],
    )
    update_slice_state(
        layout=layout,
        module_path=module_path,
        task_id=task_id,
        slice_id=slice_id,
        status=status,
        attempts=attempts,
        last_error=last_error,
    )
    if block_task:
        mark_task_blocked(layout, module_path, task_id, blocked_reason or last_error)
    return {"status": status, "gate": gate, "incident": incident}
