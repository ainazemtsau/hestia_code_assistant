"""Output helpers for human/json modes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandResult:
    command: str
    ok: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    next: dict[str, Any] | None = None
    human_lines: list[str] = field(default_factory=list)

    def as_json(self) -> dict[str, Any]:
        out: dict[str, Any] = {"ok": self.ok, "command": self.command}
        if self.data:
            out["data"] = self.data
        if self.next is not None:
            out["next"] = self.next
        return out


def print_json_only(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def print_human(lines: list[str]) -> None:
    for line in lines:
        print(line)
