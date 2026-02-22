"""Profile loading and merging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.state import load_profile
from csk_next.io.files import read_json


DEFAULT_PROFILE = {
    "name": "default",
    "required_gates": ["scope", "verify", "review"],
    "default_commands": {},
    "e2e": {
        "required": False,
        "commands": [],
    },
    "user_check_required": False,
    "recommended": {
        "linters": [],
        "test_frameworks": [],
        "skills": [],
        "mcp": [],
    },
}


def merge_profile(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "name": override.get("name", base.get("name", "default")),
        "required_gates": override.get("required_gates", base.get("required_gates", [])),
        "default_commands": override.get("default_commands", base.get("default_commands", {})),
        "e2e": {
            "required": override.get("e2e", {}).get(
                "required", base.get("e2e", {}).get("required", False)
            ),
            "commands": override.get("e2e", {}).get(
                "commands", base.get("e2e", {}).get("commands", [])
            ),
        },
        "user_check_required": bool(
            override.get("user_check_required", base.get("user_check_required", False))
        ),
        "recommended": {
            "linters": override.get("recommended", {}).get(
                "linters", base.get("recommended", {}).get("linters", [])
            ),
            "test_frameworks": override.get("recommended", {}).get(
                "test_frameworks", base.get("recommended", {}).get("test_frameworks", [])
            ),
            "skills": override.get("recommended", {}).get(
                "skills", base.get("recommended", {}).get("skills", [])
            ),
            "mcp": override.get("recommended", {}).get(
                "mcp", base.get("recommended", {}).get("mcp", [])
            ),
        },
    }
    load_profile_data(merged)
    return merged


def load_profile_data(data: dict[str, Any]) -> dict[str, Any]:
    profile = {
        "name": data["name"],
        "required_gates": list(data["required_gates"]),
        "default_commands": dict(data.get("default_commands", {})),
        "e2e": data["e2e"],
        "user_check_required": bool(data.get("user_check_required", False)),
        "recommended": data["recommended"],
    }
    return load_profile_dict(profile)


def load_profile_dict(data: dict[str, Any]) -> dict[str, Any]:
    # Reuse schema checks implemented in state loader.
    if not isinstance(data.get("required_gates"), list):
        raise ValueError("Profile required_gates must be list")
    if not isinstance(data.get("default_commands", {}), dict):
        raise ValueError("Profile default_commands must be object")
    if not isinstance(data.get("user_check_required", False), bool):
        raise ValueError("Profile user_check_required must be bool")
    return data


def load_profile_from_paths(engine_path: Path, local_path: Path, name: str = "default") -> dict[str, Any]:
    engine_profile_path = engine_path / "templates" / "profiles" / f"{name}.json"
    local_profile_path = local_path / "profiles" / f"{name}.json"

    base = DEFAULT_PROFILE
    if engine_profile_path.exists():
        base = merge_profile(base, read_json(engine_profile_path))
    if local_profile_path.exists():
        base = merge_profile(base, read_json(local_profile_path))
    return base
