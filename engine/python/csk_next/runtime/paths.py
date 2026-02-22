"""Filesystem path helpers for CSK layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Layout:
    """Resolved project layout."""

    root: Path

    @property
    def csk(self) -> Path:
        return self.root / ".csk"

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
        return self.root / ".agents" / "skills"

    @property
    def root_agents(self) -> Path:
        return self.root / "AGENTS.md"

    def module_root(self, module_path: str) -> Path:
        return self.root / module_path

    def module_csk(self, module_path: str) -> Path:
        return self.module_root(module_path) / ".csk"

    def module_kernel(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "module"

    def module_tasks(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "tasks"

    def module_run(self, module_path: str) -> Path:
        return self.module_csk(module_path) / "run"


def resolve_layout(root: str | Path | None = None) -> Layout:
    """Resolve layout from explicit root or current working directory."""
    if root is None:
        return Layout(Path.cwd())
    return Layout(Path(root).resolve())
