"""CSK CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from csk_next.cli.parser import build_parser
from csk_next.eventlog.store import append_event
from csk_next.runtime.paths import resolve_layout


_MODULE_SUBCOMMANDS = {"list", "show", "add", "init", "status"}


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _render_list(values: list[str]) -> str:
    if not values:
        return "-"
    return "; ".join(values)


def _print_status_text(payload: dict[str, Any]) -> None:
    summary = payload.get("summary", {})
    modules = payload.get("modules", [])
    next_block = payload.get("next", {})
    print("SUMMARY")
    print(
        f"bootstrapped={summary.get('bootstrapped')} "
        f"mission={summary.get('active_mission_id')} "
        f"milestone={summary.get('active_milestone_id')} "
        f"modules={summary.get('modules_total')}"
    )
    print("")
    print("STATUS")
    if not modules:
        print("- no modules")
    else:
        for module in modules:
            progress = (
                f"{module.get('slices_done', 0)}/{module.get('slices_total', 0)}"
                if module.get("active_task_id")
                else "-"
            )
            print(
                f"- {module.get('module_id')}: phase={module.get('phase')} "
                f"task={module.get('active_task_id')} slice={module.get('active_slice_id')} progress={progress}"
            )
    print("")
    print("NEXT")
    print(next_block.get("recommended", "-"))
    alternatives = next_block.get("alternatives", [])
    if isinstance(alternatives, list) and alternatives:
        print(f"ALT: {_render_list([str(item) for item in alternatives])}")


def _print_module_text(payload: dict[str, Any]) -> None:
    module = payload.get("module", {})
    next_block = payload.get("next", {})
    print("SUMMARY")
    print(f"module={module.get('module_id')} path={module.get('path')}")
    print("")
    print("STATUS")
    print(
        f"phase={module.get('phase')} task={module.get('active_task_id')} "
        f"slice={module.get('active_slice_id')} "
        f"progress={module.get('slices_done', 0)}/{module.get('slices_total', 0)}"
    )
    if module.get("blocked_reason"):
        print(f"blocked_reason={module.get('blocked_reason')}")
    if payload.get("cd_hint"):
        print(payload["cd_hint"])
    print("")
    print("NEXT")
    print(next_block.get("recommended", "-"))
    alternatives = next_block.get("alternatives", [])
    if isinstance(alternatives, list) and alternatives:
        print(f"ALT: {_render_list([str(item) for item in alternatives])}")


def _find_command_index(argv: list[str]) -> int | None:
    index = 0
    while index < len(argv):
        token = argv[index]
        if token in {"--root", "--state-root"}:
            index += 2
            continue
        if token.startswith("--root=") or token.startswith("--state-root="):
            index += 1
            continue
        if token.startswith("-"):
            index += 1
            continue
        return index
    return None


def _rewrite_user_aliases(argv: list[str]) -> list[str]:
    command_index = _find_command_index(argv)
    if command_index is None:
        return argv

    command = argv[command_index]
    if command == "module":
        target_index = command_index + 1
        if target_index >= len(argv):
            return argv
        target = argv[target_index]
        if target.startswith("-") or target in _MODULE_SUBCOMMANDS:
            return argv
        return [
            *argv[:target_index],
            "status",
            "--module-id",
            target,
            *argv[target_index + 1 :],
        ]

    if command == "retro":
        target_index = command_index + 1
        if target_index >= len(argv):
            return [*argv, "run"]
        target = argv[target_index]
        if target.startswith("-"):
            return [*argv[:target_index], "run", *argv[target_index:]]
    return argv


def _command_name(args: argparse.Namespace) -> str:
    parts: list[str] = []
    command = getattr(args, "command", None)
    if command:
        parts.append(str(command))
    for attr in [
        "registry_cmd",
        "wizard_cmd",
        "module_cmd",
        "worktree_cmd",
        "mission_cmd",
        "task_cmd",
        "plan_cmd",
        "slice_cmd",
        "gate_cmd",
        "event_cmd",
        "incident_cmd",
        "retro_cmd",
        "context_cmd",
        "pkm_cmd",
        "skills_cmd",
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
    parsed_argv = _rewrite_user_aliases(raw_argv)
    parser = build_parser()
    args = parser.parse_args(parsed_argv)

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
        user_error = isinstance(exc, (ValueError, KeyError, FileNotFoundError))
        exit_code = 2 if user_error else 20
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
                    "exit_code": exit_code,
                    "error": str(exc),
                },
                worktree_path=str(layout.state_root),
            )
        except Exception:  # noqa: BLE001
            pass
        payload = {"status": "error", "error": str(exc)}
        _print(payload)
        return exit_code

    status = payload.get("status")
    if status in {"blocked", "gate_failed", "review_failed", "failed"}:
        exit_code = 10
    elif status in {"replay_failed", "invariant_failed"}:
        exit_code = 30
    elif status == "error":
        exit_code = 20
    else:
        exit_code = 0
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
            "result_status": status or "ok",
            "exit_code": exit_code,
        },
        worktree_path=str(layout.state_root),
    )

    if command_name == "completion" and isinstance(payload.get("script"), str):
        print(str(payload["script"]), end="")
        return exit_code

    if sys.stdout.isatty():
        if command_name == "status" and not bool(getattr(args, "json", False)):
            _print_status_text(payload)
            return exit_code
        if command_name == "module status":
            _print_module_text(payload)
            return exit_code

    _print(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
