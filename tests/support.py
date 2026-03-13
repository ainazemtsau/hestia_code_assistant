from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from shutil import copytree, ignore_patterns, rmtree
from typing import Iterator
from uuid import uuid4


REPO_ROOT = Path(__file__).parent.parent
TEST_TMP_ROOT = REPO_ROOT / ".test-tmp"


def _create_scratch_dir(parent: Path, prefix: str) -> Path:
    parent.mkdir(parents=True, exist_ok=True)
    while True:
        candidate = parent / f"{prefix}{uuid4().hex}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue


@contextmanager
def repo_temp_dir() -> Iterator[Path]:
    tmp = _create_scratch_dir(TEST_TMP_ROOT, "tmp")
    try:
        yield tmp
    finally:
        rmtree(tmp, ignore_errors=True)


@contextmanager
def workflow_test_roots() -> Iterator[tuple[Path, Path]]:
    with repo_temp_dir() as workspace:
        project_root = workspace / "client-project"
        workflow_root = project_root / "workflow-checkout"
        project_root.mkdir(parents=True, exist_ok=True)
        copytree(REPO_ROOT / "install", workflow_root / "install")
        copytree(
            REPO_ROOT / "tools" / "csk",
            workflow_root / "tools" / "csk",
            ignore=ignore_patterns("__pycache__"),
        )
        yield project_root, workflow_root
