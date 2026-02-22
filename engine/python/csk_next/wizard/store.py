"""Wizard session persistence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.io.files import ensure_dir, read_json, write_json
from csk_next.io.jsonl import append_jsonl
from csk_next.runtime.paths import Layout
from csk_next.runtime.time import utc_now_iso
from csk_next.wizard.fsm import wizard_steps
from csk_next.wizard.models import WizardSession, WizardStep


def _wizard_root(layout: Layout) -> Path:
    root = layout.app / "wizards"
    ensure_dir(root)
    return root


def _next_session_id(layout: Layout) -> str:
    root = _wizard_root(layout)
    max_seen = 0
    for child in root.iterdir():
        if child.is_dir() and child.name.startswith("W-"):
            try:
                value = int(child.name.split("-")[1])
            except (IndexError, ValueError):
                continue
            max_seen = max(max_seen, value)
    return f"W-{max_seen + 1:04d}"


def _session_dir(layout: Layout, session_id: str) -> Path:
    path = _wizard_root(layout) / session_id
    ensure_dir(path)
    return path


def _session_path(layout: Layout, session_id: str) -> Path:
    return _session_dir(layout, session_id) / "session.json"


def _events_path(layout: Layout, session_id: str) -> Path:
    return _session_dir(layout, session_id) / "events.jsonl"


def _result_path(layout: Layout, session_id: str) -> Path:
    return _session_dir(layout, session_id) / "result.json"


def start_session(layout: Layout) -> WizardSession:
    session_id = _next_session_id(layout)
    now = utc_now_iso()
    session = WizardSession(
        session_id=session_id,
        status="in_progress",
        current_step_index=0,
        steps=wizard_steps(),
        context={},
        created_at=now,
        updated_at=now,
    )
    write_json(_session_path(layout, session_id), session.to_dict())
    append_event(layout, session_id, {"event": "session_started", "created_at": now})
    return session


def _step_from_data(data: dict[str, Any]) -> WizardStep:
    from csk_next.wizard.models import WizardOption

    return WizardStep(
        step_id=str(data["step_id"]),
        title=str(data["title"]),
        prompt=str(data["prompt"]),
        input_hint=str(data["input_hint"]),
        options=[
            WizardOption(
                value=str(opt["value"]),
                label=str(opt["label"]),
                description=str(opt["description"]),
            )
            for opt in data.get("options", [])
        ],
        recommended=data.get("recommended"),
        unchanged=list(data.get("unchanged", [])),
    )


def load_session(layout: Layout, session_id: str) -> WizardSession:
    data = read_json(_session_path(layout, session_id))
    return WizardSession(
        session_id=str(data["session_id"]),
        status=str(data["status"]),
        current_step_index=int(data["current_step_index"]),
        steps=[_step_from_data(step) for step in data["steps"]],
        context=dict(data.get("context", {})),
        created_at=str(data["created_at"]),
        updated_at=str(data["updated_at"]),
    )


def save_session(layout: Layout, session: WizardSession) -> None:
    session.updated_at = utc_now_iso()
    write_json(_session_path(layout, session.session_id), session.to_dict())


def append_event(layout: Layout, session_id: str, payload: dict[str, Any]) -> None:
    row = {
        "session_id": session_id,
        "recorded_at": utc_now_iso(),
        **payload,
    }
    append_jsonl(_events_path(layout, session_id), row)


def save_result(layout: Layout, session_id: str, result: dict[str, Any]) -> None:
    write_json(_result_path(layout, session_id), result)


def load_result(layout: Layout, session_id: str) -> dict[str, Any] | None:
    path = _result_path(layout, session_id)
    if not path.exists():
        return None
    return read_json(path)
