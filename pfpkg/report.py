"""Manager-facing report."""

from __future__ import annotations

import json
from pathlib import Path

from pfpkg.projections import event_count, last_incidents, modules_summary
from pfpkg.status import build_status


def _review_gate(conn) -> bool:
    cur = conn.execute("SELECT 1 FROM events WHERE type='review.completed' ORDER BY event_id DESC LIMIT 1")
    return cur.fetchone() is not None


def _tests_gate(conn) -> bool:
    cur = conn.execute(
        "SELECT payload_json FROM events WHERE type='command.completed' ORDER BY event_id DESC LIMIT 1"
    )
    row = cur.fetchone()
    if not row:
        return False
    payload = json.loads(row["payload_json"])
    return payload.get("exit_code") == 0


def build_manager_report(conn, db_path: Path) -> dict:
    status = build_status(conn, db_path)
    modules = modules_summary(conn)

    report = {
        "status": {
            "initialized": status["initialized"],
            "active_mission": status["active_mission"],
            "focus": status["focus"],
            "stale_docs_count": status["stale_docs_count"],
        },
        "modules": {
            "count": len(modules),
            "items": modules,
        },
        "counters": {
            "events": event_count(conn),
            "incidents": len(last_incidents(conn, limit=1000)),
        },
        "gates": {
            "plan_approved": bool(status.get("plan_approved")),
            "tests_ok": _tests_gate(conn),
            "review_ok": _review_gate(conn),
        },
        "risks": last_incidents(conn, limit=3),
        "next": status["next"],
    }
    return report


def render_manager_report_human(report: dict) -> list[str]:
    status = report["status"]
    lines = [
        "Manager report",
        f"Init: {'yes' if status['initialized'] else 'no'}",
        f"Active mission: {status['active_mission']['mission_id'] if status['active_mission'] else 'none'}",
        f"Focus: module={status['focus'].get('module_id') or 'none'} task={status['focus'].get('task_id') or 'none'}",
        f"Modules: {report['modules']['count']}",
        f"Events: {report['counters']['events']}",
        f"Docs stale: {status['stale_docs_count']}",
        "Gates:",
        f"- plan_approved: {report['gates']['plan_approved']}",
        f"- tests_ok: {report['gates']['tests_ok']}",
        f"- review_ok: {report['gates']['review_ok']}",
        "",
        f"NEXT ({'CLI' if report['next']['kind']=='cli' else 'Codex'}): {report['next']['cmd']}",
        f"WHY: {report['next']['why']}",
    ]
    if report["risks"]:
        lines.append("Recent risks/incidents:")
        for item in report["risks"]:
            lines.append(f"- [{item['event_id']}] {item['summary']}")
    return lines
