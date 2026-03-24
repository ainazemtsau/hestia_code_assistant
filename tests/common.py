from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PF_BIN = REPO_ROOT / "pf"


def run_pf(cwd: Path, *args: str, json_mode: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = [str(PF_BIN), *args]
    if json_mode:
        cmd.append("--json")
    return subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def run_pf_json(cwd: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
    proc = run_pf(cwd, *args, json_mode=True)
    payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc, payload


def make_repo() -> tempfile.TemporaryDirectory[str]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name)
    (root / ".git").mkdir(parents=True, exist_ok=True)
    return tmp
