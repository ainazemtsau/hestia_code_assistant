"""Local overlay configuration helpers."""

from __future__ import annotations

from typing import Any

from csk_next.io.files import read_json
from csk_next.runtime.paths import Layout


_DEFAULT_CONFIG: dict[str, Any] = {
    "schema_version": "1.0.0",
    "default_profile": "default",
    "worktree_default": True,
    "allowlist_commands": [],
    "denylist_commands": ["rm", "sudo", "curl", "wget"],
    "user_check_mode": "profile_optional",
}


def load_local_config(layout: Layout) -> dict[str, Any]:
    path = layout.local / "config.json"
    if not path.exists():
        return dict(_DEFAULT_CONFIG)

    data = read_json(path)
    merged = dict(_DEFAULT_CONFIG)
    merged.update(data)
    return merged


def worktree_default_enabled(layout: Layout) -> bool:
    config = load_local_config(layout)
    return bool(config.get("worktree_default", True))


def command_policy(layout: Layout) -> tuple[set[str], set[str]]:
    config = load_local_config(layout)
    allow = {str(item).strip() for item in config.get("allowlist_commands", []) if str(item).strip()}
    deny = {str(item).strip() for item in config.get("denylist_commands", []) if str(item).strip()}
    return allow, deny
