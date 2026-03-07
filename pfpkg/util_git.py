"""Git helpers (best-effort, deterministic output)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_tree_hash(repo_root: Path, rel_path: str) -> tuple[str | None, bool]:
    code, out, _ = run_git(repo_root, ["rev-parse", f"HEAD:{rel_path}"])
    tree = out if code == 0 and out else None
    code2, out2, _ = run_git(repo_root, ["status", "--porcelain", "--", rel_path])
    dirty = bool(out2) if code2 == 0 else False
    return tree, dirty
