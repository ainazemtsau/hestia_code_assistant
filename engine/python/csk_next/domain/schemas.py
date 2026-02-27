"""Lightweight schema validation for CSK artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SchemaValidationError(ValueError):
    """Raised when artifact validation fails."""


@dataclass(frozen=True)
class SchemaDef:
    required_keys: tuple[str, ...]


SCHEMAS: dict[str, SchemaDef] = {
    "registry": SchemaDef(("schema_version", "modules", "defaults", "updated_at")),
    "mission": SchemaDef(("mission_id", "title", "summary", "status", "created_at", "updated_at")),
    "mission_routing": SchemaDef(("mission_id", "module_routes", "assumptions", "risks")),
    "mission_milestones": SchemaDef(("mission_id", "milestones", "updated_at")),
    "mission_worktrees": SchemaDef(("mission_id", "module_worktrees", "opt_out_modules")),
    "task_state": SchemaDef(("task_id", "module_id", "status", "profile", "max_attempts", "slices")),
    "slices": SchemaDef(("slices",)),
    "critic_report": SchemaDef(("task_id", "critic", "p0", "p1", "p2", "p3", "notes", "passed", "reviewed_at")),
    "freeze": SchemaDef(("task_id", "plan_sha256", "slices_sha256", "frozen_at")),
    "approval": SchemaDef(("approved_by", "approved_at")),
    "review_proof": SchemaDef(("task_id", "slice_id", "p0", "p1", "p2", "p3", "passed", "recorded_at")),
    "scope_proof": SchemaDef(("task_id", "slice_id", "passed", "violations", "checked_at")),
    "verify_proof": SchemaDef(("task_id", "slice_id", "passed", "commands", "checked_at")),
    "ready_proof": SchemaDef(("task_id", "passed", "checks", "checked_at")),
    "incident": SchemaDef(("id", "severity", "kind", "phase", "message", "created_at")),
    "profile": SchemaDef(("name", "required_gates", "e2e", "recommended")),
    "event_envelope": SchemaDef(("id", "ts", "type", "actor", "payload", "artifact_refs", "engine_version")),
}


def _require_keys(data: dict[str, Any], required_keys: tuple[str, ...], schema_name: str) -> None:
    missing = [key for key in required_keys if key not in data]
    if missing:
        missing_csv = ", ".join(missing)
        raise SchemaValidationError(f"Schema '{schema_name}' missing required keys: {missing_csv}")


def _require_type(value: Any, expected: type | tuple[type, ...], field: str) -> None:
    if not isinstance(value, expected):
        expected_name = (
            ", ".join(item.__name__ for item in expected)
            if isinstance(expected, tuple)
            else expected.__name__
        )
        raise SchemaValidationError(f"Field '{field}' must be {expected_name}")


def _require_list_of_str(value: Any, field: str) -> None:
    _require_type(value, list, field)
    if any(not isinstance(item, str) for item in value):
        raise SchemaValidationError(f"Field '{field}' must contain strings")


def _validate_registry(data: dict[str, Any]) -> None:
    _require_type(data["schema_version"], str, "schema_version")
    _require_type(data["defaults"], dict, "defaults")
    _require_type(data["modules"], list, "modules")

    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    for index, module in enumerate(data["modules"]):
        if not isinstance(module, dict):
            raise SchemaValidationError(f"modules[{index}] must be object")
        _require_keys(
            module,
            ("module_id", "path", "registered", "initialized", "created_at", "updated_at"),
            "registry.module",
        )
        _require_type(module["module_id"], str, f"modules[{index}].module_id")
        _require_type(module["path"], str, f"modules[{index}].path")
        _require_type(module["registered"], bool, f"modules[{index}].registered")
        _require_type(module["initialized"], bool, f"modules[{index}].initialized")
        module_id = module["module_id"]
        module_path = module["path"]
        if module_id in seen_ids:
            raise SchemaValidationError(f"Duplicate module_id in registry: {module_id}")
        if module_path in seen_paths:
            raise SchemaValidationError(f"Duplicate module path in registry: {module_path}")
        seen_ids.add(module_id)
        seen_paths.add(module_path)


def _validate_task_state(data: dict[str, Any]) -> None:
    from csk_next.domain.models import SLICE_STATUSES, TASK_STATUSES

    _require_type(data["task_id"], str, "task_id")
    _require_type(data["module_id"], str, "module_id")
    _require_type(data["status"], str, "status")
    _require_type(data["profile"], str, "profile")
    _require_type(data["max_attempts"], int, "max_attempts")
    _require_type(data["slices"], dict, "slices")

    if data["max_attempts"] <= 0:
        raise SchemaValidationError("Field 'max_attempts' must be > 0")
    if data["status"] not in TASK_STATUSES:
        raise SchemaValidationError(f"Unknown task status: {data['status']}")
    if data["status"] == "blocked" and not data.get("blocked_reason"):
        raise SchemaValidationError("Field 'blocked_reason' is required when task status is blocked")

    for slice_id, slice_state in data["slices"].items():
        if not isinstance(slice_id, str):
            raise SchemaValidationError("Slice state key must be string")
        if not isinstance(slice_state, dict):
            raise SchemaValidationError(f"Slice state '{slice_id}' must be object")
        _require_keys(slice_state, ("status", "attempts", "max_attempts"), "task_state.slice")
        _require_type(slice_state["status"], str, f"slices[{slice_id}].status")
        _require_type(slice_state["attempts"], int, f"slices[{slice_id}].attempts")
        _require_type(slice_state["max_attempts"], int, f"slices[{slice_id}].max_attempts")
        if slice_state["status"] not in SLICE_STATUSES:
            raise SchemaValidationError(f"Unknown slice status '{slice_state['status']}' for {slice_id}")
        if slice_state["attempts"] < 0:
            raise SchemaValidationError(f"slices[{slice_id}].attempts must be >= 0")
        if slice_state["max_attempts"] <= 0:
            raise SchemaValidationError(f"slices[{slice_id}].max_attempts must be > 0")


def _validate_slices(data: dict[str, Any]) -> None:
    from csk_next.domain.models import SLICE_STATUSES

    _require_type(data["slices"], list, "slices")
    seen: set[str] = set()
    required = (
        "slice_id",
        "title",
        "allowed_paths",
        "required_gates",
        "deps",
        "traceability",
        "max_attempts",
        "verify_commands",
        "e2e_required",
        "status",
        "attempts",
        "last_error",
    )
    for index, row in enumerate(data["slices"]):
        if not isinstance(row, dict):
            raise SchemaValidationError(f"slices[{index}] must be object")
        _require_keys(row, required, "slices.item")
        _require_type(row["slice_id"], str, f"slices[{index}].slice_id")
        slice_id = row["slice_id"]
        if slice_id in seen:
            raise SchemaValidationError(f"Duplicate slice_id: {slice_id}")
        seen.add(slice_id)

        _require_list_of_str(row["allowed_paths"], f"slices[{index}].allowed_paths")
        _require_list_of_str(row["required_gates"], f"slices[{index}].required_gates")
        _require_list_of_str(row["deps"], f"slices[{index}].deps")
        _require_list_of_str(row["traceability"], f"slices[{index}].traceability")
        _require_list_of_str(row["verify_commands"], f"slices[{index}].verify_commands")
        _require_type(row["max_attempts"], int, f"slices[{index}].max_attempts")
        _require_type(row["e2e_required"], bool, f"slices[{index}].e2e_required")
        _require_type(row["status"], str, f"slices[{index}].status")
        _require_type(row["attempts"], int, f"slices[{index}].attempts")
        if row["status"] not in SLICE_STATUSES:
            raise SchemaValidationError(f"Unknown slice status '{row['status']}' for {slice_id}")
        if row["max_attempts"] <= 0:
            raise SchemaValidationError(f"slices[{index}].max_attempts must be > 0")
        if row["attempts"] < 0:
            raise SchemaValidationError(f"slices[{index}].attempts must be >= 0")


def _validate_mission_worktrees(data: dict[str, Any]) -> None:
    _require_type(data["mission_id"], str, "mission_id")
    _require_type(data["module_worktrees"], dict, "module_worktrees")
    _require_list_of_str(data["opt_out_modules"], "opt_out_modules")

    for module_id, path in data["module_worktrees"].items():
        if not isinstance(module_id, str):
            raise SchemaValidationError("module_worktrees keys must be strings")
        _require_type(path, str, f"module_worktrees[{module_id}]")

    create_status = data.get("create_status")
    if create_status is None:
        return
    _require_type(create_status, dict, "create_status")
    for module_id, status in create_status.items():
        if not isinstance(module_id, str):
            raise SchemaValidationError("create_status keys must be strings")
        if not isinstance(status, dict):
            raise SchemaValidationError(f"create_status[{module_id}] must be object")
        _require_keys(status, ("created", "branch", "fallback_reason"), "mission_worktrees.create_status")
        _require_type(status["created"], bool, f"create_status[{module_id}].created")
        _require_type(status["branch"], str, f"create_status[{module_id}].branch")
        fallback_reason = status["fallback_reason"]
        if fallback_reason is not None and not isinstance(fallback_reason, str):
            raise SchemaValidationError(f"create_status[{module_id}].fallback_reason must be string or null")


def _validate_profile(data: dict[str, Any]) -> None:
    _require_type(data["name"], str, "name")
    _require_list_of_str(data["required_gates"], "required_gates")
    _require_type(data["e2e"], dict, "e2e")
    _require_type(data["recommended"], dict, "recommended")

    if "default_commands" in data:
        _require_type(data["default_commands"], dict, "default_commands")
    if "user_check_required" in data:
        _require_type(data["user_check_required"], bool, "user_check_required")

    e2e = data["e2e"]
    _require_keys(e2e, ("required", "commands"), "profile.e2e")
    _require_type(e2e["required"], bool, "e2e.required")
    _require_list_of_str(e2e["commands"], "e2e.commands")

    recommended = data["recommended"]
    _require_keys(recommended, ("linters", "test_frameworks", "skills", "mcp"), "profile.recommended")
    _require_list_of_str(recommended["linters"], "recommended.linters")
    _require_list_of_str(recommended["test_frameworks"], "recommended.test_frameworks")
    _require_list_of_str(recommended["skills"], "recommended.skills")
    _require_list_of_str(recommended["mcp"], "recommended.mcp")


def _validate_verify_proof(data: dict[str, Any]) -> None:
    _require_type(data["task_id"], str, "task_id")
    _require_type(data["slice_id"], str, "slice_id")
    _require_type(data["passed"], bool, "passed")
    _require_type(data["commands"], list, "commands")
    if "executed_count" in data:
        _require_type(data["executed_count"], int, "executed_count")
        if data["executed_count"] < 0:
            raise SchemaValidationError("executed_count must be >= 0")


def _validate_critic_report(data: dict[str, Any]) -> None:
    _require_type(data["task_id"], str, "task_id")
    _require_type(data["critic"], str, "critic")
    _require_type(data["notes"], str, "notes")
    _require_type(data["passed"], bool, "passed")
    _require_type(data["reviewed_at"], str, "reviewed_at")
    for field in ["p0", "p1", "p2", "p3"]:
        _require_type(data[field], int, field)
        if data[field] < 0:
            raise SchemaValidationError(f"Field '{field}' must be >= 0")


def _validate_event_envelope(data: dict[str, Any]) -> None:
    _require_type(data["id"], str, "id")
    _require_type(data["ts"], str, "ts")
    _require_type(data["type"], str, "type")
    _require_type(data["actor"], str, "actor")
    _require_type(data["payload"], dict, "payload")
    _require_list_of_str(data["artifact_refs"], "artifact_refs")
    _require_type(data["engine_version"], str, "engine_version")

    for optional_field in [
        "mission_id",
        "module_id",
        "task_id",
        "slice_id",
        "repo_git_head",
        "worktree_path",
    ]:
        value = data.get(optional_field)
        if value is not None and not isinstance(value, str):
            raise SchemaValidationError(f"Field '{optional_field}' must be string or null")


EXTRA_VALIDATORS = {
    "registry": _validate_registry,
    "task_state": _validate_task_state,
    "slices": _validate_slices,
    "mission_worktrees": _validate_mission_worktrees,
    "profile": _validate_profile,
    "verify_proof": _validate_verify_proof,
    "critic_report": _validate_critic_report,
    "event_envelope": _validate_event_envelope,
}


def validate_schema(name: str, data: dict[str, Any]) -> None:
    """Validate dictionary against required key set."""
    if name not in SCHEMAS:
        raise SchemaValidationError(f"Unknown schema: {name}")
    if not isinstance(data, dict):
        raise SchemaValidationError(f"Schema '{name}' expects JSON object")
    required_keys = SCHEMAS[name].required_keys
    _require_keys(data, required_keys, name)
    validator = EXTRA_VALIDATORS.get(name)
    if validator is not None:
        validator(data)


def validate_or_raise(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Pass-through validation helper."""
    validate_schema(name, data)
    return data
