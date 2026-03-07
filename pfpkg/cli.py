"""pf CLI dispatcher."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pfpkg.artifacts import put_artifact
from pfpkg.context_builder import build_context_bundle
from pfpkg.db import db_session, is_initialized
from pfpkg.doctor import run_doctor
from pfpkg.docs_freshness import check_docs, mark_doc_fixed, scan_docs
from pfpkg.errors import (
    EXIT_IO,
    EXIT_OK,
    EXIT_USAGE,
    EXIT_VALIDATION,
    PfError,
)
from pfpkg.events import append_event_from_args, event_tail
from pfpkg.focus import get_focus, set_focus_module
from pfpkg.init_cmd import init_project
from pfpkg.missions import close_mission, create_mission
from pfpkg.modules import detect_modules, get_module, init_module, list_modules, upsert_module
from pfpkg.output import CommandResult, print_human, print_json_only
from pfpkg.paths import PFPaths, find_repo_root
from pfpkg.pkm import list_pkm, refresh_pkm_staleness, upsert_pkm_from_args
from pfpkg.plans import approve_plan, create_slice, mark_plan_saved, validate_slices
from pfpkg.report import build_manager_report, render_manager_report_human
from pfpkg.replay import replay_check
from pfpkg.status import build_status, render_status_human
from pfpkg.tasks import set_task_state, create_task
from pfpkg.worktrees import list_worktrees, upsert_worktree


VALID_INTENTS = {"plan", "execute", "review", "retro", "status"}


class PFArgumentParser(argparse.ArgumentParser):
    """Argument parser that never writes usage text during normal command flow."""

    def error(self, message: str) -> None:  # pragma: no cover - tested via CLI behavior
        raise PfError(message, EXIT_USAGE)


def _extract_json_flag(argv: list[str]) -> tuple[list[str], bool]:
    clean = [x for x in argv if x != "--json"]
    return clean, len(clean) != len(argv)


def _parser() -> argparse.ArgumentParser:
    p = PFArgumentParser(prog="pf")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("init")
    sub.add_parser("status")

    # focus
    p_focus = sub.add_parser("focus")
    sub_focus = p_focus.add_subparsers(dest="focus_cmd")
    p_focus_module = sub_focus.add_parser("module")
    p_focus_module.add_argument("module_id")

    # event
    p_event = sub.add_parser("event")
    sub_event = p_event.add_subparsers(dest="event_cmd")
    p_event_append = sub_event.add_parser("append")
    p_event_append.add_argument("--type", required=True)
    p_event_append.add_argument("--scope-type", required=True)
    p_event_append.add_argument("--scope-id", required=True)
    p_event_append.add_argument("--summary", required=True)
    p_event_append.add_argument("--actor", default="assistant")
    p_event_append.add_argument("--payload-json")
    p_event_append.add_argument("--payload")
    p_event_append.add_argument("--artifact-ids")
    p_event_append.add_argument("--mission-id")
    p_event_append.add_argument("--task-id")
    p_event_append.add_argument("--slice-id")
    p_event_append.add_argument("--worktree-id")

    p_event_tail = sub_event.add_parser("tail")
    p_event_tail.add_argument("--scope-type")
    p_event_tail.add_argument("--scope-id")
    p_event_tail.add_argument("--mission-id")
    p_event_tail.add_argument("--limit", type=int, default=20)

    # artifact
    p_artifact = sub.add_parser("artifact")
    sub_artifact = p_artifact.add_subparsers(dest="artifact_cmd")
    p_artifact_put = sub_artifact.add_parser("put")
    p_artifact_put.add_argument("--kind", required=True)
    p_artifact_put.add_argument("--path", required=True)

    # module
    p_module = sub.add_parser("module")
    sub_module = p_module.add_subparsers(dest="module_cmd")
    sub_module.add_parser("detect")
    p_module_upsert = sub_module.add_parser("upsert")
    p_module_upsert.add_argument("--module-id", required=True)
    p_module_upsert.add_argument("--root-path", required=True)
    p_module_upsert.add_argument("--display-name", required=True)
    sub_module.add_parser("list")
    p_module_show = sub_module.add_parser("show")
    p_module_show.add_argument("--module-id", required=True)
    p_module_init = sub_module.add_parser("init")
    p_module_init.add_argument("--module-id", required=True)
    p_module_init.add_argument("--write-scaffold", action="store_true")

    # worktree
    p_worktree = sub.add_parser("worktree")
    sub_worktree = p_worktree.add_subparsers(dest="worktree_cmd")
    p_worktree_upsert = sub_worktree.add_parser("upsert")
    p_worktree_upsert.add_argument("--worktree-id", required=True)
    p_worktree_upsert.add_argument("--module-id", required=True)
    p_worktree_upsert.add_argument("--path", required=True)
    p_worktree_upsert.add_argument("--branch")

    p_worktree_register = sub_worktree.add_parser("register")
    p_worktree_register.add_argument("--worktree-id")
    p_worktree_register.add_argument("--module-id", required=True)
    p_worktree_register.add_argument("--path", required=True)
    p_worktree_register.add_argument("--branch")

    p_worktree_list = sub_worktree.add_parser("list")
    p_worktree_list.add_argument("--module-id")

    # mission
    p_mission = sub.add_parser("mission")
    sub_mission = p_mission.add_subparsers(dest="mission_cmd")
    p_mission_create = sub_mission.add_parser("create")
    p_mission_create.add_argument("--title", required=True)
    p_mission_create.add_argument("--summary")
    p_mission_create.add_argument("--spec-path")
    p_mission_close = sub_mission.add_parser("close")
    p_mission_close.add_argument("--mission-id", required=True)
    p_mission_close.add_argument("--summary", required=True)

    # task
    p_task = sub.add_parser("task")
    sub_task = p_task.add_subparsers(dest="task_cmd")
    p_task_create = sub_task.add_parser("create")
    p_task_create.add_argument("--module-id", required=True)
    p_task_create.add_argument("--title", required=True)
    p_task_create.add_argument("--mission-id")
    p_task_state = sub_task.add_parser("set-state")
    p_task_state.add_argument("--task-id", required=True)
    p_task_state.add_argument("--state", required=True)

    # plan
    p_plan = sub.add_parser("plan")
    sub_plan = p_plan.add_subparsers(dest="plan_cmd")
    p_plan_saved = sub_plan.add_parser("mark-saved")
    p_plan_saved.add_argument("--module-id", required=True)
    p_plan_saved.add_argument("--task-id")
    p_plan_approve = sub_plan.add_parser("approve")
    p_plan_approve.add_argument("--module-id", required=True)
    p_plan_approve.add_argument("--task-id")
    p_plan_approve.add_argument("--note", required=True)

    # slice
    p_slice = sub.add_parser("slice")
    sub_slice = p_slice.add_subparsers(dest="slice_cmd")
    p_slice_create = sub_slice.add_parser("create")
    p_slice_create.add_argument("--task-id", required=True)
    p_slice_create.add_argument("--title", required=True)
    p_slice_create.add_argument("--allowed-paths", default="")
    p_slice_create.add_argument("--verify", default="")

    # slices
    p_slices = sub.add_parser("slices")
    sub_slices = p_slices.add_subparsers(dest="slices_cmd")
    p_slices_validate = sub_slices.add_parser("validate")
    p_slices_validate.add_argument("--module-id", required=True)

    # docs
    p_docs = sub.add_parser("docs")
    sub_docs = p_docs.add_subparsers(dest="docs_cmd")
    p_docs_scan = sub_docs.add_parser("scan")
    p_docs_scan.add_argument("--scope", choices=["root", "module"])
    p_docs_scan.add_argument("--module-id")
    p_docs_check = sub_docs.add_parser("check")
    p_docs_check.add_argument("--scope", choices=["root", "module"])
    p_docs_check.add_argument("--module-id")
    p_docs_mark = sub_docs.add_parser("mark-fixed")
    p_docs_mark.add_argument("--path", required=True)
    p_docs_mark.add_argument("--reason")

    # pkm
    p_pkm = sub.add_parser("pkm")
    sub_pkm = p_pkm.add_subparsers(dest="pkm_cmd")
    p_pkm_upsert = sub_pkm.add_parser("upsert")
    p_pkm_upsert.add_argument("--scope-type", required=True)
    p_pkm_upsert.add_argument("--scope-id", required=True)
    p_pkm_upsert.add_argument("--kind", required=True)
    p_pkm_upsert.add_argument("--title", required=True)
    p_pkm_upsert.add_argument("--body-md", required=True)
    p_pkm_upsert.add_argument("--fingerprint-json", required=True)
    p_pkm_upsert.add_argument("--confidence", type=float, required=True)
    p_pkm_upsert.add_argument("--tags")

    p_pkm_list = sub_pkm.add_parser("list")
    p_pkm_list.add_argument("--scope-type", required=True)
    p_pkm_list.add_argument("--scope-id", required=True)
    p_pkm_list.add_argument("--kind")

    # context
    p_context = sub.add_parser("context")
    sub_context = p_context.add_subparsers(dest="context_cmd")
    p_context_build = sub_context.add_parser("build")
    p_context_build.add_argument("--intent", required=True)
    p_context_build.add_argument("--module")
    p_context_build.add_argument("--task")
    p_context_build.add_argument("--budget", type=int, default=12000)
    p_context_build.add_argument("--query")

    # replay
    p_replay = sub.add_parser("replay")
    p_replay.add_argument("--check", action="store_true")

    # doctor
    sub.add_parser("doctor")

    # report
    p_report = sub.add_parser("report")
    sub_report = p_report.add_subparsers(dest="report_cmd")
    sub_report.add_parser("manager")

    return p


def _result_for_status(conn, paths: PFPaths) -> CommandResult:
    status_data = build_status(conn, paths.pf_db_path)
    return CommandResult(
        command="status",
        data={"state": status_data},
        next=status_data["next"],
        human_lines=render_status_human(status_data),
    )


def _dispatch(args, paths: PFPaths) -> CommandResult:
    if args.command in (None, "status"):
        if not is_initialized(paths.pf_db_path):
            status_data = {
                "initialized": False,
                "active_mission": None,
                "focus": {"module_id": None, "task_id": None, "worktree_id": None},
                "modules": [],
                "incidents": [],
                "stale_docs_count": 0,
                "next": {
                    "kind": "cli",
                    "cmd": "pf init",
                    "why": "initialize PowerFlow in this repo",
                },
            }
            return CommandResult(
                command="status",
                data={"state": status_data},
                next=status_data["next"],
                human_lines=render_status_human(status_data),
            )
        with db_session(paths.pf_db_path, require_init=True) as conn:
            return _result_for_status(conn, paths)

    if args.command == "init":
        payload = init_project(paths.repo_root, paths.pf_db_path)
        return CommandResult(
            command="init",
            data=payload,
            next={"kind": "cli", "cmd": "pf status", "why": "review initialized state"},
            human_lines=[
                "PowerFlow init: OK",
                f"Created: {', '.join(payload['created']) if payload['created'] else 'nothing new'}",
                f"Skipped: {', '.join(payload['skipped']) if payload['skipped'] else 'none'}",
                "NEXT: pf status",
            ],
        )

    if args.command == "doctor":
        payload = run_doctor(paths.repo_root, paths.pf_db_path)
        lines = [f"DOCTOR: {'OK' if payload['ok'] else 'FAIL'}"]
        for check in payload["checks"]:
            lines.append(f"- {check['name']}: {'ok' if check['ok'] else 'fail'} ({check['message']})")
        if payload["warnings"]:
            lines.append("Warnings:")
            for warning in payload["warnings"]:
                lines.append(f"- {warning}")
        return CommandResult(command="doctor", data=payload, human_lines=lines)

    with db_session(paths.pf_db_path, require_init=True) as conn:
        def resolve_plan_task_id(module_id: str, explicit_task_id: str | None) -> str | None:
            if explicit_task_id:
                return explicit_task_id
            focus = get_focus(conn)
            if focus.get("module_id") == module_id and focus.get("task_id"):
                return focus["task_id"]
            return None

        if args.command == "focus" and args.focus_cmd == "module":
            focus = set_focus_module(conn, args.module_id)
            return CommandResult(
                command="focus module",
                data={"focus": focus},
                next={"kind": "cli", "cmd": "pf context build --intent status", "why": "refresh bounded context"},
                human_lines=[f"FOCUS OK: module={focus['module_id']}", "NEXT: pf context build --intent status"],
            )

        if args.command == "event" and args.event_cmd == "append":
            payload = append_event_from_args(conn, args)
            return CommandResult(
                command="event append",
                data=payload,
                human_lines=[f"EVENT OK id={payload['event_id']}"],
            )

        if args.command == "event" and args.event_cmd == "tail":
            payload = event_tail(
                conn,
                limit=args.limit,
                scope_type=args.scope_type,
                scope_id=args.scope_id,
                mission_id=args.mission_id,
            )
            lines = ["Recent events:"]
            for item in payload:
                lines.append(
                    f"- [{item['event_id']}] {item['ts']} {item['type']} {item['scope_type']}:{item['scope_id']} {item['summary']}"
                )
            return CommandResult(command="event tail", data={"events": payload}, human_lines=lines)

        if args.command == "artifact" and args.artifact_cmd == "put":
            artifact = put_artifact(conn, paths.repo_root, kind=args.kind, path_value=args.path)
            return CommandResult(
                command="artifact put",
                data={"artifact": artifact},
                human_lines=[
                    "ARTIFACT OK",
                    f"id={artifact['artifact_id']} kind={artifact['kind']} path={artifact['path']} sha256={artifact['sha256'][:12]}",
                ],
            )

        if args.command == "module" and args.module_cmd == "detect":
            candidates = detect_modules(paths.repo_root)
            return CommandResult(
                command="module detect",
                data={"candidates": candidates},
                human_lines=["Module candidates:", *[f"- {c['module_id']} -> {c['root_path']} ({c['reason']})" for c in candidates]],
            )

        if args.command == "module" and args.module_cmd == "upsert":
            module = upsert_module(
                conn,
                paths.repo_root,
                module_id=args.module_id,
                root_path=args.root_path,
                display_name=args.display_name,
            )
            return CommandResult(
                command="module upsert",
                data={"module": module},
                human_lines=[f"MODULE OK: {module['module_id']} ({module['root_path']})"],
            )

        if args.command == "module" and args.module_cmd == "list":
            modules = list_modules(conn)
            return CommandResult(
                command="module list",
                data={"modules": modules},
                human_lines=["Modules:", *[f"- {m['module_id']} ({m['root_path']}) initialized={m['initialized']}" for m in modules]],
            )

        if args.command == "module" and args.module_cmd == "show":
            module = get_module(conn, args.module_id)
            return CommandResult(
                command="module show",
                data={"module": module},
                human_lines=[f"Module {module['module_id']}", f"root_path={module['root_path']}", f"initialized={module['initialized']}"],
            )

        if args.command == "module" and args.module_cmd == "init":
            payload = init_module(conn, paths.repo_root, module_id=args.module_id, write_scaffold=args.write_scaffold)
            return CommandResult(
                command="module init",
                data=payload,
                human_lines=[
                    f"MODULE INIT OK: {args.module_id}",
                    f"Created files: {', '.join(payload['created_files']) if payload['created_files'] else 'none'}",
                ],
            )

        if args.command == "worktree" and args.worktree_cmd in {"upsert", "register"}:
            worktree_id = args.worktree_id or f"WT-{args.module_id}"
            wt = upsert_worktree(
                conn,
                worktree_id=worktree_id,
                module_id=args.module_id,
                path=args.path,
                branch=args.branch,
            )
            return CommandResult(
                command=f"worktree {args.worktree_cmd}",
                data={"worktree": wt},
                human_lines=[f"WORKTREE OK: {wt['worktree_id']} -> {wt['module_id']} ({wt['path']})"],
            )

        if args.command == "worktree" and args.worktree_cmd == "list":
            wts = list_worktrees(conn, module_id=args.module_id)
            return CommandResult(
                command="worktree list",
                data={"worktrees": wts},
                human_lines=["Worktrees:", *[f"- {w['worktree_id']} module={w['module_id']} path={w['path']} branch={w['branch'] or '-'}" for w in wts]],
            )

        if args.command == "mission" and args.mission_cmd == "create":
            mission = create_mission(
                conn,
                paths.repo_root,
                title=args.title,
                summary=args.summary,
                spec_path=args.spec_path,
            )
            return CommandResult(
                command="mission create",
                data={"mission": mission},
                human_lines=[f"MISSION OK: {mission['mission_id']} {mission['title']}"],
            )

        if args.command == "mission" and args.mission_cmd == "close":
            payload = close_mission(conn, mission_id=args.mission_id, summary=args.summary)
            return CommandResult(
                command="mission close",
                data=payload,
                human_lines=[f"MISSION CLOSED: {args.mission_id}"],
            )

        if args.command == "task" and args.task_cmd == "create":
            task = create_task(
                conn,
                paths.repo_root,
                module_id=args.module_id,
                title=args.title,
                mission_id=args.mission_id,
            )
            return CommandResult(
                command="task create",
                data={"task": task},
                human_lines=[f"TASK OK: {task['task_id']} ({task['module_id']})"],
            )

        if args.command == "task" and args.task_cmd == "set-state":
            payload = set_task_state(conn, task_id=args.task_id, state=args.state)
            return CommandResult(
                command="task set-state",
                data=payload,
                human_lines=[f"TASK STATE OK: {payload['task_id']} -> {payload['state']}"],
            )

        if args.command == "plan" and args.plan_cmd == "mark-saved":
            task_id = resolve_plan_task_id(args.module_id, args.task_id)
            payload = mark_plan_saved(
                conn,
                paths.repo_root,
                module_id=args.module_id,
                task_id=task_id,
            )
            return CommandResult(
                command="plan mark-saved",
                data=payload,
                human_lines=[f"PLAN SAVED: module={args.module_id}"],
            )

        if args.command == "plan" and args.plan_cmd == "approve":
            task_id = resolve_plan_task_id(args.module_id, args.task_id)
            payload = approve_plan(conn, module_id=args.module_id, task_id=task_id, note=args.note)
            return CommandResult(
                command="plan approve",
                data=payload,
                human_lines=[f"PLAN APPROVED: module={args.module_id}"],
            )

        if args.command == "slice" and args.slice_cmd == "create":
            allowed = [x.strip() for x in args.allowed_paths.split(",") if x.strip()]
            verify = [x.strip() for x in args.verify.split(",") if x.strip()]
            payload = create_slice(
                conn,
                paths.repo_root,
                task_id=args.task_id,
                title=args.title,
                allowed_paths=allowed,
                verify=verify,
            )
            return CommandResult(
                command="slice create",
                data=payload,
                human_lines=[f"SLICE OK: {payload['slice']['slice_id']}"],
            )

        if args.command == "slices" and args.slices_cmd == "validate":
            payload = validate_slices(paths.repo_root, args.module_id)
            lines = [f"SLICES VALIDATE: ok={payload['ok']} count={payload['slice_count']}"]
            for problem in payload["problems"]:
                lines.append(f"- {problem}")
            return CommandResult(command="slices validate", data=payload, human_lines=lines)

        if args.command == "docs" and args.docs_cmd == "scan":
            payload = scan_docs(conn, paths.repo_root, scope=args.scope, module_id=args.module_id)
            return CommandResult(
                command="docs scan",
                data=payload,
                human_lines=[f"DOCS SCAN OK: {payload['count']} docs indexed"],
            )

        if args.command == "docs" and args.docs_cmd == "check":
            payload = check_docs(conn, paths.repo_root, scope=args.scope, module_id=args.module_id)
            return CommandResult(
                command="docs check",
                data=payload,
                human_lines=[f"DOCS CHECK OK: checked={payload['checked']} stale={payload['stale_count']}"],
            )

        if args.command == "docs" and args.docs_cmd == "mark-fixed":
            payload = mark_doc_fixed(conn, paths.repo_root, path=args.path, reason=args.reason)
            return CommandResult(
                command="docs mark-fixed",
                data=payload,
                human_lines=[f"DOC FIXED: {payload['path']}"],
            )

        if args.command == "pkm" and args.pkm_cmd == "upsert":
            payload = upsert_pkm_from_args(conn, args)
            return CommandResult(command="pkm upsert", data=payload, human_lines=[f"PKM OK: id={payload['pkm_id']} {payload['title']}"])

        if args.command == "pkm" and args.pkm_cmd == "list":
            refresh_pkm_staleness(conn, paths.repo_root)
            items = list_pkm(conn, scope_type=args.scope_type, scope_id=args.scope_id, kind=args.kind)
            lines = ["PKM items:"]
            for item in items:
                lines.append(f"- [{item['pkm_id']}] {item['kind']} {item['title']} stale={item['stale']} confidence={item['confidence']}")
            return CommandResult(command="pkm list", data={"items": items}, human_lines=lines)

        if args.command == "context" and args.context_cmd == "build":
            if args.intent not in VALID_INTENTS:
                raise PfError("intent must be one of plan|execute|review|retro|status", EXIT_VALIDATION)
            payload = build_context_bundle(
                conn,
                paths.repo_root,
                intent=args.intent,
                module=args.module,
                task=args.task,
                budget=args.budget,
                query=args.query,
            )
            bundle = payload["bundle"]
            return CommandResult(
                command="context build",
                data=payload,
                human_lines=[
                    f"CONTEXT OK: {bundle['bundle_id']}",
                    f"scope={bundle['scope']['type']}:{bundle['scope']['id']} intent={bundle['intent']}",
                    f"bundle.json={payload['bundle_json']}",
                    f"bundle.md={payload['bundle_md']}",
                ],
            )

        if args.command == "replay":
            if not args.check:
                raise PfError("replay requires --check", EXIT_USAGE)
            payload = replay_check(conn)
            if not payload["ok"]:
                raise PfError("replay check failed", EXIT_VALIDATION)
            return CommandResult(command="replay --check", data=payload, human_lines=["REPLAY CHECK: OK"])

        if args.command == "report" and args.report_cmd == "manager":
            report = build_manager_report(conn, paths.pf_db_path)
            return CommandResult(
                command="report manager",
                data={"report": report},
                next=report["next"],
                human_lines=render_manager_report_human(report),
            )

    raise PfError("unknown command", EXIT_USAGE)


def main(argv: list[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    cleaned_argv, json_mode = _extract_json_flag(raw_argv)

    try:
        parser = _parser()
        args = parser.parse_args(cleaned_argv)

        repo_root = find_repo_root(Path.cwd())
        paths = PFPaths(repo_root=repo_root)

        result = _dispatch(args, paths)

        if json_mode:
            print_json_only(result.as_json())
        else:
            print_human(result.human_lines)
        return EXIT_OK

    except PfError as exc:
        if json_mode:
            error_payload: dict[str, Any] = {"code": exc.code, "message": str(exc)}
            if exc.details is not None:
                error_payload["details"] = exc.details
            print_json_only({"ok": False, "error": error_payload})
        else:
            print(f"ERROR: {exc}")
        return exc.code
    except SystemExit as exc:
        code = int(exc.code)
        return code if code else EXIT_OK
    except Exception as exc:  # pragma: no cover
        if json_mode:
            print_json_only({"ok": False, "error": {"code": EXIT_IO, "message": str(exc)}})
        else:
            print(f"ERROR: {exc}")
        return EXIT_IO


if __name__ == "__main__":
    raise SystemExit(main())
