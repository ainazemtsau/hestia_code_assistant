"""Retro generation."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import append_event
from csk_next.io.files import ensure_dir, write_text
from csk_next.io.jsonl import read_jsonl
from csk_next.runtime.paths import Layout
from csk_next.runtime.tasks import task_dir
from csk_next.runtime.tasks_engine import mark_task_status, read_task_state


_CLUSTER_MAP = {
    "env": {"command_not_found", "environment", "doctor"},
    "toolchain": {"verify_fail", "e2e_fail", "implement_fail"},
    "plan": {"scope_violation", "drift", "freeze"},
    "test": {"e2e_missing", "verify_fail"},
    "process": {"token_waste", "review_fail"},
}


def _cluster_for(kind: str) -> str:
    for cluster, values in _CLUSTER_MAP.items():
        if kind in values:
            return cluster
    return "process"


def run_retro(layout: Layout, module_id: str, task_id: str, feedback: str) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    module_path = module["path"]

    state = read_task_state(layout, module_path, task_id)
    if state["status"] not in {"ready_approved", "blocked"}:
        raise ValueError(
            f"Retro requires task status ready_approved or blocked, got '{state['status']}'"
        )

    incidents = read_jsonl(layout.app_incidents)
    related = [row for row in incidents if row.get("context", {}).get("task_id") == task_id]

    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in related:
        clusters[_cluster_for(str(row.get("kind", "")))].append(row)

    task_root = task_dir(layout, module_path, task_id)
    lines = [f"# Retro for {task_id}", "", "## Clusters"]
    for cluster in ["env", "toolchain", "plan", "test", "process"]:
        lines.append(f"### {cluster}")
        items = clusters.get(cluster, [])
        if not items:
            lines.append("- no incidents")
        else:
            for item in items:
                lines.append(f"- {item['kind']}: {item['message']}")
        lines.append("")

    lines.extend(
        [
            "## Patch proposals",
            "- Update local profile gates/commands for recurring failures.",
            "- Add local skill overrides for common remediation steps.",
            "- Add doctor checks for missing dependencies.",
            "",
            "## User feedback",
            f"- {feedback or 'none'}",
        ]
    )
    write_text(task_root / "retro.md", "\n".join(lines) + "\n")

    patch_dir = layout.local / "patches"
    ensure_dir(patch_dir)
    patch_file = patch_dir / f"{task_id}-{state['updated_at'].replace(':', '').replace('-', '')}.md"
    write_text(
        patch_file,
        "# Local patch proposals\n\n- Tune profile verify commands.\n- Improve skill prompts.\n",
    )

    mark_task_status(layout, module_path, task_id, "retro_done")
    retro_file = str(task_root / "retro.md")
    patch_file_str = str(patch_file)
    append_event(
        layout=layout,
        event_type="retro.completed",
        actor="engine",
        module_id=module_id,
        task_id=task_id,
        payload={
            "task_id": task_id,
            "incidents": len(related),
            "retro_file": retro_file,
            "patch_file": patch_file_str,
        },
        artifact_refs=[retro_file, patch_file_str],
    )

    return {
        "status": "ok",
        "task_id": task_id,
        "incidents": len(related),
        "retro_file": retro_file,
        "patch_file": patch_file_str,
    }
