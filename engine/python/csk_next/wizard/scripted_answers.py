"""Scripted wizard answer parsing and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from csk_next.io.files import read_text
from csk_next.runtime.paths import Layout
from csk_next.wizard.fsm import wizard_steps

_STEP_ORDER = tuple(step.step_id for step in wizard_steps())
_ALLOWED_STEPS = set(_STEP_ORDER)
_ALLOWED_SHAPES = {"single", "multi", "auto"}
_ALLOWED_PLAN_OPTIONS = {"A", "B", "C"}
_ALLOWED_CONFIRM = {"yes", "no"}


def _parse_json_doc(raw: str, source_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source_name}: invalid JSON ({exc.msg} at line {exc.lineno}, column {exc.colno})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{source_name}: JSON root must be an object")
    return payload


def _normalize_module_mapping(value: Any, source_name: str, step_id: str) -> str:
    if isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            raise ValueError(f"{source_name}: '{step_id}' cannot be empty")
        return normalized

    tokens: list[str] = []
    if isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, str):
                token = item.strip()
                if not token:
                    raise ValueError(f"{source_name}: '{step_id}[{index}]' cannot be empty")
                tokens.append(token)
                continue
            if not isinstance(item, dict):
                raise ValueError(f"{source_name}: '{step_id}[{index}]' must be string or object")
            module_id = item.get("module_id")
            module_path = item.get("path")
            if not isinstance(module_id, str) or not module_id.strip():
                raise ValueError(f"{source_name}: '{step_id}[{index}].module_id' must be a non-empty string")
            if module_path is None:
                tokens.append(module_id.strip())
                continue
            if not isinstance(module_path, str) or not module_path.strip():
                raise ValueError(f"{source_name}: '{step_id}[{index}].path' must be a non-empty string")
            tokens.append(f"{module_id.strip()}:{module_path.strip()}")
    elif isinstance(value, dict):
        for raw_module_id in sorted(value):
            module_id = str(raw_module_id).strip()
            if not module_id:
                raise ValueError(f"{source_name}: '{step_id}' contains an empty module id")
            module_path = value[raw_module_id]
            if module_path is None:
                tokens.append(module_id)
                continue
            if not isinstance(module_path, str) or not module_path.strip():
                raise ValueError(f"{source_name}: '{step_id}.{module_id}' must be a non-empty string or null")
            tokens.append(f"{module_id}:{module_path.strip()}")
    else:
        raise ValueError(f"{source_name}: '{step_id}' must be a string, list, or object")

    if not tokens:
        raise ValueError(f"{source_name}: '{step_id}' cannot be empty")
    return ",".join(tokens)


def _normalize_answers_doc(payload: dict[str, Any], source_name: str) -> dict[str, str]:
    answers_node: Any
    if "answers" in payload:
        answers_node = payload["answers"]
    else:
        answers_node = payload
    if not isinstance(answers_node, dict):
        raise ValueError(f"{source_name}: 'answers' must be an object")

    unknown = sorted(str(key) for key in answers_node.keys() if str(key) not in _ALLOWED_STEPS)
    if unknown:
        known = ", ".join(_STEP_ORDER)
        raise ValueError(f"{source_name}: unknown answer keys: {', '.join(unknown)}; allowed keys: {known}")

    normalized: dict[str, str] = {}
    for step_id in _STEP_ORDER:
        if step_id not in answers_node:
            continue
        value = answers_node[step_id]
        if step_id == "intake_request":
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{source_name}: '{step_id}' must be a non-empty string")
            normalized[step_id] = value.strip()
            continue
        if step_id == "module_mapping":
            normalized[step_id] = _normalize_module_mapping(value, source_name, step_id)
            continue
        if step_id == "execution_shape":
            if not isinstance(value, str):
                raise ValueError(f"{source_name}: '{step_id}' must be a string")
            shape = value.strip().lower()
            if shape not in _ALLOWED_SHAPES:
                raise ValueError(f"{source_name}: '{step_id}' must be one of: single, multi, auto")
            normalized[step_id] = shape
            continue
        if step_id == "planning_option":
            if not isinstance(value, str):
                raise ValueError(f"{source_name}: '{step_id}' must be a string")
            option = value.strip().upper()
            if option not in _ALLOWED_PLAN_OPTIONS:
                raise ValueError(f"{source_name}: '{step_id}' must be one of: A, B, C")
            normalized[step_id] = option
            continue
        if step_id == "confirm_materialization":
            if isinstance(value, bool):
                normalized[step_id] = "yes" if value else "no"
                continue
            if not isinstance(value, str):
                raise ValueError(f"{source_name}: '{step_id}' must be yes/no or boolean")
            decision = value.strip().lower()
            if decision not in _ALLOWED_CONFIRM:
                raise ValueError(f"{source_name}: '{step_id}' must be one of: yes, no")
            normalized[step_id] = decision
            continue

    if not normalized:
        raise ValueError(f"{source_name}: no scripted answers provided")
    return normalized


def _resolve_answers_file(layout: Layout, answers_ref: str) -> Path:
    ref = answers_ref.strip()
    if not ref.startswith("@"):
        raise ValueError("run --answers expects @path/to/answers.json")
    raw_path = ref[1:].strip()
    if not raw_path:
        raise ValueError("run --answers expects a non-empty @path")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = layout.repo_root / candidate
    return candidate.resolve()


def _load_answers_file(layout: Layout, answers_ref: str) -> dict[str, str]:
    path = _resolve_answers_file(layout, answers_ref)
    if not path.exists():
        raise FileNotFoundError(f"answers file not found: {path}")
    data = _parse_json_doc(read_text(path), f"answers file '{path}'")
    return _normalize_answers_doc(data, f"answers file '{path}'")


def _legacy_answers(
    *,
    request: str | None,
    modules: str | None,
    shape: str | None,
    plan_option: str | None,
    auto_confirm: bool,
) -> dict[str, str] | None:
    payload: dict[str, Any] = {}
    if request is not None:
        payload["intake_request"] = request
    if modules is not None:
        payload["module_mapping"] = modules
    if shape is not None:
        payload["execution_shape"] = shape
    if plan_option is not None:
        payload["planning_option"] = plan_option
    if auto_confirm:
        payload["confirm_materialization"] = "yes"
    if not payload:
        return None
    return _normalize_answers_doc(payload, "run flags")


def resolve_run_answers(
    *,
    layout: Layout,
    answers_ref: str | None,
    answers_json: str | None,
    request: str | None,
    modules: str | None,
    shape: str | None,
    plan_option: str | None,
    auto_confirm: bool,
) -> dict[str, str] | None:
    has_explicit_answers = answers_ref is not None or answers_json is not None
    has_legacy_flags = any([request is not None, modules is not None, shape is not None, plan_option is not None, auto_confirm])

    if answers_ref is not None and answers_json is not None:
        raise ValueError("Use either --answers or --answers-json, not both")
    if has_explicit_answers and has_legacy_flags:
        raise ValueError("Do not mix --answers/--answers-json with legacy run flags (--request/--modules/--shape/--plan-option/--yes)")

    if answers_ref is not None:
        return _load_answers_file(layout, answers_ref)
    if answers_json is not None:
        payload = _parse_json_doc(answers_json, "run --answers-json")
        return _normalize_answers_doc(payload, "run --answers-json")
    return _legacy_answers(
        request=request,
        modules=modules,
        shape=shape,
        plan_option=plan_option,
        auto_confirm=auto_confirm,
    )

