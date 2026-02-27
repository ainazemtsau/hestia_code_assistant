#!/usr/bin/env python3
"""Thin launcher for CSK CLI.

This module is a fallback entrypoint when `csk` is unavailable on PATH.
It adds the local engine python source to module path before importing CLI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _bootstrap_pythonpath() -> None:
    script_dir = Path(__file__).resolve().parent
    engine_python = script_dir.parent / "engine" / "python"
    engine_python_str = str(engine_python)

    if str(engine_python) not in sys.path:
        sys.path.insert(0, engine_python_str)

    if "PYTHONPATH" in os.environ:
        prefix = os.environ["PYTHONPATH"]
        if engine_python_str not in prefix.split(":"):
            os.environ["PYTHONPATH"] = f"{engine_python_str}:{prefix}"
    else:
        os.environ["PYTHONPATH"] = engine_python_str


_bootstrap_pythonpath()

from csk_next.cli.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
