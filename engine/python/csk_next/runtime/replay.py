"""Replay/invariant checks from event log."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.eventlog.store import query_events
from csk_next.runtime.paths import Layout


def _exists(path: str | None) -> bool:
    if not path:
        return False
    return Path(path).exists()


def _task_key(module_id: str | None, task_id: str | None) -> tuple[str, str] | None:
    if not module_id or not task_id:
        return None
    return module_id, task_id


def _slice_key(module_id: str | None, task_id: str | None, slice_id: str | None) -> tuple[str, str, str] | None:
    if not module_id or not task_id or not slice_id:
        return None
    return module_id, task_id, slice_id


def _recommend_next(violation: dict[str, Any]) -> dict[str, Any]:
    kind = str(violation.get("kind", ""))
    module_id = violation.get("module_id")
    task_id = violation.get("task_id")
    slice_id = violation.get("slice_id")
    if kind in {"missing_manifest", "slice_complete_without_proof"} and module_id and task_id and slice_id:
        return {
            "recommended": f"csk slice run --module-id {module_id} --task-id {task_id} --slice-id {slice_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if kind in {"missing_ready_proof", "missing_handoff", "ready_validated_without_plan"} and module_id and task_id:
        return {
            "recommended": f"csk gate validate-ready --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if kind in {"missing_ready_approval", "ready_approved_without_validate"} and module_id and task_id:
        return {
            "recommended": f"csk gate approve-ready --module-id {module_id} --task-id {task_id} --approved-by <human>",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if kind in {"missing_retro_file", "missing_patch_file"} and module_id and task_id:
        return {
            "recommended": f"csk retro run --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    if kind in {"plan_approved_without_freeze", "missing_plan_approval_artifact", "frozen_without_critic"} and module_id and task_id:
        return {
            "recommended": f"csk task critic --module-id {module_id} --task-id {task_id}",
            "alternatives": [f"csk module {module_id}", "csk status --json"],
        }
    return {"recommended": "csk status --json", "alternatives": ["csk replay --check"]}


def replay_check(layout: Layout) -> dict[str, Any]:
    # query_events returns newest-first ordered by (ts DESC, rowid DESC).
    # Reverse to process in insertion chronology and avoid UUID tie-break drift
    # for events recorded in the same second.
    events = list(reversed(query_events(layout=layout, limit=5000)))
    checks: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []
    refs: set[str] = set()

    critic_passed_tasks: set[tuple[str, str]] = set()
    frozen_tasks: set[tuple[str, str]] = set()
    plan_approved_tasks: set[tuple[str, str]] = set()
    ready_validated_tasks: set[tuple[str, str]] = set()
    proof_manifests: dict[tuple[str, str, str], str] = {}

    for event in events:
        event_id = str(event["id"])
        event_type = str(event["type"])
        payload = event.get("payload", {})
        artifact_refs = [str(item) for item in event.get("artifact_refs", []) if isinstance(item, str)]
        artifact_refs_posix = [ref.replace("\\", "/") for ref in artifact_refs]
        module_id = event.get("module_id")
        task_id = event.get("task_id")
        slice_id = event.get("slice_id")

        task_key = _task_key(module_id, task_id)
        slice_key = _slice_key(module_id, task_id, slice_id)

        if event_type == "task.critic_passed":
            if task_key is not None:
                critic_passed_tasks.add(task_key)

        if event_type == "task.frozen":
            if task_key is not None and task_key not in critic_passed_tasks:
                violations.append(
                    {
                        "kind": "frozen_without_critic",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": "task.frozen has no prior task.critic_passed",
                        "refs": [],
                    }
                )
            freeze_ref = next(
                (ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if ref_posix.endswith("freeze.json")),
                "",
            )
            freeze_ok = _exists(freeze_ref)
            checks.append({"event_id": event_id, "name": "freeze_artifact_exists", "passed": freeze_ok})
            if not freeze_ok:
                violations.append(
                    {
                        "kind": "plan_approved_without_freeze",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing freeze artifact {freeze_ref}",
                        "refs": [freeze_ref],
                    }
                )
            if task_key is not None:
                frozen_tasks.add(task_key)

        if event_type == "task.plan_approved":
            if task_key is not None and task_key not in frozen_tasks:
                violations.append(
                    {
                        "kind": "plan_approved_without_freeze",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": "task.plan_approved has no prior task.frozen",
                        "refs": [],
                    }
                )
            plan_approval_refs = [
                ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if "approvals/plan.json" in ref_posix
            ]
            plan_approval_ok = any(_exists(ref) for ref in plan_approval_refs)
            checks.append({"event_id": event_id, "name": "plan_approval_exists", "passed": plan_approval_ok})
            if not plan_approval_ok:
                violations.append(
                    {
                        "kind": "missing_plan_approval_artifact",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing plan approval artifact {plan_approval_refs[0] if plan_approval_refs else ''}",
                        "refs": plan_approval_refs,
                    }
                )
            if task_key is not None:
                plan_approved_tasks.add(task_key)

        if event_type == "proof.pack.written":
            manifest_path = str(payload.get("manifest_path", "")) or (artifact_refs[0] if artifact_refs else "")
            manifest_ok = _exists(manifest_path)
            checks.append({"event_id": event_id, "name": "proof_manifest_exists", "passed": manifest_ok})
            if slice_key is not None:
                proof_manifests[slice_key] = manifest_path
            if not manifest_ok:
                violations.append(
                    {
                        "kind": "missing_manifest",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": slice_id,
                        "message": f"missing manifest {manifest_path}",
                        "refs": [manifest_path],
                    }
                )

        if event_type == "slice.completed":
            manifest_path = proof_manifests.get(slice_key, "") if slice_key is not None else ""
            if not manifest_path:
                manifest_path = next(
                    (ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if ref_posix.endswith("manifest.json")),
                    "",
                )
            proof_ok = bool(manifest_path) and _exists(manifest_path)
            if slice_key is not None and manifest_path:
                proof_manifests[slice_key] = manifest_path
            checks.append({"event_id": event_id, "name": "slice_completed_has_proof_pack", "passed": proof_ok})
            if not proof_ok:
                violations.append(
                    {
                        "kind": "slice_complete_without_proof",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": slice_id,
                        "message": f"slice.completed without manifest for {module_id}:{task_id}:{slice_id}",
                        "refs": [manifest_path] if manifest_path else [],
                    }
                )

        if event_type == "ready.validated":
            if task_key is not None and task_key not in plan_approved_tasks:
                violations.append(
                    {
                        "kind": "ready_validated_without_plan",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": "ready.validated has no prior task.plan_approved",
                        "refs": [],
                    }
                )
            ready_proof_path = next(
                (ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if ref_posix.endswith("proofs/ready.json")),
                "",
            )
            handoff_path = str(payload.get("handoff_path", "")) or next(
                (ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if ref_posix.endswith("READY/handoff.md")),
                "",
            )
            ready_proof_ok = _exists(ready_proof_path)
            handoff_ok = _exists(handoff_path)
            checks.append({"event_id": event_id, "name": "ready_proof_exists", "passed": ready_proof_ok})
            checks.append({"event_id": event_id, "name": "ready_handoff_exists", "passed": handoff_ok})
            if not ready_proof_ok:
                violations.append(
                    {
                        "kind": "missing_ready_proof",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing ready proof {ready_proof_path}",
                        "refs": [ready_proof_path],
                    }
                )
            if not handoff_ok:
                violations.append(
                    {
                        "kind": "missing_handoff",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing READY handoff {handoff_path}",
                        "refs": [handoff_path],
                    }
                )
            if task_key is not None:
                ready_validated_tasks.add(task_key)

        if event_type == "ready.approved":
            if task_key is not None and task_key not in ready_validated_tasks:
                violations.append(
                    {
                        "kind": "ready_approved_without_validate",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": "ready.approved has no prior ready.validated",
                        "refs": [],
                    }
                )
            ready_path = str(payload.get("ready_proof_path", ""))
            handoff_path = str(payload.get("handoff_path", ""))
            approval_refs = [
                ref for ref, ref_posix in zip(artifact_refs, artifact_refs_posix) if "approvals/ready.json" in ref_posix
            ]
            ready_ok = _exists(ready_path)
            handoff_ok = _exists(handoff_path)
            approval_ok = any(_exists(ref) for ref in approval_refs)
            checks.append({"event_id": event_id, "name": "ready_proof_exists", "passed": ready_ok})
            checks.append({"event_id": event_id, "name": "ready_handoff_exists", "passed": handoff_ok})
            checks.append({"event_id": event_id, "name": "ready_approval_exists", "passed": approval_ok})
            if not ready_ok:
                violations.append(
                    {
                        "kind": "missing_ready_proof",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing ready proof {ready_path}",
                        "refs": [ready_path],
                    }
                )
            if not handoff_ok:
                violations.append(
                    {
                        "kind": "missing_handoff",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing READY handoff {handoff_path}",
                        "refs": [handoff_path],
                    }
                )
            if not approval_ok:
                violations.append(
                    {
                        "kind": "missing_ready_approval",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing READY approval artifact {approval_refs[0] if approval_refs else ''}",
                        "refs": approval_refs,
                    }
                )

        if event_type == "retro.completed":
            retro_file = str(payload.get("retro_file", ""))
            patch_file = str(payload.get("patch_file", ""))
            retro_ok = _exists(retro_file)
            patch_ok = _exists(patch_file)
            checks.append({"event_id": event_id, "name": "retro_file_exists", "passed": retro_ok})
            checks.append({"event_id": event_id, "name": "retro_patch_exists", "passed": patch_ok})
            if not retro_ok:
                violations.append(
                    {
                        "kind": "missing_retro_file",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing retro file {retro_file}",
                        "refs": [retro_file],
                    }
                )
            if not patch_ok:
                violations.append(
                    {
                        "kind": "missing_patch_file",
                        "event_id": event_id,
                        "module_id": module_id,
                        "task_id": task_id,
                        "slice_id": None,
                        "message": f"missing patch proposal {patch_file}",
                        "refs": [patch_file],
                    }
                )

    violation_lines: list[str] = []
    for item in violations:
        message = f"{item['event_id']}: {item['message']}"
        if message not in violation_lines:
            violation_lines.append(message)
        for ref in item.get("refs", []):
            if isinstance(ref, str) and ref:
                refs.add(ref)

    status = "ok" if not violation_lines else "failed"
    next_block = {"recommended": "csk status --json", "alternatives": ["csk replay --check"]}
    if violations:
        next_block = _recommend_next(violations[0])

    return {
        "status": status,
        "checks": checks,
        "violations": violation_lines,
        "refs": sorted(refs),
        "next": next_block,
    }
