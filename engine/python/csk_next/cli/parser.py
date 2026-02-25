"""CLI parser wiring."""

from __future__ import annotations

import argparse

from csk_next.cli import handlers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="csk")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument(
        "--state-root",
        help="State root path (default: --root or CSK_STATE_ROOT env var)",
    )

    sub = parser.add_subparsers(dest="command")
    parser.set_defaults(command="status", handler=handlers.cmd_status)

    status_p = sub.add_parser("status")
    status_p.add_argument("--json", action="store_true")
    status_p.set_defaults(handler=handlers.cmd_status)

    run_p = sub.add_parser("run", help="Run the interactive wizard-first workflow")
    run_p.add_argument("--request", help="Optional request text for scripted wizard run")
    run_p.add_argument("--modules", help="Optional module mapping: module_id:path,module2:path2")
    run_p.add_argument("--shape", choices=["single", "multi", "auto"], help="Optional execution shape")
    run_p.add_argument("--plan-option", choices=["A", "B", "C"], help="Optional planning option")
    run_p.add_argument("--yes", action="store_true", help="Auto-confirm materialization")
    run_p.add_argument("--non-interactive", action="store_true", help="Do not prompt for missing wizard steps")
    run_p.set_defaults(handler=handlers.cmd_run)

    wizard_p = sub.add_parser("wizard", help="Wizard backend API")
    wizard_sub = wizard_p.add_subparsers(dest="wizard_cmd", required=True)

    wizard_start_p = wizard_sub.add_parser("start")
    wizard_start_p.add_argument("--request")
    wizard_start_p.set_defaults(handler=handlers.cmd_wizard_start)

    wizard_answer_p = wizard_sub.add_parser("answer")
    wizard_answer_p.add_argument("--session-id", required=True)
    wizard_answer_p.add_argument("--response", required=True)
    wizard_answer_p.set_defaults(handler=handlers.cmd_wizard_answer)

    wizard_status_p = wizard_sub.add_parser("status")
    wizard_status_p.add_argument("--session-id", required=True)
    wizard_status_p.set_defaults(handler=handlers.cmd_wizard_status)

    bootstrap_p = sub.add_parser("bootstrap")
    bootstrap_p.set_defaults(handler=handlers.cmd_bootstrap)

    intake_p = sub.add_parser("intake")
    intake_p.add_argument("request")
    intake_p.set_defaults(handler=handlers.cmd_intake)

    registry_p = sub.add_parser("registry")
    registry_sub = registry_p.add_subparsers(dest="registry_cmd", required=True)

    registry_detect_p = registry_sub.add_parser("detect")
    registry_detect_p.set_defaults(handler=handlers.cmd_registry_detect)

    module_p = sub.add_parser("module")
    module_sub = module_p.add_subparsers(dest="module_cmd", required=True)

    module_list_p = module_sub.add_parser("list")
    module_list_p.set_defaults(handler=handlers.cmd_module_list)

    module_show_p = module_sub.add_parser("show")
    module_show_p.add_argument("module_id")
    module_show_p.set_defaults(handler=handlers.cmd_module_show)

    module_add_p = module_sub.add_parser("add")
    module_add_p.add_argument("--path", required=True)
    module_add_p.add_argument("--module-id")
    module_add_p.set_defaults(handler=handlers.cmd_module_add)

    module_init_p = module_sub.add_parser("init")
    module_init_p.add_argument("--module-id", required=True)
    module_init_p.add_argument(
        "--write-scaffold",
        action="store_true",
        help="Write module scaffold files (AGENTS.md, PUBLIC_API.md) into code module",
    )
    module_init_p.set_defaults(handler=handlers.cmd_module_init)

    module_status_p = module_sub.add_parser("status")
    module_status_p.add_argument("--module-id")
    module_status_p.set_defaults(handler=handlers.cmd_module_status)

    mission_p = sub.add_parser("mission")
    mission_sub = mission_p.add_subparsers(dest="mission_cmd", required=True)

    mission_new_p = mission_sub.add_parser("new")
    mission_new_p.add_argument("--title", required=True)
    mission_new_p.add_argument("--summary", required=True)
    mission_new_p.add_argument("--modules", nargs="+", required=True)
    mission_new_p.add_argument("--profile", default="default")
    mission_new_p.add_argument("--no-worktree", action="store_true")
    mission_new_p.add_argument("--no-task-stubs", action="store_true")
    mission_new_p.set_defaults(handler=handlers.cmd_mission_new)

    mission_status_p = mission_sub.add_parser("status")
    mission_status_p.add_argument("--mission-id", required=True)
    mission_status_p.set_defaults(handler=handlers.cmd_mission_status)

    mission_spawn_p = mission_sub.add_parser("spawn-milestone")
    mission_spawn_p.add_argument("--mission-id", required=True)
    mission_spawn_p.add_argument("--title", required=True)
    mission_spawn_p.add_argument("--modules", nargs="+", required=True)
    mission_spawn_p.add_argument("--depends-on", nargs="*", default=[])
    mission_spawn_p.add_argument("--parallel-group", action="append", default=[])
    mission_spawn_p.add_argument("--integration-check", action="append", default=[])
    mission_spawn_p.set_defaults(handler=handlers.cmd_mission_spawn)

    task_p = sub.add_parser("task")
    task_sub = task_p.add_subparsers(dest="task_cmd", required=True)

    task_new_p = task_sub.add_parser("new")
    task_new_p.add_argument("--module-id", required=True)
    task_new_p.add_argument("--mission-id")
    task_new_p.add_argument("--profile", default="default")
    task_new_p.add_argument("--max-attempts", type=int, default=2)
    task_new_p.add_argument("--plan-template")
    task_new_p.set_defaults(handler=handlers.cmd_task_new)

    task_critic_p = task_sub.add_parser("critic")
    task_critic_p.add_argument("--module-id", required=True)
    task_critic_p.add_argument("--task-id", required=True)
    task_critic_p.add_argument("--critic", default="csk-critic")
    task_critic_p.add_argument("--p0", type=int, default=0)
    task_critic_p.add_argument("--p1", type=int, default=0)
    task_critic_p.add_argument("--p2", type=int, default=0)
    task_critic_p.add_argument("--p3", type=int, default=0)
    task_critic_p.add_argument("--notes", default="")
    task_critic_p.set_defaults(handler=handlers.cmd_task_critic)

    task_freeze_p = task_sub.add_parser("freeze")
    task_freeze_p.add_argument("--module-id", required=True)
    task_freeze_p.add_argument("--task-id", required=True)
    task_freeze_p.set_defaults(handler=handlers.cmd_task_freeze)

    task_approve_p = task_sub.add_parser("approve-plan")
    task_approve_p.add_argument("--module-id", required=True)
    task_approve_p.add_argument("--task-id", required=True)
    task_approve_p.add_argument("--approved-by", required=True)
    task_approve_p.set_defaults(handler=handlers.cmd_task_approve)

    task_status_p = task_sub.add_parser("status")
    task_status_p.add_argument("--module-id", required=True)
    task_status_p.add_argument("--task-id", required=True)
    task_status_p.set_defaults(handler=handlers.cmd_task_status)

    slice_p = sub.add_parser("slice")
    slice_sub = slice_p.add_subparsers(dest="slice_cmd", required=True)

    slice_run_p = slice_sub.add_parser("run")
    slice_run_p.add_argument("--module-id", required=True)
    slice_run_p.add_argument("--task-id", required=True)
    slice_run_p.add_argument("--slice-id", required=True)
    slice_run_p.add_argument("--implement")
    slice_run_p.add_argument("--verify-cmd", action="append", default=[])
    slice_run_p.add_argument("--e2e-cmd", action="append", default=[])
    slice_run_p.add_argument("--reviewer", default="csk-reviewer")
    slice_run_p.add_argument("--p0", type=int, default=0)
    slice_run_p.add_argument("--p1", type=int, default=0)
    slice_run_p.add_argument("--p2", type=int, default=0)
    slice_run_p.add_argument("--p3", type=int, default=0)
    slice_run_p.add_argument("--review-notes", default="")
    slice_run_p.set_defaults(handler=handlers.cmd_slice_run)

    slice_mark_p = slice_sub.add_parser("mark")
    slice_mark_p.add_argument("--module-id", required=True)
    slice_mark_p.add_argument("--task-id", required=True)
    slice_mark_p.add_argument("--slice-id", required=True)
    slice_mark_p.add_argument("--status", required=True)
    slice_mark_p.add_argument("--note", default="")
    slice_mark_p.set_defaults(handler=handlers.cmd_slice_mark)

    gate_p = sub.add_parser("gate")
    gate_sub = gate_p.add_subparsers(dest="gate_cmd", required=True)

    gate_scope_p = gate_sub.add_parser("scope-check")
    gate_scope_p.add_argument("--module-id", required=True)
    gate_scope_p.add_argument("--task-id", required=True)
    gate_scope_p.add_argument("--slice-id", required=True)
    gate_scope_p.add_argument("--changed", action="append", default=[])
    gate_scope_p.add_argument("--allowed-path", action="append", default=[])
    gate_scope_p.set_defaults(handler=handlers.cmd_gate_scope)

    gate_verify_p = gate_sub.add_parser("verify")
    gate_verify_p.add_argument("--module-id", required=True)
    gate_verify_p.add_argument("--task-id", required=True)
    gate_verify_p.add_argument("--slice-id", required=True)
    gate_verify_p.add_argument("--cmd", action="append", default=[])
    gate_verify_p.set_defaults(handler=handlers.cmd_gate_verify)

    gate_review_p = gate_sub.add_parser("record-review")
    gate_review_p.add_argument("--module-id", required=True)
    gate_review_p.add_argument("--task-id", required=True)
    gate_review_p.add_argument("--slice-id", required=True)
    gate_review_p.add_argument("--reviewer", default="csk-reviewer")
    gate_review_p.add_argument("--p0", type=int, default=0)
    gate_review_p.add_argument("--p1", type=int, default=0)
    gate_review_p.add_argument("--p2", type=int, default=0)
    gate_review_p.add_argument("--p3", type=int, default=0)
    gate_review_p.add_argument("--notes", default="")
    gate_review_p.set_defaults(handler=handlers.cmd_gate_review)

    gate_validate_p = gate_sub.add_parser("validate-ready")
    gate_validate_p.add_argument("--module-id", required=True)
    gate_validate_p.add_argument("--task-id", required=True)
    gate_validate_p.set_defaults(handler=handlers.cmd_gate_validate_ready)

    gate_approve_p = gate_sub.add_parser("approve-ready")
    gate_approve_p.add_argument("--module-id", required=True)
    gate_approve_p.add_argument("--task-id", required=True)
    gate_approve_p.add_argument("--approved-by", required=True)
    gate_approve_p.set_defaults(handler=handlers.cmd_gate_approve_ready)

    event_p = sub.add_parser("event")
    event_sub = event_p.add_subparsers(dest="event_cmd", required=True)

    event_append_p = event_sub.add_parser("append")
    event_append_p.add_argument("--type", required=True)
    event_append_p.add_argument("--actor", default="engine")
    event_append_p.add_argument("--mission-id")
    event_append_p.add_argument("--module-id")
    event_append_p.add_argument("--task-id")
    event_append_p.add_argument("--slice-id")
    event_append_p.add_argument("--payload", default="{}")
    event_append_p.add_argument("--artifact-ref", action="append", default=[])
    event_append_p.add_argument("--worktree-path")
    event_append_p.add_argument("--repo-git-head")
    event_append_p.add_argument("--engine-version")
    event_append_p.set_defaults(handler=handlers.cmd_event_append)

    event_tail_p = event_sub.add_parser("tail")
    event_tail_p.add_argument("--n", type=int, default=20)
    event_tail_p.add_argument("--type")
    event_tail_p.add_argument("--mission-id")
    event_tail_p.add_argument("--module-id")
    event_tail_p.add_argument("--task-id")
    event_tail_p.add_argument("--slice-id")
    event_tail_p.set_defaults(handler=handlers.cmd_event_tail)

    incident_p = sub.add_parser("incident")
    incident_sub = incident_p.add_subparsers(dest="incident_cmd", required=True)

    incident_add_p = incident_sub.add_parser("add")
    incident_add_p.add_argument("--severity", required=True)
    incident_add_p.add_argument("--kind", required=True)
    incident_add_p.add_argument("--phase", required=True)
    incident_add_p.add_argument("--message", required=True)
    incident_add_p.add_argument("--remediation", required=True)
    incident_add_p.add_argument("--module-id")
    incident_add_p.add_argument("--task-id")
    incident_add_p.set_defaults(handler=handlers.cmd_incident_add)

    retro_p = sub.add_parser("retro")
    retro_sub = retro_p.add_subparsers(dest="retro_cmd", required=True)

    retro_run_p = retro_sub.add_parser("run")
    retro_run_p.add_argument("--module-id", required=True)
    retro_run_p.add_argument("--task-id", required=True)
    retro_run_p.add_argument("--feedback", default="")
    retro_run_p.set_defaults(handler=handlers.cmd_retro_run)

    validate_p = sub.add_parser("validate")
    validate_p.add_argument("--all", action="store_true")
    validate_p.add_argument("--strict", action="store_true")
    validate_p.set_defaults(handler=handlers.cmd_validate)

    update_p = sub.add_parser("update")
    update_sub = update_p.add_subparsers(dest="update_cmd", required=True)
    update_engine_p = update_sub.add_parser("engine")
    update_engine_p.set_defaults(handler=handlers.cmd_update_engine)

    migrate_state_p = sub.add_parser("migrate-state")
    migrate_state_p.add_argument(
        "--source-root",
        help="Source root containing legacy .csk/.agents/AGENTS.md (default: --root)",
    )
    migrate_state_p.set_defaults(handler=handlers.cmd_migrate_state)

    doctor_p = sub.add_parser("doctor")
    doctor_sub = doctor_p.add_subparsers(dest="doctor_cmd", required=True)
    doctor_run_p = doctor_sub.add_parser("run")
    doctor_run_p.add_argument("--command", dest="doctor_commands", action="append", default=[])
    doctor_run_p.add_argument(
        "--git-boundary",
        action="store_true",
        help="Check for tracked/staged files that should stay outside product Git",
    )
    doctor_run_p.set_defaults(handler=handlers.cmd_doctor_run)

    return parser
