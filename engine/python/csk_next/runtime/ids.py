"""Identifier helpers for Mission/Task IDs."""

from __future__ import annotations

import re
from pathlib import Path


_ID_PATTERNS = {
    "M": re.compile(r"^M-(\d{4})$"),
    "T": re.compile(r"^T-(\d{4})$"),
}


def _next_id(prefix: str, parent: Path) -> str:
    max_seen = 0
    if parent.exists():
        for child in parent.iterdir():
            match = _ID_PATTERNS[prefix].match(child.name)
            if match:
                max_seen = max(max_seen, int(match.group(1)))
    return f"{prefix}-{max_seen + 1:04d}"


def next_mission_id(missions_dir: Path) -> str:
    return _next_id("M", missions_dir)


def next_task_id(tasks_dir: Path) -> str:
    return _next_id("T", tasks_dir)
