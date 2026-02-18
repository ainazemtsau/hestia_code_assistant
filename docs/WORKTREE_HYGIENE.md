# Worktree hygiene (Codex app) — CSK‑M Pro v2

When running parallel work, use Codex app worktrees.

Guidelines
- Use detached HEAD during implementation to avoid branch checkout conflicts across worktrees.
- Create a branch only when you are ready to commit/publish locally.
- Archive worktree threads after completion.

Cleanup
- Keep proof packs in `run/` so you do not create merge conflicts.
- If a worktree is stale, regenerate it from main and re-apply patches if needed.

If you want strict enforcement, add a manual checklist:
- scope-check passed
- verify passed
- review recorded
- user-check recorded with pass
- validate-ready passed
- only then create branch/commit
