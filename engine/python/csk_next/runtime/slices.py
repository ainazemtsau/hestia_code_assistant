"""Public slice APIs."""

from __future__ import annotations

from csk_next.domain.state import ensure_registry, find_module
from csk_next.runtime.paths import Layout
from csk_next.runtime.slice_executor import execute_slice
from csk_next.runtime.tasks_engine import update_slice_state


def slice_run(**kwargs):
    """Execute one slice through gated workflow."""
    return execute_slice(**kwargs)


def slice_mark(
    *,
    layout: Layout,
    module_id: str,
    task_id: str,
    slice_id: str,
    status: str,
    note: str,
) -> dict[str, str]:
    """Mark slice status explicitly with audit note."""
    registry = ensure_registry(layout.registry)
    module = find_module(registry, module_id)
    module_path = module["path"]

    update_slice_state(
        layout=layout,
        module_path=module_path,
        task_id=task_id,
        slice_id=slice_id,
        status=status,
        last_error=note,
    )
    return {
        "status": "ok",
        "slice_id": slice_id,
        "marked_status": status,
        "note": note,
    }
