"""CSK CLI entrypoint."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable

from csk_next.cli.parser import build_parser
from csk_next.eventlog.store import append_event
from csk_next.runtime.paths import resolve_layout
from csk_next.runtime.status import project_module_status, project_root_status


_MODULE_SUBCOMMANDS = {"list", "show", "add", "init", "status"}
_USER_FACING_COMMANDS = {
    "status",
    "new",
    "run",
    "approve",
    "module status",
    "retro run",
    "replay",
}


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _render_list(values: list[str]) -> str:
    if not values:
        return "-"
    return "; ".join(values)


def _payload_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def _print_status_text(payload: dict[str, Any]) -> None:
    data = _payload_data(payload)
    summary = payload.get("summary", {})
    if not isinstance(summary, dict):
        summary = data.get("summary", {}) if isinstance(data.get("summary"), dict) else {}
    modules = data.get("modules", [])
    skills = data.get("skills", {})
    counters = data.get("counters", summary.get("counters", {}))
    next_block = payload.get("next", {})
    if not isinstance(next_block, dict):
        next_block = data.get("next", {}) if isinstance(data.get("next"), dict) else {}
    skills_status = "ok" if str(skills.get("status", "ok")) == "ok" else "stale"
    tasks_by_status = counters.get("tasks_by_status", {}) if isinstance(counters, dict) else {}
    tasks_total = sum(int(value) for value in tasks_by_status.values()) if isinstance(tasks_by_status, dict) else 0

    print("SUMMARY:")
    print(
        f"phase={summary.get('project_phase')} "
        f"bootstrapped={summary.get('bootstrapped')} "
        f"mission={summary.get('active_mission_id')} "
        f"milestone={summary.get('active_milestone_id')} "
        f"modules={summary.get('modules_total')} "
        f"skills={skills_status} "
        f"tasks={tasks_total} "
        f"proofs={counters.get('proof_packs_total') if isinstance(counters, dict) else 0} "
        f"retro={counters.get('retro_total') if isinstance(counters, dict) else 0}"
    )
    print("")
    print("STATUS:")
    if skills_status != "ok":
        print(
            f"- skills: stale modified={len(skills.get('modified', []))} "
            f"missing={len(skills.get('missing', []))} stale={len(skills.get('stale', []))}"
        )
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
    print("NEXT:")
    print(next_block.get("recommended", "-"))
    alternatives = next_block.get("alternatives", [])
    if isinstance(alternatives, list) and alternatives:
        print(f"ALT: {_render_list([str(item) for item in alternatives])}")


def _print_module_text(payload: dict[str, Any]) -> None:
    data = _payload_data(payload)
    summary = payload.get("summary", {})
    module = data.get("module", {})
    next_block = payload.get("next", {})
    if not isinstance(next_block, dict):
        next_block = data.get("next", {}) if isinstance(data.get("next"), dict) else {}
    print("SUMMARY:")
    print(f"module={module.get('module_id')} path={module.get('path')}")
    if isinstance(summary, dict) and summary.get("project_phase"):
        print(f"project_phase={summary.get('project_phase')}")
    print("")
    print("STATUS:")
    print(
        f"phase={module.get('phase')} task={module.get('active_task_id')} "
        f"slice={module.get('active_slice_id')} "
        f"progress={module.get('slices_done', 0)}/{module.get('slices_total', 0)}"
    )
    if module.get("blocked_reason"):
        print(f"blocked_reason={module.get('blocked_reason')}")
    if data.get("cd_hint"):
        print(data["cd_hint"])
    print("")
    print("NEXT:")
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


def _error_next(command_name: str, args: argparse.Namespace) -> dict[str, Any] | None:
    if command_name not in _USER_FACING_COMMANDS:
        return None

    if command_name == "status":
        return {"recommended": "csk run", "alternatives": ["csk status --json"]}
    if command_name == "new":
        return {"recommended": "csk status --json", "alternatives": ["csk run"]}
    if command_name == "run":
        return {"recommended": "csk status --json", "alternatives": ["csk new \"<request>\" --modules <id>"]}
    if command_name == "approve":
        module_id = getattr(args, "module_id", None)
        if module_id:
            return {"recommended": f"csk module {module_id}", "alternatives": ["csk status --json"]}
        return {"recommended": "csk status --json", "alternatives": ["csk run"]}
    if command_name == "module status":
        module_id = getattr(args, "module_id", None)
        if module_id:
            return {"recommended": f"csk module {module_id}", "alternatives": ["csk status --json"]}
        return {"recommended": "csk status --json", "alternatives": ["csk run"]}
    if command_name == "retro run":
        module_id = getattr(args, "module_id", None)
        if module_id:
            return {"recommended": f"csk module {module_id}", "alternatives": ["csk status --json"]}
        return {"recommended": "csk status --json", "alternatives": ["csk run"]}
    if command_name == "replay":
        return {"recommended": "csk replay --check", "alternatives": ["csk status --json"]}
    return None


def _normalize_next(next_block: Any) -> dict[str, Any]:
    if not isinstance(next_block, dict):
        return {"recommended": "csk run", "alternatives": ["csk status --json"]}
    recommended = str(next_block.get("recommended") or "csk run")
    alternatives_raw = next_block.get("alternatives", [])
    alternatives = [str(item) for item in alternatives_raw] if isinstance(alternatives_raw, list) else []
    return {"recommended": recommended, "alternatives": alternatives}


def _fallback_next(command_name: str, args: argparse.Namespace) -> dict[str, Any]:
    layout = resolve_layout(args.root, args.state_root)
    if command_name == "module status":
        module_id = getattr(args, "module_id", None)
        if module_id:
            try:
                payload = project_module_status(layout, module_id)
                return _normalize_next(payload.get("next"))
            except Exception:  # noqa: BLE001
                pass
    try:
        payload = project_root_status(layout)
        return _normalize_next(payload.get("next"))
    except Exception:  # noqa: BLE001
        return {"recommended": "csk run", "alternatives": ["csk status --json"]}


def _summary_block(command_name: str, payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    summary = payload.get("summary")
    if isinstance(summary, dict):
        return summary

    result: dict[str, Any] = {"command": command_name}
    for field in ["mission_id", "module_id", "task_id", "slice_id"]:
        value = getattr(args, field, None)
        if value is not None:
            result[field] = value
    kind = payload.get("kind")
    if isinstance(kind, str):
        result["kind"] = kind
    return result


def _collect_refs(payload: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    key_hints = {
        "path",
        "task_path",
        "mission_path",
        "output_dir",
        "bundle_path",
        "handoff",
        "patch_file",
        "retro_file",
        "log_path",
    }

    def visit(node: Any, key: str | None = None) -> None:
        if isinstance(node, dict):
            for child_key, child_value in node.items():
                if child_key == "artifact_refs" and isinstance(child_value, list):
                    for row in child_value:
                        if isinstance(row, str) and row.strip():
                            refs.append(row.strip())
                    continue
                visit(child_value, child_key)
            return
        if isinstance(node, list):
            for item in node:
                visit(item, key)
            return
        if isinstance(node, str) and key is not None:
            if not node.strip():
                return
            if key in key_hints or key.endswith("_path") or key.endswith("_file") or key.endswith("_dir"):
                refs.append(node.strip())

    visit(payload)
    dedup: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        dedup.append(ref)
    return dedup


def _collect_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    raw_errors = payload.get("errors")
    if isinstance(raw_errors, list):
        for row in raw_errors:
            if isinstance(row, str) and row.strip():
                errors.append(row.strip())

    raw_error = payload.get("error")
    if isinstance(raw_error, str) and raw_error.strip():
        errors.append(raw_error.strip())

    replay = payload.get("replay")
    if isinstance(replay, dict):
        violations = replay.get("violations")
        if isinstance(violations, list):
            for row in violations:
                if isinstance(row, str) and row.strip():
                    errors.append(row.strip())

    dedup: list[str] = []
    seen: set[str] = set()
    for error in errors:
        if error in seen:
            continue
        seen.add(error)
        dedup.append(error)
    return dedup


def _strict_user_envelope(command_name: str, payload: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if command_name not in _USER_FACING_COMMANDS:
        return payload

    raw_next = payload.get("next")
    if isinstance(raw_next, dict):
        next_block = _normalize_next(raw_next)
    else:
        next_block = _fallback_next(command_name, args)

    data = {key: value for key, value in payload.items() if key not in {"summary", "status", "next", "refs", "errors", "data"}}
    status = str(payload.get("status", "ok"))
    errors = _collect_errors(payload)

    return {
        "summary": _summary_block(command_name, payload, args),
        "status": status,
        "next": next_block,
        "refs": _collect_refs(payload),
        "errors": errors,
        "data": data,
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
        next_block = _error_next(command_name, args)
        if next_block:
            payload["next"] = next_block
        _print(_strict_user_envelope(command_name, payload, args))
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

    render_payload = _strict_user_envelope(command_name, payload, args)

    if sys.stdout.isatty():
        if command_name == "status" and not bool(getattr(args, "json", False)):
            _print_status_text(render_payload)
            return exit_code
        if command_name == "module status" and not bool(getattr(args, "json", False)):
            _print_module_text(render_payload)
            return exit_code

    _print(render_payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
