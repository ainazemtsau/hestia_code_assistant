"""CLI command handlers."""

from __future__ import annotations

import argparse
import json
import shlex
from typing import Any

from csk_next.doctor.run import run_doctor
from csk_next.domain.state import ensure_registry, find_module
from csk_next.eventlog.store import append_event, tail_events
from csk_next.gates.ready import validate_ready
from csk_next.gates.review import record_review
from csk_next.gates.scope import check_scope
from csk_next.gates.verify import parse_cmds, run_verify
from csk_next.io.files import read_json, write_json
from csk_next.profiles.manager import load_profile_from_paths
from csk_next.runtime.bootstrap import bootstrap
from csk_next.runtime.incidents import log_incident, make_incident
from csk_next.runtime.intake import classify_request
from csk_next.runtime.missions import mission_new, mission_status, spawn_milestone
from csk_next.runtime.modules import (
    module_add,
    module_init,
    module_list,
    module_show,
    module_status,
    registry_detect,
)
from csk_next.runtime.paths import Layout, resolve_layout
from csk_next.runtime.proofs import proof_dir
from csk_next.runtime.retro import run_retro
from csk_next.runtime.state_migration import migrate_state
from csk_next.runtime.status import project_module_status, project_root_status
from csk_next.runtime.slices import slice_mark, slice_run
from csk_next.runtime.tasks import ready_approval_path, task_dir, task_run_dir
from csk_next.runtime.tasks_engine import (
    mark_task_status,
    task_approve_plan,
    task_freeze,
    task_new,
    task_record_critic,
    task_status,
)
from csk_next.runtime.time import utc_now_iso
from csk_next.runtime.validation import ValidationError, validate_all
from csk_next.update.engine import update_engine
from csk_next.wizard.runner import run_wizard, wizard_answer, wizard_start, wizard_status


def _layout(args: argparse.Namespace) -> Layout:
    return resolve_layout(args.root, args.state_root)


def _resolve_module(layout, module_id: str) -> dict[str, Any]:
    registry = ensure_registry(layout.registry)
    return find_module(registry, module_id)


def _parse_argv(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    if "|" in raw:
        raise ValueError("Pipelines are forbidden")
    argv = shlex.split(raw)
    if not argv:
        return None
    return argv


def cmd_bootstrap(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return bootstrap(layout)


def cmd_status(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return project_root_status(layout)


def cmd_run(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return run_wizard(
        layout=layout,
        request=args.request,
        modules=args.modules,
        shape=args.shape,
        plan_option=args.plan_option,
        auto_confirm=args.yes,
        non_interactive=args.non_interactive,
    )


def cmd_wizard_start(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    started = wizard_start(layout)
    if args.request:
        session_id = started["wizard"]["session_id"]
        return wizard_answer(layout, session_id, args.request)
    return started


def cmd_wizard_answer(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return wizard_answer(layout, args.session_id, args.response)


def cmd_wizard_status(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return wizard_status(layout, args.session_id)


def cmd_module_add(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return module_add(layout, args.path, args.module_id)


def cmd_module_list(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return module_list(layout)


def cmd_module_show(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return module_show(layout, args.module_id)


def cmd_module_init(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return module_init(layout, args.module_id, write_scaffold=args.write_scaffold)


def cmd_module_status(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    if args.module_id is None:
        return project_root_status(layout)
    return project_module_status(layout, args.module_id)


def cmd_intake(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    registry = ensure_registry(layout.registry)
    module_candidates = [item["module_id"] for item in registry["modules"]]
    payload = classify_request(args.request, module_candidates)
    return {"status": "ok", "intake": payload}


def cmd_registry_detect(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return registry_detect(layout)


def cmd_mission_new(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return mission_new(
        layout=layout,
        title=args.title,
        summary=args.summary,
        module_ids=args.modules,
        create_worktrees=not args.no_worktree,
        create_task_stubs=not args.no_task_stubs,
        profile=args.profile,
    )


def cmd_mission_status(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return mission_status(layout=layout, mission_id=args.mission_id)


def cmd_mission_spawn(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    parallel_groups = [group.split(",") for group in args.parallel_group]
    return spawn_milestone(
        layout=layout,
        mission_id=args.mission_id,
        title=args.title,
        module_items=args.modules,
        depends_on=args.depends_on,
        parallel_groups=parallel_groups,
        integration_checks=args.integration_check,
    )


def cmd_task_new(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    return task_new(
        layout=layout,
        module_id=args.module_id,
        module_path=module["path"],
        mission_id=args.mission_id,
        profile=args.profile,
        max_attempts=args.max_attempts,
        plan_template=args.plan_template,
    )


def cmd_task_critic(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    return task_record_critic(
        layout=layout,
        module_path=module["path"],
        task_id=args.task_id,
        critic=args.critic,
        p0=args.p0,
        p1=args.p1,
        p2=args.p2,
        p3=args.p3,
        notes=args.notes,
    )


def cmd_task_freeze(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    return task_freeze(layout=layout, module_path=module["path"], task_id=args.task_id)


def cmd_task_approve(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    return task_approve_plan(
        layout=layout,
        module_path=module["path"],
        task_id=args.task_id,
        approved_by=args.approved_by,
    )


def cmd_task_status(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    return task_status(layout=layout, module_path=module["path"], task_id=args.task_id)


def cmd_slice_run(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return slice_run(
        layout=layout,
        module_id=args.module_id,
        task_id=args.task_id,
        slice_id=args.slice_id,
        implement_cmd=_parse_argv(args.implement),
        verify_cmds_raw=args.verify_cmd,
        e2e_cmds_raw=args.e2e_cmd,
        reviewer=args.reviewer,
        p0=args.p0,
        p1=args.p1,
        p2=args.p2,
        p3=args.p3,
        review_notes=args.review_notes,
    )


def cmd_slice_mark(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return slice_mark(
        layout=layout,
        module_id=args.module_id,
        task_id=args.task_id,
        slice_id=args.slice_id,
        status=args.status,
        note=args.note,
    )


def cmd_gate_scope(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    run_dir = task_run_dir(layout, module["path"], args.task_id)
    proof = check_scope(
        task_id=args.task_id,
        slice_id=args.slice_id,
        task_run_dir=run_dir,
        changed=args.changed,
        allowed_paths=args.allowed_path,
    )
    return {"status": "ok" if proof["passed"] else "failed", "proof": proof}


def cmd_gate_verify(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    run_dir = task_run_dir(layout, module["path"], args.task_id)
    commands = parse_cmds(args.cmd)
    proof = run_verify(
        task_id=args.task_id,
        slice_id=args.slice_id,
        task_run_dir=run_dir,
        cwd=layout.module_root(module["path"]),
        commands=commands,
        require_at_least_one=True,
    )
    return {"status": "ok" if proof["passed"] else "failed", "proof": proof}


def cmd_gate_review(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    run_dir = task_run_dir(layout, module["path"], args.task_id)
    proof = record_review(
        task_id=args.task_id,
        slice_id=args.slice_id,
        task_run_dir=run_dir,
        reviewer=args.reviewer,
        p0=args.p0,
        p1=args.p1,
        p2=args.p2,
        p3=args.p3,
        notes=args.notes,
    )
    return {"status": "ok" if proof["passed"] else "failed", "proof": proof}


def cmd_gate_validate_ready(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    module_path = module["path"]
    task_root = task_dir(layout, module_path, args.task_id)
    task_state = read_json(task_root / "task.json")

    profile = load_profile_from_paths(layout.engine, layout.local, task_state["profile"])
    ready = validate_ready(
        task_id=args.task_id,
        module_path=module_path,
        task_dir=task_root,
        task_run_dir=task_run_dir(layout, module_path, args.task_id),
        layout=layout,
        profile=profile,
    )
    if ready["passed"]:
        mark_task_status(layout, module_path, args.task_id, "ready_validated")
    return {"status": "ok" if ready["passed"] else "failed", "ready": ready}


def cmd_gate_approve_ready(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    module = _resolve_module(layout, args.module_id)
    module_path = module["path"]
    task_root = task_dir(layout, module_path, args.task_id)
    ready_proof_path = proof_dir(task_run_dir(layout, module_path, args.task_id)) / "ready.json"
    if not ready_proof_path.exists():
        raise ValueError("Missing ready proof; run validate-ready first")

    proof = read_json(ready_proof_path)
    if not proof.get("passed", False):
        raise ValueError("Cannot approve READY: validation failed")

    approval = {
        "approved_by": args.approved_by,
        "approved_at": utc_now_iso(),
    }
    write_json(ready_approval_path(layout, module_path, args.task_id), approval)
    mark_task_status(layout, module_path, args.task_id, "ready_approved")

    return {
        "status": "ok",
        "approval": approval,
        "handoff": str(task_root / "handoff.json"),
    }


def cmd_event_append(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    payload = json.loads(args.payload)
    if not isinstance(payload, dict):
        raise ValueError("event payload must be a JSON object")

    event = append_event(
        layout=layout,
        event_type=args.type,
        actor=args.actor,
        mission_id=args.mission_id,
        module_id=args.module_id,
        task_id=args.task_id,
        slice_id=args.slice_id,
        payload=payload,
        artifact_refs=args.artifact_ref,
        worktree_path=args.worktree_path,
        repo_git_head=args.repo_git_head,
        engine_version=args.engine_version,
    )
    return {"status": "ok", "event": event}


def cmd_event_tail(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    events = tail_events(
        layout=layout,
        n=args.n,
        event_type=args.type,
        mission_id=args.mission_id,
        module_id=args.module_id,
        task_id=args.task_id,
        slice_id=args.slice_id,
    )
    return {"status": "ok", "events": events}


def cmd_incident_add(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    incident = make_incident(
        severity=args.severity,
        kind=args.kind,
        phase=args.phase,
        module_id=args.module_id,
        message=args.message,
        remediation=args.remediation,
        context={"task_id": args.task_id} if args.task_id else {},
    )
    log_incident(layout.app_incidents, incident)
    return {"status": "ok", "incident": incident}


def cmd_retro_run(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return run_retro(layout, args.module_id, args.task_id, args.feedback)


def cmd_validate(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    try:
        return validate_all(layout, strict=args.strict)
    except ValidationError as exc:
        return {"status": "failed", "strict": args.strict, "error": str(exc)}


def cmd_update_engine(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return update_engine(layout)


def cmd_migrate_state(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return migrate_state(layout, source_root=args.source_root)


def cmd_doctor_run(args: argparse.Namespace) -> dict[str, Any]:
    layout = _layout(args)
    return run_doctor(layout, args.doctor_commands, git_boundary=args.git_boundary)
