"""Git worktree helpers."""

from __future__ import annotations

from pathlib import Path

from csk_next.io.files import ensure_dir
from csk_next.io.runner import run_argv


def create_module_worktree(
    *,
    repo_root: Path,
    mission_id: str,
    module_id: str,
) -> dict[str, object]:
    """Create a worktree for the module, returning status metadata."""
    target = repo_root / ".csk" / "worktrees" / mission_id / module_id
    ensure_dir(target.parent)

    branch = f"csk/{mission_id}/{module_id}"
    in_repo = run_argv(["git", "-C", str(repo_root), "rev-parse", "--is-inside-work-tree"], check=False)
    if in_repo.returncode != 0:
        return {
            "created": False,
            "path": str(target),
            "branch": branch,
            "fallback_reason": "not_a_git_repository",
            "stderr": in_repo.stderr,
        }

    if target.exists() and any(target.iterdir()):
        return {
            "created": True,
            "path": str(target),
            "branch": branch,
            "fallback_reason": None,
            "stderr": "",
        }

    create = run_argv(
        [
            "git",
            "-C",
            str(repo_root),
            "worktree",
            "add",
            "-b",
            branch,
            str(target),
            "HEAD",
        ],
        check=False,
    )
    if create.returncode == 0:
        return {
            "created": True,
            "path": str(target),
            "branch": branch,
            "fallback_reason": None,
            "stderr": "",
        }

    existing_branch = run_argv(
        ["git", "-C", str(repo_root), "worktree", "add", str(target), branch],
        check=False,
    )
    if existing_branch.returncode == 0:
        return {
            "created": True,
            "path": str(target),
            "branch": branch,
            "fallback_reason": None,
            "stderr": "",
        }

    return {
        "created": False,
        "path": str(target),
        "branch": branch,
        "fallback_reason": "worktree_create_failed",
        "stderr": create.stderr or existing_branch.stderr,
    }
