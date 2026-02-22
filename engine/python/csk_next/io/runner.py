"""Deterministic subprocess runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess, run


class RunnerError(RuntimeError):
    """Raised when command execution fails."""


@dataclass(frozen=True)
class RunResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


def run_argv(argv: list[str], cwd: Path | None = None, check: bool = False) -> RunResult:
    if not argv:
        raise RunnerError("Empty argv")
    process: CompletedProcess[str] = run(
        argv,
        cwd=str(cwd) if cwd is not None else None,
        capture_output=True,
        text=True,
        check=False,
    )
    result = RunResult(
        argv=argv,
        returncode=process.returncode,
        stdout=process.stdout,
        stderr=process.stderr,
    )
    if check and process.returncode != 0:
        raise RunnerError(f"Command failed ({process.returncode}): {' '.join(argv)}\n{process.stderr}")
    return result
