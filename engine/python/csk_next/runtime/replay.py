"""Replay/invariant checks from event log."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.eventlog.store import query_events
from csk_next.io.files import read_json
from csk_next.runtime.paths import Layout


def _exists(path: str | None) -> bool:
    if not path:
        return False
    return Path(path).exists()


def replay_check(layout: Layout) -> dict[str, Any]:
    events = query_events(layout=layout, limit=5000)
    violations: list[str] = []
    checks: list[dict[str, Any]] = []

    for event in events:
        event_id = str(event["id"])
        event_type = str(event["type"])
        payload = event.get("payload", {})

        if event_type == "proof.pack.written":
            manifest_path = str(payload.get("manifest_path", ""))
            passed = _exists(manifest_path)
            checks.append({"event_id": event_id, "name": "proof_manifest_exists", "passed": passed})
            if not passed:
                violations.append(f"{event_id}: missing manifest {manifest_path}")

        if event_type == "ready.approved":
            ready_path = str(payload.get("ready_proof_path", ""))
            passed = _exists(ready_path)
            checks.append({"event_id": event_id, "name": "ready_proof_exists", "passed": passed})
            if not passed:
                violations.append(f"{event_id}: missing ready proof {ready_path}")

        if event_type == "retro.completed":
            retro_file = str(payload.get("retro_file", ""))
            passed = _exists(retro_file)
            checks.append({"event_id": event_id, "name": "retro_file_exists", "passed": passed})
            if not passed:
                violations.append(f"{event_id}: missing retro file {retro_file}")

    status = "ok" if not violations else "failed"
    return {"status": status, "checks": checks, "violations": violations}
