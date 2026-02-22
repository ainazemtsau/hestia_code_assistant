"""File lock primitives."""

from __future__ import annotations

import contextlib
from pathlib import Path

from csk_next.io.files import ensure_dir


@contextlib.contextmanager
def file_lock(path: Path):
    """Coarse lock based on lockfile creation."""
    ensure_dir(path.parent)
    lock_path = path.with_suffix(path.suffix + ".lock")
    while True:
        try:
            fd = lock_path.open("x", encoding="utf-8")
            break
        except FileExistsError:
            continue
    try:
        fd.write("locked")
        fd.flush()
        yield
    finally:
        fd.close()
        lock_path.unlink(missing_ok=True)
