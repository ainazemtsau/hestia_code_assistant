"""Filesystem path helpers for CSK layout."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path, PurePosixPath


def _normalize_relative_path(raw: str) -> Path:
    """Normalize a repo-relative path and reject path escapes."""
    value = raw.strip().replace("\\", "/")
    if value in {"", "."}:
        return Path(".")

    posix_path = PurePosixPath(value)
    if posix_path.is_absolute():
        raise ValueError(f"Path must be relative: {raw}")

    parts: list[str] = []
    for part in posix_path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            raise ValueError(f"Path cannot escape repository root: {raw}")
        parts.append(part)

    return Path(*parts) if parts else Path(".")


@dataclass(frozen=True)
class Layout:
    """Resolved project layout."""

    repo_root: Path
    state_root: Path

    @property
    def root(self) -> Path:
        """Backward-compatible alias for repository root."""
        return self.repo_root

    @property
    def csk(self) -> Path:
        return self.state_root / ".csk"

    @property
    def engine(self) -> Path:
        return self.csk / "engine"

    @property
    def local(self) -> Path:
        return self.csk / "local"

    @property
    def app(self) -> Path:
        return self.csk / "app"

    @property
    def registry(self) -> Path:
        return self.app / "registry.json"

    @property
    def app_logs(self) -> Path:
        return self.app / "logs"

    @property
    def app_incidents(self) -> Path:
        return self.app_logs / "incidents.jsonl"

    @property
    def missions(self) -> Path:
        return self.app / "missions"

    @property
    def backlog(self) -> Path:
        return self.app / "backlog.jsonl"

    @property
    def research(self) -> Path:
        return self.app / "research"

    @property
    def agents_skills(self) -> Path:
        return self.state_root / ".agents" / "skills"

    @property
    def root_agents(self) -> Path:
        return self.state_root / "AGENTS.md"

    def module_root(self, module_path: str) -> Path:
        return self.repo_root / _normalize_relative_path(module_path)

    def module_csk(self, module_path: str) -> Path:
        return self.csk / "modules" / _normalize_relative_path(module_path)

    def module_kernel(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "module"

    def module_tasks(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "tasks"

    def module_run(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "run"


def resolve_layout(
    root: str | Path | None = None,
    state_root: str | Path | None = None,
) -> Layout:
    """Resolve layout from explicit root/state-root or current working directory."""
    repo_root = Path.cwd().resolve() if root is None else Path(root).resolve()

    state_arg = state_root if state_root is not None else os.environ.get("CSK_STATE_ROOT")
    if state_arg is None:
        resolved_state_root = repo_root
    else:
        candidate = Path(state_arg).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root / candidate
        resolved_state_root = candidate.resolve()

    return Layout(repo_root=repo_root, state_root=resolved_state_root)
