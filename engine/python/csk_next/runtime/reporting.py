"""Manager report generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry
from csk_next.eventlog.store import query_events
from csk_next.io.files import ensure_dir, read_json, write_json, write_text
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso
from csk_next.skills.generator import validate_generated_skills


def _engine_version(layout: Layout) -> str:
    version = layout.engine / "VERSION"
    if not version.exists():
        return "unknown"
    return version.read_text(encoding="utf-8").strip() or "unknown"


def _task_states(layout: Layout, module_path: str) -> list[dict[str, Any]]:
    root = layout.module_tasks(module_path)
    if not root.exists():
        return []
    rows: list[dict[str, Any]] = []
    for task_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        task_path = task_dir / "task.json"
        if not task_path.exists():
            continue
        rows.append(read_json(task_path))
    return rows


def _report_counters(layout: Layout, registry: dict[str, Any]) -> dict[str, int]:
    missions_total = len([path for path in layout.missions.iterdir() if path.is_dir()]) if layout.missions.exists() else 0
    tasks_total = 0
    slices_total = 0
    proof_packs_total = 0
    retro_total = 0

    for module in registry.get("modules", []):
        module_path = str(module.get("path", "."))
        task_states = _task_states(layout, module_path)
        tasks_total += len(task_states)
        for state in task_states:
            slices = state.get("slices", {})
            if isinstance(slices, dict):
                slices_total += len(slices)
            task_id = state.get("task_id")
            if isinstance(task_id, str):
                retro_file = layout.module_tasks(module_path) / task_id / "retro.md"
                if retro_file.exists():
                    retro_total += 1
        task_run_root = layout.module_run(module_path) / "tasks"
        if task_run_root.exists():
            proof_packs_total += sum(1 for path in task_run_root.rglob("manifest.json") if path.is_file())

    return {
        "missions_total": missions_total,
        "tasks_total": tasks_total,
        "slices_total": slices_total,
        "proof_packs_total": proof_packs_total,
        "retro_total": retro_total,
    }


def _non_ok_events(layout: Layout, limit: int = 20) -> list[dict[str, Any]]:
    events = query_events(layout=layout, limit=5000)
    rows: list[dict[str, Any]] = []
    for event in events:
        event_type = str(event.get("type", ""))
        payload = event.get("payload", {})
        if event_type == "command.completed":
            result_status = str(payload.get("result_status", ""))
            if result_status in {"ok", "done"}:
                continue
            rows.append(
                {
                    "id": str(event.get("id")),
                    "ts": str(event.get("ts")),
                    "type": event_type,
                    "command": str(payload.get("command", "")),
                    "result_status": result_status,
                    "exit_code": payload.get("exit_code"),
                    "module_id": event.get("module_id"),
                    "task_id": event.get("task_id"),
                    "slice_id": event.get("slice_id"),
                }
            )
            continue
        if event_type.endswith(".failed"):
            rows.append(
                {
                    "id": str(event.get("id")),
                    "ts": str(event.get("ts")),
                    "type": event_type,
                    "command": "",
                    "result_status": "failed",
                    "exit_code": None,
                    "module_id": event.get("module_id"),
                    "task_id": event.get("task_id"),
                    "slice_id": event.get("slice_id"),
                }
            )
    return rows[:limit]


def _write_recent_commands_transcript(layout: Layout, report_dir: Path, ts_compact: str) -> Path:
    events = query_events(layout=layout, limit=200)
    lines = ["# Recent CLI Transcript", ""]
    for event in sorted(events, key=lambda row: (str(row.get("ts", "")), str(row.get("id", "")))):
        event_type = str(event.get("type", ""))
        payload = event.get("payload", {})
        if event_type == "command.started":
            continue
        if event_type != "command.completed":
            continue
        command = str(payload.get("command", ""))
        exit_code = payload.get("exit_code")
        result_status = str(payload.get("result_status", ""))
        lines.append(f"- {event.get('ts')} command={command} status={result_status} exit_code={exit_code}")
    transcript_path = report_dir / f"transcript-last-commands-{ts_compact}.md"
    write_text(transcript_path, "\n".join(lines) + "\n")
    return transcript_path


def _transcript_refs(layout: Layout, transcript_path: Path) -> list[str]:
    refs: list[str] = []
    candidates = [
        layout.repo_root / "docs" / "acceptance" / "A_GREENFIELD_TRANSCRIPT.md",
        layout.repo_root
        / "docs"
        / "remediation_2026-02-26"
        / "phase-04-wizard-scripted-routing"
        / "SCRIPTED_TRANSCRIPT.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            refs.append(str(candidate))
    refs.append(str(transcript_path))
    return refs[:5]


def manager_report_v2(layout: Layout) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    counters = _report_counters(layout, registry)
    non_ok = _non_ok_events(layout)
    ts = utc_now_iso()
    ts_compact = ts.replace(":", "").replace("-", "")
    report_dir = layout.app / "reports"
    ensure_dir(report_dir)
    transcript_path = _write_recent_commands_transcript(layout, report_dir, ts_compact)

    skills = validate_generated_skills(
        engine_skills_src=layout.engine / "skills_src",
        local_override=layout.local / "skills_override",
        output_dir=layout.agents_skills,
    )
    local_config = layout.local / "config.json"
    report = {
        "version": "2",
        "generated_at": ts,
        "engine": {"version": _engine_version(layout)},
        "overlay": {
            "local_config_path": str(local_config),
            "local_config_exists": local_config.exists(),
            "skills_drift_status": str(skills.get("status", "unknown")),
        },
        "counters": counters,
        "non_ok_events": non_ok,
        "transcript_refs": _transcript_refs(layout, transcript_path),
        "skills": skills,
    }
    report_path = report_dir / f"manager-report-v2-{ts_compact}.json"
    write_json(report_path, report)
    return {
        "status": "ok",
        "report": report,
        "path": str(report_path),
        "artifact_refs": [str(report_path), str(transcript_path)],
    }
