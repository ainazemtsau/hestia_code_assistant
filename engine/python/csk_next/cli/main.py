"""CSK CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from csk_next.cli.parser import build_parser
from csk_next.eventlog.store import append_event
from csk_next.runtime.paths import resolve_layout


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _command_name(args: argparse.Namespace) -> str:
    parts: list[str] = []
    command = getattr(args, "command", None)
    if command:
        parts.append(str(command))
    for attr in [
        "wizard_cmd",
        "module_cmd",
        "mission_cmd",
        "task_cmd",
        "slice_cmd",
        "gate_cmd",
        "event_cmd",
        "incident_cmd",
        "retro_cmd",
        "update_cmd",
        "doctor_cmd",
    ]:
        value = getattr(args, attr, None)
        if value:
            parts.append(str(value))
    return " ".join(parts) if parts else "unknown"


def _command_scope(args: argparse.Namespace) -> dict[str, str | None]:
    return {
        "mission_id": getattr(args, "mission_id", None),
        "module_id": getattr(args, "module_id", None),
        "task_id": getattr(args, "task_id", None),
        "slice_id": getattr(args, "slice_id", None),
    }


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else list(sys.argv[1:])
    parser = build_parser()
    args = parser.parse_args(raw_argv)

    handler: Callable[[argparse.Namespace], dict[str, Any]] = args.handler
    layout = resolve_layout(args.root, args.state_root)
    command_name = _command_name(args)
    scope = _command_scope(args)

    append_event(
        layout=layout,
        event_type="command.started",
        actor="engine",
        mission_id=scope["mission_id"],
        module_id=scope["module_id"],
        task_id=scope["task_id"],
        slice_id=scope["slice_id"],
        payload={"command": command_name, "argv": raw_argv},
        worktree_path=str(layout.state_root),
    )

    try:
        payload = handler(args)
    except Exception as exc:  # noqa: BLE001
        try:
            append_event(
                layout=layout,
                event_type="command.completed",
                actor="engine",
                mission_id=scope["mission_id"],
                module_id=scope["module_id"],
                task_id=scope["task_id"],
                slice_id=scope["slice_id"],
                payload={
                    "command": command_name,
                    "result_status": "error",
                    "exit_code": 1,
                    "error": str(exc),
                },
                worktree_path=str(layout.state_root),
            )
        except Exception:  # noqa: BLE001
            pass
        payload = {"status": "error", "error": str(exc)}
        _print(payload)
        return 1

    failure_statuses = {"error", "failed", "gate_failed", "review_failed", "blocked"}
    exit_code = 0 if payload.get("status") not in failure_statuses else 1
    append_event(
        layout=layout,
        event_type="command.completed",
        actor="engine",
        mission_id=scope["mission_id"],
        module_id=scope["module_id"],
        task_id=scope["task_id"],
        slice_id=scope["slice_id"],
        payload={
            "command": command_name,
            "result_status": payload.get("status", "ok"),
            "exit_code": exit_code,
        },
        worktree_path=str(layout.state_root),
    )

    _print(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
