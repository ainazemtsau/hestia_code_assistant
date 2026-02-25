"""Git worktree helpers."""

from __future__ import annotations

from pathlib import Path

from csk_next.io.files import ensure_dir
from csk_next.io.files import read_json, write_json
from csk_next.io.runner import run_argv


def create_module_worktree(
    *,
    repo_root: Path,
    state_root: Path,
    mission_id: str,
    module_id: str,
) -> dict[str, object]:
    """Create a worktree for the module, returning status metadata."""
    target = state_root / ".csk" / "worktrees" / mission_id / module_id
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


def ensure_worktrees_for_mission(*, repo_root: Path, state_root: Path, mission_dir: Path) -> dict[str, object]:
    routing = read_json(mission_dir / "routing.json")
    worktrees_path = mission_dir / "worktrees.json"
    doc = read_json(worktrees_path) if worktrees_path.exists() else {"module_worktrees": {}, "opt_out_modules": []}
    create_status = doc.get("create_status", {})
    if not isinstance(create_status, dict):
        create_status = {}

    changed = 0
    for route in routing.get("module_routes", []):
        module_id = str(route.get("module_id", ""))
        if not module_id:
            continue
        info = create_module_worktree(
            repo_root=repo_root,
            state_root=state_root,
            mission_id=mission_dir.name,
            module_id=module_id,
        )
        doc.setdefault("module_worktrees", {})[module_id] = str(info["path"])
        create_status[module_id] = {
            "created": bool(info["created"]),
            "branch": str(info["branch"]),
            "fallback_reason": info["fallback_reason"],
        }
        changed += 1
    doc["create_status"] = create_status
    write_json(worktrees_path, doc)
    return {"status": "ok", "mission_id": mission_dir.name, "updated": changed, "worktrees": doc.get("module_worktrees", {})}
