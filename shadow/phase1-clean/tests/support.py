from __future__ import annotations

import sys
from contextlib import contextmanager
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from shutil import copytree, ignore_patterns, rmtree
from typing import Iterator
from uuid import uuid4


SHADOW_ROOT = Path(__file__).parent.parent
TMP_ROOT = SHADOW_ROOT / ".tmp"


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
    tmp = _create_scratch_dir(TMP_ROOT, "tmp")
    try:
        yield tmp
    finally:
        rmtree(tmp, ignore_errors=True)


def load_shadow_module(name: str, rel_path: str):
    module_path = SHADOW_ROOT / rel_path
    spec = spec_from_file_location(name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@contextmanager
def workflow_test_roots() -> Iterator[tuple[Path, Path]]:
    with repo_temp_dir() as workspace:
        project_root = workspace / "client-project"
        workflow_root = project_root / "workflow-checkout"
        project_root.mkdir(parents=True, exist_ok=True)
        copytree(SHADOW_ROOT / "install", workflow_root / "install")
        copytree(
            SHADOW_ROOT / "tools",
            workflow_root / "tools",
            ignore=ignore_patterns("__pycache__"),
        )
        yield project_root, workflow_root
