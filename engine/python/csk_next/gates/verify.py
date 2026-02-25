"""Verify gate implementation."""

from __future__ import annotations

import shlex
from pathlib import Path
from time import perf_counter

from csk_next.domain.schemas import validate_schema
from csk_next.io.files import ensure_dir, write_text
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


def enforce_command_policy(
    commands: list[list[str]],
    *,
    allowlist: set[str] | None = None,
    denylist: set[str] | None = None,
) -> None:
    allow = allowlist or set()
    deny = denylist or set()
    for argv in commands:
        if not argv:
            continue
        cmd = argv[0]
        if cmd in deny:
            raise ValueError(f"Command denied by policy: {cmd}")
        if allow and cmd not in allow:
            raise ValueError(f"Command not allowed by policy: {cmd}")


def run_verify(
    *,
    task_id: str,
    slice_id: str,
    task_run_dir: Path,
    cwd: Path,
    commands: list[list[str]],
    require_at_least_one: bool = False,
    allowlist: set[str] | None = None,
    denylist: set[str] | None = None,
) -> dict[str, object]:
    enforce_command_policy(commands, allowlist=allowlist, denylist=denylist)

    command_results = []
    passed = True
    failure_reason: str | None = None
    started = perf_counter()
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

    duration_ms = int((perf_counter() - started) * 1000)
    checked_at = utc_now_iso()
    log_dir = task_run_dir / "logs"
    ensure_dir(log_dir)
    log_path = log_dir / f"verify-{checked_at.replace(':', '').replace('-', '')}.log"
    lines: list[str] = []
    for item in command_results:
        argv = " ".join(item["argv"])
        lines.append(f"$ {argv}")
        lines.append(f"exit={item['returncode']}")
        stdout = str(item.get("stdout", "")).rstrip()
        stderr = str(item.get("stderr", "")).rstrip()
        if stdout:
            lines.append("stdout:")
            lines.append(stdout)
        if stderr:
            lines.append("stderr:")
            lines.append(stderr)
        lines.append("")
    write_text(log_path, "\n".join(lines).rstrip() + "\n")

    proof = {
        "task_id": task_id,
        "slice_id": slice_id,
        "passed": passed,
        "executed_count": len(command_results),
        "failure_reason": failure_reason,
        "commands": command_results,
        "duration_ms": duration_ms,
        "log_path": str(log_path),
        "checked_at": checked_at,
    }
    validate_schema("verify_proof", proof)
    write_proof(task_run_dir, "verify", proof, slice_id=slice_id)
    return proof
