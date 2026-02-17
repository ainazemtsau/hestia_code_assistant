#!/usr/bin/env python3
"""
Install CSK rules into Codex user rules directory.

Codex typically stores rules under ~/.codex/rules/.
This script installs: ~/.codex/rules/csk.rules

Idempotent; safe to re-run.
"""
from __future__ import annotations
import os
from pathlib import Path
import shutil

def main() -> int:
    home = Path(os.path.expanduser("~"))
    codex_home = Path(os.environ.get("CODEX_HOME", str(home / ".codex")))
    rules_dir = codex_home / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)

    src = Path(__file__).resolve().parent / "rules" / "csk.rules"
    if not src.exists():
        raise SystemExit(f"Missing rules file: {src}")

    dst = rules_dir / "csk.rules"
    shutil.copyfile(src, dst)
    print(f"[csk] installed rules: {dst}")
    print("[csk] restart Codex for rules to take effect.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
