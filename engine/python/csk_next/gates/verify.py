"""Verify gate implementation."""

from __future__ import annotations

import shlex
from pathlib import Path

from csk_next.domain.schemas import validate_schema
from csk_next.io.runner import run_argv
from csk_next.runtime.proofs import write_proof
from csk_next.runtime.time import utc_now_iso


def parse_cmds(raw_commands: list[str]) -> list[list[str]]:
    """Parse CLI command strings into argv lists."""
    parsed: list[list[str]] = []
    for raw in raw_commands:
        if "|" in raw:
            raise ValueError("Pipelines are not allowed in verify commands")
        argv = shlex.split(raw)
        if not argv:
            continue
        parsed.append(argv)
    return parsed


def run_verify(
    *,
    task_id: str,
    slice_id: str,
    task_run_dir: Path,
    cwd: Path,
    commands: list[list[str]],
    require_at_least_one: bool = False,
) -> dict[str, object]:
    command_results = []
    passed = True
    failure_reason: str | None = None
    if require_at_least_one and not commands:
        passed = False
        failure_reason = "verify_commands_missing"
    for argv in commands:
        result = run_argv(argv, cwd=cwd, check=False)
        command_results.append(
            {
                "argv": argv,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.returncode != 0:
            passed = False

    proof = {
        "task_id": task_id,
        "slice_id": slice_id,
        "passed": passed,
        "executed_count": len(command_results),
        "failure_reason": failure_reason,
        "commands": command_results,
        "checked_at": utc_now_iso(),
    }
    validate_schema("verify_proof", proof)
    write_proof(task_run_dir, "verify", proof, slice_id=slice_id)
    return proof
