"""Domain errors and mapped exit codes for pf CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EXIT_OK = 0
EXIT_USAGE = 2
EXIT_VALIDATION = 10
EXIT_NOT_INITIALIZED = 20
EXIT_NOT_FOUND = 30
EXIT_IO = 40


@dataclass
class PfError(Exception):
    """Raised for expected CLI failures."""

    message: str
    code: int = EXIT_VALIDATION
    details: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message
