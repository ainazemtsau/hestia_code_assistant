"""Domain model builders for CSK artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any

from csk_next.runtime.time import utc_now_iso


TASK_STATUSES = {
    "draft",
    "critic_passed",
    "frozen",
    "plan_approved",
    "executing",
    "ready_validated",
    "ready_approved",
    "blocked",
    "retro_done",
    "closed",
}

TASK_TRANSITIONS: dict[str, set[str]] = {
    "draft": {"critic_passed"},
    "critic_passed": {"frozen"},
    "frozen": {"plan_approved"},
    "plan_approved": {"executing"},
    "executing": {"ready_validated", "blocked"},
    "ready_validated": {"ready_approved", "blocked"},
    "ready_approved": {"retro_done"},
    "blocked": {"retro_done"},
    "retro_done": {"closed"},
    "closed": set(),
}

SLICE_STATUSES = {
    "pending",
    "running",
    "gate_failed",
    "review_failed",
    "blocked",
    "done",
}

MISSION_STATUSES = {"draft", "active", "milestone_done", "ready", "closed"}


@dataclass(frozen=True)
class ModuleRecord:
    """Module entry persisted in registry."""

    module_id: str
    path: str
    initialized: bool
    created_at: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "path": self.path,
            "initialized": self.initialized,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class Registry:
    """Top-level registry model."""

    schema_version: str
    modules: list[ModuleRecord]
    defaults: dict[str, Any]
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "modules": [mod.to_dict() for mod in self.modules],
            "defaults": self.defaults,
            "updated_at": self.updated_at,
        }


def new_registry() -> Registry:
    now = utc_now_iso()
    return Registry(
        schema_version="1.0.0",
        modules=[],
        defaults={
            "worktree_policy": "per_module",
            "proof_storage": "worktree_run",
            "user_check": "profile_optional",
        },
        updated_at=now,
    )


def normalize_module_path(module_path: str) -> str:
    raw = module_path.strip().replace("\\", "/")
    if raw in {"", "."}:
        return "."

    posix_path = PurePosixPath(raw)
    if posix_path.is_absolute():
        raise ValueError(f"Module path must be relative: {module_path}")

    parts: list[str] = []
    for part in posix_path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError(f"Module path cannot escape repository root: {module_path}")
        parts.append(part)

    return "/".join(parts) if parts else "."


def new_module_record(module_id: str, module_path: str) -> ModuleRecord:
    now = utc_now_iso()
    normalized = normalize_module_path(module_path)
    return ModuleRecord(
        module_id=module_id,
        path=normalized,
        initialized=False,
        created_at=now,
        updated_at=now,
    )


def mission_stub(mission_id: str, title: str, summary: str) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "mission_id": mission_id,
        "title": title,
        "summary": summary,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
    }


def mission_routing_stub(mission_id: str, module_ids: list[str]) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "mission_id": mission_id,
        "module_routes": [
            {
                "module_id": module_id,
                "goal": "",
                "scope": "",
                "non_scope": "",
                "worktree_opt_out": False,
            }
            for module_id in module_ids
        ],
        "assumptions": [],
        "risks": [],
        "updated_at": now,
    }


def milestone_stub(mission_id: str) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "mission_id": mission_id,
        "milestones": [
            {
                "milestone_id": "MS-0001",
                "title": "Milestone 1",
                "status": "draft",
                "module_items": [],
                "depends_on": [],
                "parallel_groups": [],
                "integration_checks": [],
            }
        ],
        "updated_at": now,
    }


def worktree_map_stub(mission_id: str) -> dict[str, Any]:
    return {
        "mission_id": mission_id,
        "module_worktrees": {},
        "opt_out_modules": [],
    }


def intake_stub(request: str) -> dict[str, Any]:
    text = request.lower()
    if any(token in text for token in ["и", "plus", "integration", "across", "module"]):
        kind = "multi_module_mission"
    elif len(text.split()) < 8:
        kind = "unknown_need_discovery"
    else:
        kind = "single_module_task"
    return {
        "classification": kind,
        "routing_draft": [],
        "milestone_draft": "MS-0001",
        "preserved_areas": [],
        "options": [
            {
                "id": "A",
                "name": "Минимальные изменения",
                "pros": ["Быстрее"],
                "cons": ["Меньше охват"],
                "recommended": kind == "single_module_task",
            },
            {
                "id": "B",
                "name": "Баланс",
                "pros": ["Умеренный риск"],
                "cons": ["Требует больше проверки"],
                "recommended": kind == "multi_module_mission",
            },
            {
                "id": "C",
                "name": "Полный редизайн",
                "pros": ["Максимальный охват"],
                "cons": ["Дороже и дольше"],
                "recommended": False,
            },
        ],
    }


def task_state_stub(
    task_id: str,
    mission_id: str | None,
    module_id: str,
    profile: str,
    max_attempts: int,
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "task_id": task_id,
        "mission_id": mission_id,
        "module_id": module_id,
        "status": "draft",
        "blocked_reason": None,
        "profile": profile,
        "max_attempts": max_attempts,
        "slices": {},
        "created_at": now,
        "updated_at": now,
    }


def default_slice_entry(slice_id: str) -> dict[str, Any]:
    return {
        "slice_id": slice_id,
        "title": f"Slice {slice_id}",
        "allowed_paths": ["."],
        "required_gates": ["scope", "verify", "review"],
        "deps": [],
        "traceability": [],
        "max_attempts": 2,
        "verify_commands": ["python -c \"print('verify ok')\""],
        "e2e_required": False,
        "status": "pending",
        "attempts": 0,
        "last_error": None,
    }


def ensure_task_transition(current: str, target: str) -> None:
    if current not in TASK_STATUSES:
        raise ValueError(f"Unknown current task status: {current}")
    if target not in TASK_STATUSES:
        raise ValueError(f"Unknown target task status: {target}")
    if current == target:
        return
    allowed = TASK_TRANSITIONS[current]
    if target not in allowed:
        raise ValueError(f"Invalid task status transition: {current} -> {target}")
