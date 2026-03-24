"""Repository and .pf path resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pfpkg.errors import EXIT_IO, PfError


@dataclass(frozen=True)
class PFPaths:
    repo_root: Path

    @property
    def pf_dir(self) -> Path:
        return self.repo_root / ".pf"

    @property
    def pf_db_path(self) -> Path:
        return self.pf_dir / "state.db"

    @property
    def agents_dir(self) -> Path:
        return self.repo_root / ".agents"

    @property
    def skills_dir(self) -> Path:
        return self.agents_dir / "skills" / "pf"

    @property
    def artifacts_dir(self) -> Path:
        return self.pf_dir / "artifacts"

    @property
    def bundles_dir(self) -> Path:
        return self.artifacts_dir / "bundles"

    @property
    def modules_dir(self) -> Path:
        return self.pf_dir / "modules"

    @property
    def missions_dir(self) -> Path:
        return self.pf_dir / "missions"

    @property
    def local_dir(self) -> Path:
        return self.pf_dir / "local"


def find_repo_root(cwd: Path | None = None) -> Path:
    current = (cwd or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        marker = candidate / ".git"
        if marker.exists():
            return candidate
    raise PfError("not inside a git repository (missing .git)", EXIT_IO)


def detect_docpack_templates(repo_root: Path) -> Path | None:
    candidate = repo_root / "powerflow_pf_mvp_docpack_v1 (1)" / "templates"
    if candidate.exists():
        return candidate
    return None
