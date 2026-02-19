#!/usr/bin/env python3
"""
CSK‑M Pro v2 — helper CLI (stdlib-only).

Key properties:
- Enforceable gates:
  - Plan Freeze + Plan Approval required
  - Scope-check enforced via git change inspection vs allowed_paths
  - Verify runs toolchain gates deterministically and writes proofs
  - Review is recorded as machine-readable proof (review.json)
  - validate-ready blocks until all required proofs + approvals exist
- No cross-process file locks (avoid Windows PermissionError patterns).
- Runtime outputs go to `run/` directories (gitignored by default).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import retro_evolution as _retro_evo
except Exception:
    _retro_evo = None

REPO_ROOT_MARKERS = [".git", ".csk-app", ".agents", ".codex", "AGENTS.md"]

def utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for parent in [p] + list(p.parents):
        if any((parent / m).exists() for m in REPO_ROOT_MARKERS):
            if (parent / ".git").exists():
                return parent
            return parent
    return p

def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)

def atomic_write_json(path: Path, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")

def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _require_retro_engine() -> Any:
    if _retro_evo is None:
        raise SystemExit("retro_evolution module is unavailable.")
    return _retro_evo


def _retro_validate_strict(repo: Path) -> Tuple[bool, List[str], List[str]]:
    cmd = [sys.executable, str((repo / "tools" / "csk" / "csk.py").resolve()), "validate", "--all", "--strict", "--json"]
    p = subprocess.run(cmd, cwd=str(repo), capture_output=True, text=True)
    raw = (p.stdout or "").strip() or (p.stderr or "").strip()
    if not raw:
        return False, ["validate produced no output"], []
    try:
        obj = json.loads(raw)
    except Exception as e:
        return False, [f"validate json parse failed: {e}"], []
    if not isinstance(obj, dict):
        return False, ["validate json output is not object"], []
    ok = bool(obj.get("ok", False))
    errors = obj.get("errors", []) if isinstance(obj.get("errors", []), list) else []
    warnings = obj.get("warnings", []) if isinstance(obj.get("warnings", []), list) else []
    return ok, [str(e) for e in errors], [str(w) for w in warnings]


def _log_workflow_drift_incident(repo: Path, summary: str, evidence: str = "") -> None:
    payload = {
        "ts": utc_now_iso(),
        "module": None,
        "stage": "retro-apply",
        "severity": "P1",
        "type": "workflow-overlay-drift",
        "summary": summary,
        "evidence": {"raw": evidence} if evidence else {},
        "proposed_fix": ["Run retro-rollback or regenerate workflow state via retro-plan/apply."],
        "status": "open",
    }
    append_jsonl(repo / ".csk-app" / "logs" / "incidents.jsonl", payload)


def _enforce_overlay_guard_for_command(repo: Path, cmd_name: str) -> None:
    revo = _require_retro_engine()
    # Retro lifecycle + read-only commands are exempt from pre-exec guard.
    exempt = {
        "status",
        "validate",
        "retro",
        "retro-plan",
        "retro-approve",
        "retro-apply",
        "retro-history",
        "retro-rollback",
        "retro-action-complete",
    }
    if cmd_name in exempt:
        return

    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})
    mids = [str(m.get("id")) for m in reg.get("modules", []) if isinstance(m, dict) and m.get("id")]
    errors, _warnings, _infos = revo.validate_contracts(repo, mids)
    drift_markers = {
        "workflow overlay hash drift detected",
        "workflow overlay assets hash drift detected",
        "workflow overlay config hash drift detected",
    }
    matched = [err for err in errors if err in drift_markers]
    if matched:
        _log_workflow_drift_incident(
            repo,
            f"Blocked command `{cmd_name}` due to workflow overlay drift.",
            evidence="; ".join(matched),
        )
        raise SystemExit("Workflow overlay drift detected. Resolve via retro lifecycle before mutating commands.")

def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "x"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


PLAN_SUMMARY_START = "<!-- PLAN_SUMMARY_START -->"
PLAN_SUMMARY_END = "<!-- PLAN_SUMMARY_END -->"
USER_ACCEPTANCE_START = "<!-- USER_ACCEPTANCE_START -->"
USER_ACCEPTANCE_END = "<!-- USER_ACCEPTANCE_END -->"


def extract_plan_summary_block(plan_text: str) -> Optional[str]:
    m = re.search(
        rf"{re.escape(PLAN_SUMMARY_START)}\s*(.*?)\s*{re.escape(PLAN_SUMMARY_END)}",
        plan_text,
        flags=re.S,
    )
    if not m:
        return None
    block = m.group(1).strip()
    return block or None


def extract_user_acceptance_block(plan_text: str) -> Optional[str]:
    m = re.search(
        rf"{re.escape(USER_ACCEPTANCE_START)}\s*(.*?)\s*{re.escape(USER_ACCEPTANCE_END)}",
        plan_text,
        flags=re.S,
    )
    if not m:
        return None
    block = m.group(1).strip()
    return block or None


def build_plan_summary_file(
    repo: Path,
    plan_path: Path,
    module_id: str,
    task_id: str,
    title: str,
    *,
    require_block: bool = True,
) -> str:
    summary_tpl = (repo / "templates" / "task" / "plan.summary.md").read_text(encoding="utf-8")
    plan_text = plan_path.read_text(encoding="utf-8")
    block = extract_plan_summary_block(plan_text)
    if not block:
        if not require_block:
            block = (
                "## Needs cleanup\n"
                "- `PLAN_SUMMARY_START/PLAN_SUMMARY_END` block was not found in plan.md.\n"
                "- Add a short shareable block in `plan.md` and rerun `regen-plan-summary`.\n"
            )
        else:
            raise SystemExit("plan.md missing PLAN_SUMMARY_START/END markers. Add the shareable block before freeze.")
    return summary_tpl.replace("<module>", module_id).replace("<T-id>", task_id).replace("<title>", title).replace("<summary_block>", block)


def build_user_acceptance_file(
    repo: Path,
    plan_path: Path,
    module_id: str,
    task_id: str,
    title: str,
    *,
    require_block: bool = True,
) -> str:
    acceptance_tpl = (repo / "templates" / "task" / "user_acceptance.md").read_text(encoding="utf-8")
    plan_text = plan_path.read_text(encoding="utf-8")
    block = extract_user_acceptance_block(plan_text)
    if not block:
        if not require_block:
            block = (
                "## Needs cleanup\n"
                "- `USER_ACCEPTANCE_START/USER_ACCEPTANCE_END` block was not found in plan.md.\n"
                "- Fill this block with concrete manual checks and rerun `regen-user-acceptance` before user CHECK."
            )
        else:
            raise SystemExit("plan.md missing USER_ACCEPTANCE_START/END markers. Add manual acceptance instructions before freeze.")
    return acceptance_tpl.replace("<module>", module_id).replace("<T-id>", task_id).replace("<title>", title).replace("<acceptance_block>", block)


def sync_plan_summary(repo: Path, plan_path: Path, summary_path: Path, module_id: str, task_id: str, title: str,
                      *, require_block: bool = True) -> None:
    content = build_plan_summary_file(
        repo,
        plan_path,
        module_id,
        task_id,
        title,
        require_block=require_block,
    )
    atomic_write_text(summary_path, content)


def sync_user_acceptance(repo: Path, plan_path: Path, acceptance_path: Path, module_id: str, task_id: str, title: str,
                         *, require_block: bool = True) -> None:
    content = build_user_acceptance_file(
        repo,
        plan_path,
        module_id,
        task_id,
        title,
        require_block=require_block,
    )
    atomic_write_text(acceptance_path, content)


def validate_plan_summary_hash(tdir: Path, freeze: Dict[str, Any], require_summary_hash: bool = False) -> List[str]:
    violations: List[str] = []
    summary_path = tdir / "plan.summary.md"
    plan_summary_sha = freeze.get("plan_summary_sha256")

    if require_summary_hash:
        if not summary_path.exists():
            violations.append("missing plan.summary.md (required for strict plan summary checks)")
            return violations
        if not plan_summary_sha:
            violations.append("plan.freeze.json missing plan_summary_sha256; re-run freeze-plan to regenerate it.")
        elif sha256_file(summary_path) != plan_summary_sha:
            violations.append("plan.summary.md hash mismatch vs freeze (summary drift)")
    elif plan_summary_sha:
        if not summary_path.exists():
            violations.append("plan_summary_sha256 exists but plan.summary.md is missing")
        elif sha256_file(summary_path) != plan_summary_sha:
            violations.append("plan.summary.md hash mismatch vs freeze (summary drift)")
    return violations

def _path_is_subpath(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def resolve_module_path_matches(repo: Path, cwd: Path) -> List[Tuple[str, Path, Path]]:
    """Return candidate module matches for cwd.

    Returns tuples: (module_id, module_rel_path, module_abs_path).
    Sorted by deepest registry path first.
    """
    reg_path = repo / ".csk-app" / "registry.json"
    reg = load_json(reg_path, default={"modules": []})
    modules = reg.get("modules", []) if isinstance(reg, dict) else []

    cwd = cwd.resolve()
    out: List[Tuple[str, Path, Path]] = []
    for m in modules:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        rel = m.get("path")
        if not isinstance(mid, str) or not isinstance(rel, str):
            continue
        abs_root = (repo / rel).resolve()
        if _path_is_subpath(cwd, abs_root):
            out.append((mid, Path(rel), abs_root))

    out.sort(key=lambda item: len(item[1].parts), reverse=True)
    return out


def resolve_module_from_cwd(repo: Path, cwd: Path) -> Tuple[Optional[Tuple[str, Path, Dict[str, Any]]], List[str]]:
    """Resolve module from cwd.

    Priority:
    1) .csk marker under cwd tree with matching module path
    2) longest registry path prefix match
    Returns (module_tuple, errors). On success errors is empty.
    """
    reg_path = repo / ".csk-app" / "registry.json"
    reg = load_json(reg_path, default={"modules": []})
    modules = reg.get("modules", []) if isinstance(reg, dict) else []
    by_path = {Path(m.get("path", "")): m for m in modules if isinstance(m, dict) and isinstance(m.get("id"), str) and isinstance(m.get("path"), str)}

    matches = resolve_module_path_matches(repo, cwd)

    if not matches:
        return None, [
            "MODULE_CONTEXT_REQUIRED: current directory is not inside any module path from registry.",
            "Run from a module worktree/module directory or pass --module-id explicitly.",
        ]

    # Prefer nearest .csk marker only when registry explicitly maps it to a module.
    for p in [cwd.resolve()] + list(cwd.resolve().parents):
        marker = p / ".csk"
        if not marker.is_dir():
            continue
        try:
            rel = p.relative_to(repo)
        except ValueError:
            continue
        exact = [m for m in matches if m[1] == rel]
        if exact:
            if len(exact) == 1:
                mid, rel_path, _ = exact[0]
                return (mid, rel_path, by_path.get(rel_path, {})), []
            return None, [
                f"Ambiguous module context at marker {marker}: "
                f"{', '.join(sorted(m[0] for m in exact))}",
                "Use --module-id to force explicit module selection.",
            ]

    # Deepest registry match is the correct module.
    if not matches:
        return None, ["MODULE_CONTEXT_REQUIRED: cannot detect module context."]

    max_depth = len(matches[0][1].parts)
    top = [m for m in matches if len(m[1].parts) == max_depth]
    if len(top) > 1:
        return None, [
            f"Ambiguous module context for {cwd}: "
            f"{', '.join(sorted(m[0] for m in top))}",
            "Use --module-id to force explicit module selection.",
        ]

    mid, rel_path, _ = top[0]
    return (mid, rel_path, by_path.get(rel_path, {})), []


def _registry_modules_lines(repo: Path) -> List[str]:
    reg_path = repo / ".csk-app" / "registry.json"
    reg = load_json(reg_path, default={"modules": []})
    modules = reg.get("modules", []) if isinstance(reg, dict) else []
    lines = []
    for m in modules:
        if isinstance(m, dict) and isinstance(m.get("id"), str) and isinstance(m.get("path"), str):
            lines.append(f"- {m.get('id')}: {m.get('path')}")
    return lines


def _module_context_fail(message: str, repo: Path, details: Optional[List[str]] = None) -> None:
    lines = [message]
    if details:
        lines.extend(details)
    known = _registry_modules_lines(repo)
    lines.append("")
    if known:
        lines.append("Known modules:")
        lines.extend(known)
    else:
        lines.append("No modules are registered. Run `add-module` or `bootstrap --apply-candidates` first.")
    lines.append("")
    lines.append("Specify module explicitly with --module-id or run from the module worktree.")
    raise SystemExit("\n".join(lines))


def _normalize_module_task_args(args: argparse.Namespace, repo: Path, cwd: Path) -> None:
    """Normalize commands that operate on <module, task> with dual syntax.

    Supported forms:
    - legacy: <module_id> <task_id>
    - cwd-autodetect: <task_id> (if module is resolvable from current dir)
    - explicit override: --module-id <module_id> <task_id_or_none?>.
    """
    module_override = args.module_id
    module_or_task = args.module_or_task_id
    task_id = args.task_id

    if task_id is None:
        # one positional arg only
        if module_override:
            args.module_id = module_override
            args.task_id = module_or_task
            return

        match, errors = resolve_module_from_cwd(repo, cwd)
        if errors:
            _module_context_fail("MODULE_CONTEXT_REQUIRED: cannot resolve module_id.", repo, errors)
        args.module_id = match[0] if match else None
        args.task_id = module_or_task
        return

    # legacy syntax with explicit module in positional
    args.module_id = module_override or module_or_task
    args.task_id = task_id


def _normalize_module_title_args(args: argparse.Namespace, repo: Path, cwd: Path) -> None:
    """Normalize commands that operate on <module, title> with dual syntax."""
    module_override = args.module_id
    module_or_title = args.module_or_title
    title = args.title

    if title is None:
        # one positional arg only
        if module_override:
            args.module_id = module_override
            args.title = module_or_title
            return

        match, errors = resolve_module_from_cwd(repo, cwd)
        if errors:
            _module_context_fail("MODULE_CONTEXT_REQUIRED: cannot resolve module_id.", repo, errors)
        args.module_id = match[0] if match else None
        args.title = module_or_title
        return

    # legacy syntax: <module_id> <title>
    args.module_id = module_override or module_or_title
    args.title = title


def _normalize_module_only_args(args: argparse.Namespace, repo: Path, cwd: Path) -> None:
    """Normalize commands that need exactly one module and no task/title."""
    module_override = args.module_id
    explicit = args.module_id_arg

    if module_override:
        args.module_id = module_override
        return

    if explicit:
        args.module_id = explicit
        return

    match, errors = resolve_module_from_cwd(repo, cwd)
    if errors:
        _module_context_fail("MODULE_CONTEXT_REQUIRED: cannot resolve module_id.", repo, errors)
    args.module_id = match[0] if match else None


def detect_stack(path: Path) -> str:
    if (path / "ProjectSettings" / "ProjectVersion.txt").exists():
        return "unity"
    if (path / "package.json").exists():
        return "node"
    if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
        return "python"
    if (path / "Cargo.toml").exists():
        return "rust"
    if (path / "go.mod").exists():
        return "go"
    if list(path.glob("*.sln")) or list(path.glob("**/*.csproj")):
        return "dotnet"
    return "unknown"

def default_toolchain_for(stack: str) -> Dict[str, Any]:
    base = {
        "schema_version": 1,
        "profile": stack,
        "risk": "medium",
        "gates": {
            "install": {"required": True, "cmd": [], "timeout_sec": 1800},
            "lint": {"required": False, "cmd": [], "timeout_sec": 1800},
            "unit": {"required": True, "cmd": [], "timeout_sec": 1800},
            "integration": {"required": False, "cmd": [], "timeout_sec": 1800},
            "e2e": {"required": False, "cmd": [], "timeout_sec": 3600},
            "security": {"required": False, "cmd": [], "timeout_sec": 3600},
        },
        "evidence": {"files": [], "probes": {}},
        "notes": "Populate commands via toolchain-probe or manual edit. No guessing."
    }
    if stack == "node":
        base["gates"]["install"]["cmd"] = ["npm", "ci"]
        base["gates"]["lint"]["required"] = True
        base["gates"]["unit"]["cmd"] = ["npm", "test"]
    elif stack == "python":
        base["gates"]["install"]["cmd"] = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
        base["gates"]["lint"]["required"] = True
        base["gates"]["unit"]["cmd"] = ["python", "-m", "pytest", "-q"]
    elif stack == "rust":
        base["gates"]["install"]["cmd"] = ["cargo", "fetch"]
        base["gates"]["lint"]["required"] = True
        base["gates"]["lint"]["cmd"] = ["cargo", "fmt", "--check"]
        base["gates"]["unit"]["cmd"] = ["cargo", "test"]
    elif stack == "go":
        base["gates"]["install"]["cmd"] = ["go", "mod", "download"]
        base["gates"]["unit"]["cmd"] = ["go", "test", "./..."]
    elif stack == "dotnet":
        base["gates"]["install"]["cmd"] = ["dotnet", "restore"]
        base["gates"]["unit"]["cmd"] = ["dotnet", "test"]
    elif stack == "unity":
        base["risk"] = "high"
        base["gates"]["install"]["required"] = False
        base["gates"]["unit"]["required"] = False
        base["notes"] = "Unity requires Unity runner/editor. Configure commands manually."
    else:
        base["gates"]["install"]["required"] = False
        base["gates"]["unit"]["required"] = False
        base["notes"] = "Unknown stack. Configure commands manually."
    return base

def ensure_app_skeleton(repo: Path) -> None:
    app = repo / ".csk-app"
    (app / "logs").mkdir(parents=True, exist_ok=True)
    (app / "initiatives").mkdir(parents=True, exist_ok=True)
    (app / "public_apis").mkdir(parents=True, exist_ok=True)

    reg_path = app / "registry.json"
    if not reg_path.exists():
        atomic_write_json(reg_path, {
            "schema_version": 2,
            "project": {"name": repo.name, "created_utc": utc_now_iso()},
            "modules": [],
            "public_api_index": ".csk-app/public_apis",
            "backlog": ".csk-app/backlog.jsonl",
            "notes": "Source of truth for module boundaries."
        })

    for p in [app/"logs/decisions.jsonl", app/"logs/incidents.jsonl", app/"backlog.jsonl"]:
        if not p.exists():
            atomic_write_text(p, "")

    digest = app / "digest.md"
    if not digest.exists():
        atomic_write_text(digest, f"# App digest (CSK‑M Pro v2)\n\n- Project: {repo.name}\n- Created: {utc_now_iso()}\n")

def ensure_module_kernel(repo: Path, module_id: str, module_root: Path) -> None:
    # Create module root if missing
    module_root.mkdir(parents=True, exist_ok=True)

    # module-level AGENTS.md
    agents_path = module_root / "AGENTS.md"
    if not agents_path.exists():
        tpl = (repo / "templates" / "module" / "AGENTS.md").read_text(encoding="utf-8")
        atomic_write_text(agents_path, tpl)

    # PUBLIC API
    public_api = module_root / "PUBLIC_API.md"
    if not public_api.exists():
        tpl = (repo / "templates" / "module" / "PUBLIC_API.md").read_text(encoding="utf-8")
        atomic_write_text(public_api, tpl.replace("<module-name>", module_id))

    csk_dir = module_root / ".csk"
    (csk_dir / "logs").mkdir(parents=True, exist_ok=True)
    (csk_dir / "memory").mkdir(exist_ok=True)
    (csk_dir / "tasks").mkdir(exist_ok=True)
    (csk_dir / "public_apis").mkdir(exist_ok=True)

    for p in [csk_dir/"logs/decisions.jsonl", csk_dir/"logs/incidents.jsonl"]:
        if not p.exists():
            atomic_write_text(p, "")

    digest = csk_dir / "digest.md"
    if not digest.exists():
        tpl = (repo / "templates" / "module" / "csk" / "digest.md").read_text(encoding="utf-8")
        atomic_write_text(digest, tpl.replace("<module-name>", module_id))

    toolchain_path = csk_dir / "toolchain.json"
    if not toolchain_path.exists():
        stack = detect_stack(module_root)
        atomic_write_json(toolchain_path, default_toolchain_for(stack))

def registry_add_or_update(repo: Path, module_id: str, rel_path: str) -> None:
    reg_path = repo / ".csk-app" / "registry.json"
    reg = load_json(reg_path, default=None)
    if not reg:
        raise SystemExit("Missing .csk-app/registry.json. Run bootstrap.")
    modules = reg.get("modules", [])
    for m in modules:
        if m.get("id") == module_id:
            m["path"] = rel_path
            m.setdefault("public_api", f"{rel_path}/PUBLIC_API.md")
            m.setdefault("status", "active")
            atomic_write_json(reg_path, reg)
            return
    modules.append({
        "id": module_id,
        "path": rel_path,
        "public_api": f"{rel_path}/PUBLIC_API.md",
        "status": "active",
        "created_utc": utc_now_iso(),
        "notes": ""
    })
    reg["modules"] = modules
    atomic_write_json(reg_path, reg)

def detect_module_candidates(repo: Path) -> List[Tuple[str, str, str]]:
    candidates: List[Tuple[str, str, str]] = []
    roots = []
    for d in ["services", "apps", "packages", "modules"]:
        if (repo / d).exists() and (repo / d).is_dir():
            roots.append(repo / d)

    def add_candidate(path: Path, evidence: str):
        rel = str(path.relative_to(repo)).replace("\\", "/")
        mid = slugify(rel.split("/")[-1])
        candidates.append((mid, rel, evidence))

    for r in roots:
        for child in r.iterdir():
            if not child.is_dir():
                continue
            stack = detect_stack(child)
            if stack != "unknown":
                add_candidate(child, f"{stack} markers")

    if not candidates:
        stack = detect_stack(repo)
        if stack != "unknown":
            add_candidate(repo, f"{stack} markers in repo root")

    # de-dup
    seen = set()
    out = []
    for mid, rel, ev in candidates:
        if rel in seen:
            continue
        seen.add(rel)
        out.append((mid, rel, ev))
    return out

def cmd_bootstrap(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json")
    if not reg.get("modules"):
        cands = detect_module_candidates(repo)
        lines = ["# Module candidates (auto-detected)\n"]
        for mid, rel, ev in cands:
            lines.append(f"- `{mid}` -> `{rel}` ({ev})")
        atomic_write_text(repo / ".csk-app" / "module_candidates.md", "\n".join(lines) + "\n")
        if args.apply_candidates:
            for mid, rel, _ in cands:
                registry_add_or_update(repo, mid, rel)
                ensure_module_kernel(repo, mid, repo / rel)
    print(f"[csk] bootstrap ok repo={repo}")

def cmd_add_module(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    mid = slugify(args.module_id)
    rel = args.path.replace("\\", "/").strip("/")
    registry_add_or_update(repo, mid, rel)
    ensure_module_kernel(repo, mid, repo / rel)
    print(f"[csk] module added {mid} -> {rel}")

def next_task_id(tasks_dir: Path) -> str:
    tasks_dir.mkdir(parents=True, exist_ok=True)
    nums = []
    for p in tasks_dir.iterdir():
        if p.is_dir() and p.name.startswith("T-"):
            m = re.match(r"T-(\d+)", p.name)
            if m:
                nums.append(int(m.group(1)))
    n = max(nums) + 1 if nums else 1
    return f"T-{n:04d}"

def get_module(repo: Path, module_id: str) -> Dict[str, Any]:
    reg = load_json(repo / ".csk-app" / "registry.json")
    module_id = slugify(module_id)
    module = next((m for m in reg.get("modules", []) if m.get("id") == module_id), None)
    if not module:
        raise SystemExit(f"Unknown module: {module_id}")
    return module

def task_paths(repo: Path, module_id: str, task_id: str) -> Tuple[Path, Path]:
    m = get_module(repo, module_id)
    module_root = repo / m["path"]
    tdir = module_root / ".csk" / "tasks" / task_id
    if not tdir.exists():
        raise SystemExit(f"Unknown task: {task_id} in module {module_id}")
    run_dir = tdir / "run"
    proofs_dir = run_dir / "proofs"
    approvals_dir = tdir / "approvals"
    approvals_dir.mkdir(parents=True, exist_ok=True)
    run_dir.mkdir(parents=True, exist_ok=True)
    proofs_dir.mkdir(parents=True, exist_ok=True)
    return tdir, module_root

def task_title(tdir: Path, task_id: str) -> str:
    st = load_json(tdir / "run" / "status.json", default={})
    title = st.get("title")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return task_id


def cmd_new_task(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    m = get_module(repo, args.module_id)
    module_root = repo / m["path"]
    ensure_module_kernel(repo, m["id"], module_root)

    tasks_dir = module_root / ".csk" / "tasks"
    tid = next_task_id(tasks_dir)
    tdir = tasks_dir / tid
    tdir.mkdir(parents=True, exist_ok=True)
    (tdir / "approvals").mkdir(exist_ok=True)
    (tdir / "run").mkdir(exist_ok=True)
    (tdir / "run" / "proofs").mkdir(exist_ok=True)

    plan_tpl = (repo / "templates" / "task" / "plan.md").read_text(encoding="utf-8")
    plan_text = plan_tpl.replace("<module>", m["id"]).replace("<T-id>", tid).replace("<title>", args.title)
    atomic_write_text(tdir / "plan.md", plan_text)
    sync_plan_summary(
        repo,
        tdir / "plan.md",
        tdir / "plan.summary.md",
        m["id"],
        tid,
        args.title,
        require_block=True,
    )
    sync_user_acceptance(
        repo,
        tdir / "plan.md",
        tdir / "user_acceptance.md",
        m["id"],
        tid,
        args.title,
        require_block=False,
    )
    slices_tpl = load_json(repo / "templates" / "task" / "slices.json")
    slices_tpl["task_id"] = tid
    slices_tpl["module"] = m["id"]
    atomic_write_json(tdir / "slices.json", slices_tpl)

    # runtime status (ignored)
    atomic_write_json(tdir / "run" / "status.json", {
        "task_id": tid,
        "module": m["id"],
        "title": args.title,
        "created_utc": utc_now_iso(),
        "phase": "planning",
        "plan_frozen": False,
        "plan_approved": False,
        "ready_approved": False,
        "active_slice": None,
        "slice_attempts": {}
    })
    print(f"[csk] new task: {m['id']}/{tid}")
    print(f"[csk] plan.md: {tdir / 'plan.md'}")
    print(f"[csk] plan.summary.md: {tdir / 'plan.summary.md'}")
    print(f"[csk] user_acceptance.md: {tdir / 'user_acceptance.md'}")

def cmd_freeze_plan(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, module_root = task_paths(repo, args.module_id, args.task_id)
    plan_path = tdir / "plan.md"
    slices_path = tdir / "slices.json"
    if not plan_path.exists() or not slices_path.exists():
        raise SystemExit("Missing plan.md or slices.json")

    title = task_title(tdir, args.task_id)

    summary_path = tdir / "plan.summary.md"
    sync_plan_summary(
        repo,
        plan_path,
        summary_path,
        args.module_id,
        args.task_id,
        title,
        require_block=True,
    )
    if not summary_path.exists():
        raise SystemExit("Failed to write plan.summary.md while freezing.")

    acceptance_path = tdir / "user_acceptance.md"
    sync_user_acceptance(
        repo,
        plan_path,
        acceptance_path,
        args.module_id,
        args.task_id,
        title,
        require_block=True,
    )
    if not acceptance_path.exists():
        raise SystemExit("Failed to write user_acceptance.md while freezing.")

    # Validate slices.json before freezing (prevents freezing broken contracts)
    slices_obj = load_json(slices_path)
    try:
        e, _w = _validate_slices_obj(slices_obj)  # defined later; safe at runtime
    except NameError:
        e = []  # fallback if validate helpers were removed
    if e:
        raise SystemExit("Cannot freeze: slices.json invalid: " + "; ".join(e))
    if isinstance(slices_obj, dict):
        if slices_obj.get("task_id") and slices_obj.get("task_id") != args.task_id:
            raise SystemExit(f"Cannot freeze: slices.task_id mismatch ({slices_obj.get('task_id')} != {args.task_id})")
        if slices_obj.get("module") and slices_obj.get("module") != slugify(args.module_id):
            raise SystemExit(f"Cannot freeze: slices.module mismatch ({slices_obj.get('module')} != {slugify(args.module_id)})")
    freeze = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "frozen_utc": utc_now_iso(),
        "plan_sha256": sha256_file(plan_path),
        "slices_sha256": sha256_file(slices_path),
        "plan_summary_sha256": sha256_file(summary_path),
        "note": "Any plan change requires new Critic review + re-freeze."
    }
    atomic_write_json(tdir / "plan.freeze.json", freeze)

    st_path = tdir / "run" / "status.json"
    st = load_json(st_path, default={})
    st["plan_frozen"] = True
    st["phase"] = "planning-approval"
    atomic_write_json(st_path, st)

    print(f"[csk] plan frozen: {args.module_id}/{args.task_id}")

def cmd_approve_plan(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, _ = task_paths(repo, args.module_id, args.task_id)
    freeze_path = tdir / "plan.freeze.json"
    if not freeze_path.exists():
        raise SystemExit("Plan is not frozen. Run freeze-plan first.")
    # Refuse approval if freeze has drift (plan/slices/summary changed after freeze)
    ok_freeze, freeze_viol = validate_freeze(tdir, require_summary_hash=True)
    if not ok_freeze:
        raise SystemExit("Plan freeze invalid: " + "; ".join(freeze_viol))
    # Basic slices contract sanity (catches manual JSON edits early)
    slices_obj = load_json(tdir / "slices.json")
    try:
        e, _w = _validate_slices_obj(slices_obj)
    except NameError:
        e = []
    if e:
        raise SystemExit("Cannot approve: slices.json invalid: " + "; ".join(e))

    approval = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "approved_utc": utc_now_iso(),
        "approved_by": args.by or "user",
        "note": args.note or ""
    }
    atomic_write_json(tdir / "approvals" / "plan.json", approval)

    st_path = tdir / "run" / "status.json"
    st = load_json(st_path, default={})
    st["plan_approved"] = True
    st["phase"] = "execution"
    atomic_write_json(st_path, st)

    print(f"[csk] plan approved: {args.module_id}/{args.task_id}")

def cmd_approve_ready(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, module_root = task_paths(repo, args.module_id, args.task_id)
    ready_check = _collect_ready_requirements(repo, tdir, module_root, args.module_id, args.task_id)
    if not ready_check:
        raise SystemExit("READY preconditions failed.")
    approval = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "approved_utc": utc_now_iso(),
        "approved_by": args.by or "user",
        "note": args.note or ""
    }
    atomic_write_json(tdir / "approvals" / "ready.json", approval)

    st_path = tdir / "run" / "status.json"
    st = load_json(st_path, default={})
    st["ready_approved"] = True
    st["phase"] = "done"
    atomic_write_json(st_path, st)

    print(f"[csk] ready approved: {args.module_id}/{args.task_id}")


def cmd_regen_plan_summary(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, _ = task_paths(repo, args.module_id, args.task_id)
    plan_path = tdir / "plan.md"
    if not plan_path.exists():
        raise SystemExit("Missing plan.md")
    summary_path = tdir / "plan.summary.md"
    title = load_json(tdir / "run" / "status.json", default={}).get("title", args.task_id)
    sync_plan_summary(
        repo,
        plan_path,
        summary_path,
        args.module_id,
        args.task_id,
        title,
        require_block=False,
    )
    print(f"[csk] regenerated plan summary: {summary_path}")


def _normalize_checks(raw: Optional[List[str]]) -> List[str]:
    if not raw:
        return []
    out: List[str] = []
    for item in raw:
        if not isinstance(item, str):
            continue
        parts = [p.strip() for p in item.split(",") if p.strip()]
        if parts:
            out.extend(parts)
        elif item.strip():
            out.append(item.strip())
    return out


def cmd_regen_user_acceptance(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, _ = task_paths(repo, args.module_id, args.task_id)
    plan_path = tdir / "plan.md"
    if not plan_path.exists():
        raise SystemExit("Missing plan.md")
    acceptance_path = tdir / "user_acceptance.md"
    title = task_title(tdir, args.task_id)
    sync_user_acceptance(
        repo,
        plan_path,
        acceptance_path,
        args.module_id,
        args.task_id,
        title,
        require_block=args.require_block,
    )
    print(f"[csk] regenerated user acceptance checklist: {acceptance_path}")


def cmd_record_user_check(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, _ = task_paths(repo, args.module_id, args.task_id)
    ua_path = tdir / "user_acceptance.md"
    if not ua_path.exists():
        raise SystemExit("Missing user_acceptance.md. Run freeze-plan or regen-user-acceptance first.")
    checks = _normalize_checks(args.checks)
    approval = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "checked_utc": utc_now_iso(),
        "checked_by": args.tested_by or "user",
        "result": args.result,
        "notes": args.notes.strip(),
        "checks": checks,
        "evidence": args.evidence.strip(),
        "user_acceptance_sha256": sha256_file(ua_path),
    }
    if not approval["notes"]:
        raise SystemExit("record-user-check requires --notes.")
    atomic_write_json(tdir / "approvals" / "user-check.json", approval)
    print(f"[csk] user-check recorded: {tdir / 'approvals' / 'user-check.json'}")


def validate_freeze(tdir: Path, require_summary_hash: bool = False) -> Tuple[bool, List[str]]:
    violations: List[str] = []
    freeze = load_json(tdir / "plan.freeze.json", default=None)
    if not freeze:
        violations.append("missing plan.freeze.json")
        return False, violations
    plan_path = tdir / "plan.md"
    slices_path = tdir / "slices.json"
    if sha256_file(plan_path) != freeze.get("plan_sha256"):
        violations.append("plan.md hash mismatch vs freeze (plan drift)")
    if sha256_file(slices_path) != freeze.get("slices_sha256"):
        violations.append("slices.json hash mismatch vs freeze (plan drift)")
    violations.extend(validate_plan_summary_hash(tdir, freeze, require_summary_hash=require_summary_hash))
    return len(violations) == 0, violations


def _validate_user_check(obj: Any, task_id: str, module_id: str, *, require_checks: bool = True) -> List[str]:
    errors: List[str] = []
    if not isinstance(obj, dict):
        return [f"user-check proof is not an object for {task_id}"]
    if obj.get("task_id") != task_id:
        errors.append(f"user-check task_id mismatch: {obj.get('task_id')} != {task_id}")
    if obj.get("module") != slugify(module_id):
        errors.append(f"user-check module mismatch: {obj.get('module')} != {slugify(module_id)}")
    if not _is_str(obj.get("checked_utc")):
        errors.append("user-check missing checked_utc")
    if not _is_str(obj.get("checked_by")):
        errors.append("user-check missing checked_by")
    if obj.get("result") not in ("pass", "fail"):
        errors.append("user-check result must be pass|fail")
    if not _is_str(obj.get("notes")) or not obj.get("notes").strip():
        if require_checks:
            errors.append("user-check missing required notes")
    sha = obj.get("user_acceptance_sha256")
    if not _is_str(sha):
        errors.append("user-check missing user_acceptance_sha256")
    checks = obj.get("checks")
    if checks is not None and not _is_list_of_str(checks):
        errors.append("user-check checks must be list[str]")
    evidence = obj.get("evidence")
    if evidence is not None and not _is_str(evidence):
        errors.append("user-check evidence must be string")
    return errors


def _require_user_check_for_ready(tdir: Path, task_id: str, module_id: str, *, enforce_sha: bool = True) -> None:
    ua_path = tdir / "approvals" / "user-check.json"
    if not ua_path.exists():
        raise SystemExit("Missing user acceptance proof (approvals/user-check.json). Run record-user-check first.")
    uc = load_json(ua_path)
    errs = _validate_user_check(uc, task_id, module_id, require_checks=True)
    if errs:
        raise SystemExit("Invalid user-check proof: " + "; ".join(errs))
    if uc.get("result") != "pass":
        raise SystemExit(f"user-check failed with result={uc.get('result')}. Re-run with --result pass after remediation.")
    if enforce_sha:
        acceptance_path = tdir / "user_acceptance.md"
        if not acceptance_path.exists():
            raise SystemExit("Missing user_acceptance.md for SHA validation. Run freeze-plan or regen-user-acceptance.")
        if uc.get("user_acceptance_sha256") != sha256_file(acceptance_path):
            raise SystemExit("user-check SHA mismatch. Re-run record-user-check for the current user_acceptance.md.")


def _collect_ready_requirements(
    repo: Path,
    tdir: Path,
    module_root: Path,
    module_id: str,
    task_id: str,
) -> Dict[str, Any]:
    _require_sync_pack_migration_ready(repo)
    ok_freeze, freeze_viol = validate_freeze(tdir, require_summary_hash=True)
    if not ok_freeze:
        raise SystemExit("Plan freeze invalid: " + "; ".join(freeze_viol))

    if not (tdir / "approvals" / "plan.json").exists():
        raise SystemExit("Missing plan approval (approvals/plan.json).")

    proofs_dir = tdir / "run" / "proofs"
    scope_p = latest_proof(proofs_dir, "scope")
    verify_p = latest_proof(proofs_dir, "verify")
    review_p = latest_proof(proofs_dir, "review")
    if not scope_p:
        raise SystemExit("Missing scope proof. Run scope-check first.")
    if not verify_p:
        raise SystemExit("Missing verify proof. Run verify first.")
    if not review_p:
        raise SystemExit("Missing review proof. Record review first.")

    scope = load_json(scope_p)
    verify = load_json(verify_p)
    review = load_json(review_p)
    if not scope.get("overall_ok", False):
        raise SystemExit("Scope proof failed. Fix scope violations.")
    if not verify.get("overall_ok", False):
        raise SystemExit("Verify proof failed. Fix failing required gates.")
    if not review.get("ready", False):
        raise SystemExit(f"Review not ready (p0={review.get('p0')}, p1={review.get('p1')}).")

    toolchain = load_json(module_root / ".csk" / "toolchain.json")
    if not toolchain:
        raise SystemExit("Missing .csk/toolchain.json")
    e2e_req = toolchain.get("gates", {}).get("e2e", {}).get("required", False)
    if e2e_req:
        e2e_p = latest_proof(proofs_dir, "e2e")
        if not e2e_p:
            raise SystemExit("E2E required but no e2e proof found.")
        e2e = load_json(e2e_p)
        if not e2e.get("overall_ok", False):
            raise SystemExit("E2E proof failed.")

    _require_user_check_for_ready(tdir, task_id, module_id, enforce_sha=True)

    return {
        "scope_proof": str(scope_p.name),
        "verify_proof": str(verify_p.name),
        "review_proof": str(review_p.name),
        "e2e_required": bool(e2e_req),
        "user_check_proof": "user-check.json",
    }

def git_changed_files(repo: Path) -> List[str]:
    """
    Return repo-root relative changed files (including untracked).
    """
    def run_git(args: List[str]) -> List[str]:
        p = subprocess.run(["git"] + args, cwd=str(repo), capture_output=True, text=True)
        if p.returncode != 0:
            return []
        return [ln.strip() for ln in p.stdout.splitlines() if ln.strip()]

    # unstaged + staged
    changed = set(run_git(["diff", "--name-only"]))
    changed |= set(run_git(["diff", "--name-only", "--cached"]))

    # untracked/other via status porcelain
    p = subprocess.run(["git","status","--porcelain"], cwd=str(repo), capture_output=True, text=True)
    if p.returncode == 0:
        for line in p.stdout.splitlines():
            if not line:
                continue
            # format: XY <path>
            path = line[3:].strip()
            if path:
                changed.add(path)

    return sorted(changed)

def posix(path: str) -> str:
    return path.replace("\\", "/")

def glob_match(rel_posix: str, patterns: List[str]) -> bool:
    from pathlib import PurePosixPath
    p = PurePosixPath(rel_posix)
    for pat in patterns:
        pat = pat.strip()
        if not pat:
            continue
        # ensure module-relative patterns work regardless of subdir depth
        # Users can provide "**/file" explicitly; we don't auto-prefix.
        if p.match(pat):
            return True
    return False

def cmd_scope_check(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, module_root = task_paths(repo, args.module_id, args.task_id)

    ok_freeze, freeze_viol = validate_freeze(tdir, require_summary_hash=True)
    if not ok_freeze:
        raise SystemExit("Plan freeze invalid: " + "; ".join(freeze_viol))

    slices = load_json(tdir / "slices.json")
    slice_id = args.slice
    allowed: List[str] = []
    forbidden: List[str] = []
    if slice_id:
        s = next((x for x in slices.get("slices", []) if x.get("id") == slice_id), None)
        if not s:
            raise SystemExit(f"Unknown slice: {slice_id}")
        allowed = s.get("scope", {}).get("allowed_paths", []) or []
        forbidden = s.get("scope", {}).get("forbidden_paths", []) or []
    else:
        # union allowed across slices
        for s in slices.get("slices", []):
            allowed += (s.get("scope", {}).get("allowed_paths", []) or [])
            forbidden += (s.get("scope", {}).get("forbidden_paths", []) or [])
        allowed = sorted(set(allowed))
        forbidden = sorted(set(forbidden))

    if not allowed:
        raise SystemExit("No allowed_paths specified (P0). Fix plan/slices.")

    repo_rel_module = posix(str(module_root.relative_to(repo)))
    changed = git_changed_files(repo)

    changed_in_module: List[str] = []
    violations: List[str] = []

    for f in changed:
        fpos = posix(f)
        if repo_rel_module == ".":
            # module is repo root
            rel_to_module = fpos
        else:
            prefix = repo_rel_module.rstrip("/") + "/"
            if not fpos.startswith(prefix):
                violations.append(f"changed outside module root: {fpos}")
                continue
            rel_to_module = fpos[len(prefix):]
        changed_in_module.append(rel_to_module)

        if forbidden and glob_match(rel_to_module, forbidden):
            violations.append(f"forbidden path touched: {rel_to_module}")
            continue
        if not glob_match(rel_to_module, allowed):
            violations.append(f"not in allowed_paths: {rel_to_module}")

    overall_ok = len(violations) == 0

    proof = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "ran_utc": utc_now_iso(),
        "slice": slice_id,
        "overall_ok": overall_ok,
        "changed_files": changed_in_module,
        "violations": violations
    }
    out = tdir / "run" / "proofs" / f"scope-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    atomic_write_json(out, proof)
    print(f"[csk] scope-check overall_ok={overall_ok} proof={out}")
    if not overall_ok:
        sys.exit(1)

def run_cmd(cmd: List[str], cwd: Path, timeout_sec: int) -> Dict[str, Any]:
    started = utc_now_iso()
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout_sec)
        return {
            "cmd": cmd,
            "cwd": str(cwd),
            "started": started,
            "finished": utc_now_iso(),
            "exit": p.returncode,
            "stdout_tail": (p.stdout or "")[-4000:],
            "stderr_tail": (p.stderr or "")[-4000:]
        }
    except subprocess.TimeoutExpired as e:
        return {
            "cmd": cmd,
            "cwd": str(cwd),
            "started": started,
            "finished": utc_now_iso(),
            "exit": 124,
            "stdout_tail": (e.stdout or "")[-4000:],
            "stderr_tail": (e.stderr or "")[-4000:],
            "error": "timeout"
        }
    except FileNotFoundError as e:
        return {
            "cmd": cmd,
            "cwd": str(cwd),
            "started": started,
            "finished": utc_now_iso(),
            "exit": 127,
            "stdout_tail": "",
            "stderr_tail": str(e),
            "error": "command_not_found"
        }

def cmd_verify(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, module_root = task_paths(repo, args.module_id, args.task_id)

    ok_freeze, freeze_viol = validate_freeze(tdir, require_summary_hash=True)
    if not ok_freeze and not args.allow_unfrozen:
        raise SystemExit("Plan freeze invalid: " + "; ".join(freeze_viol))

    approvals = (tdir / "approvals" / "plan.json")
    if not approvals.exists() and not args.allow_unapproved:
        raise SystemExit("Plan not approved. Run approve-plan first (or pass --allow-unapproved).")

    toolchain = load_json(module_root / ".csk" / "toolchain.json", default=None)
    if not toolchain:
        raise SystemExit("Missing .csk/toolchain.json")

    gates = toolchain.get("gates", {})
    requested = [g.strip() for g in (args.gates.split(",") if args.gates else ["all"])]

    results = []
    overall_ok = True
    for gname, g in gates.items():
        if "all" not in requested and gname not in requested:
            continue
        if not g.get("required", False) and not args.include_optional:
            continue
        cmd = g.get("cmd", []) or []
        if not cmd:
            res = {"gate": gname, "required": g.get("required", False), "skipped": True, "reason": "no_cmd_configured"}
            results.append(res)
            if g.get("required", False):
                overall_ok = False
            continue
        timeout = int(g.get("timeout_sec", args.timeout_sec))
        res = run_cmd(cmd, cwd=module_root, timeout_sec=timeout)
        res["gate"] = gname
        res["required"] = g.get("required", False)
        results.append(res)
        if res.get("exit", 1) != 0 and g.get("required", False):
            overall_ok = False

    proof = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "ran_utc": utc_now_iso(),
        "overall_ok": overall_ok,
        "results": results
    }
    out = tdir / "run" / "proofs" / f"verify-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    atomic_write_json(out, proof)
    print(f"[csk] verify overall_ok={overall_ok} proof={out}")
    if not overall_ok:
        sys.exit(1)

def latest_proof(proofs_dir: Path, prefix: str) -> Optional[Path]:
    cands = sorted(proofs_dir.glob(f"{prefix}-*.json"))
    return cands[-1] if cands else None

def cmd_record_review(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, _ = task_paths(repo, args.module_id, args.task_id)
    proof = {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "ran_utc": utc_now_iso(),
        "p0": args.p0,
        "p1": args.p1,
        "p2": args.p2,
        "p3": args.p3,
        "summary": args.summary,
        "ready": (args.p0 == 0 and args.p1 == 0),
        "evidence": {}
    }
    out = tdir / "run" / "proofs" / f"review-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.json"
    atomic_write_json(out, proof)
    print(f"[csk] review recorded ready={proof['ready']} proof={out}")
    if not proof["ready"] and args.fail_on_blockers:
        sys.exit(1)

def cmd_validate_ready(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tdir, module_root = task_paths(repo, args.module_id, args.task_id)
    req = _collect_ready_requirements(repo, tdir, module_root, args.module_id, args.task_id)

    # write a ready report in run/
    out = tdir / "run" / "ready.json"
    atomic_write_json(out, {
        "task_id": args.task_id,
        "module": slugify(args.module_id),
        "validated_utc": utc_now_iso(),
        "scope_proof": req["scope_proof"],
        "verify_proof": req["verify_proof"],
        "review_proof": req["review_proof"],
        "e2e_required": bool(req["e2e_required"]),
        "user_check_proof": req["user_check_proof"],
    })
    print(f"[csk] READY VALIDATED ok. ready_report={out}")

def cmd_api_sync(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json")
    api_index = repo / ".csk-app" / "public_apis"
    api_index.mkdir(parents=True, exist_ok=True)

    # Copy each module PUBLIC_API.md into index
    for m in reg.get("modules", []):
        mid = m["id"]
        src = repo / m.get("public_api", f"{m['path']}/PUBLIC_API.md")
        if not src.exists():
            continue
        atomic_write_text(api_index / f"{mid}.md", src.read_text(encoding="utf-8"))

    # Sync index into each module `.csk/public_apis/` (full sync; can be narrowed later)
    for m in reg.get("modules", []):
        mroot = repo / m["path"]
        dst = mroot / ".csk" / "public_apis"
        if not dst.exists():
            continue
        for api in api_index.glob("*.md"):
            atomic_write_text(dst / api.name, api.read_text(encoding="utf-8"))

    print("[csk] api sync complete")

def cmd_status(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})
    lines = []
    lines.append(f"Project: {reg.get('project', {}).get('name', repo.name)}")
    lines.append(f"Modules: {len(reg.get('modules', []))}")
    for m in reg.get("modules", []):
        mid = m["id"]
        module_root = repo / m["path"]
        tasks_dir = module_root / ".csk" / "tasks"
        active = []
        if tasks_dir.exists():
            for t in sorted(tasks_dir.iterdir()):
                if not t.is_dir():
                    continue
                st = load_json(t / "run" / "status.json", default={})
                phase = st.get("phase")
                if phase and phase not in ("done",):
                    active.append(f"{t.name}:{phase}")
        lines.append(f"- {mid} ({m['path']}) active={', '.join(active) if active else 'none'}")
    print("\n".join(lines))

def cmd_incident(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    payload = {
        "ts": utc_now_iso(),
        "module": slugify(args.module_id) if args.module_id else None,
        "stage": args.stage,
        "severity": args.severity,
        "type": args.type,
        "summary": args.summary,
        "evidence": {"raw": args.evidence} if args.evidence else {},
        "proposed_fix": args.fix or [],
        "status": "open"
    }
    if args.module_id:
        m = get_module(repo, args.module_id)
        mroot = repo / m["path"]
        append_jsonl(mroot / ".csk" / "logs" / "incidents.jsonl", payload)
    else:
        append_jsonl(repo / ".csk-app" / "logs" / "incidents.jsonl", payload)
    print("[csk] incident logged")

def cmd_retro(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})

    def read_jsonl(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        out = []
        for ln in path.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out

    report_lines = []
    report_lines.append(f"# Retro report — {utc_now_iso()}\n")
    report_lines.append("## Principles\n- Convert incidents into concrete patches: env/toolchain/tests/rules.\n")

    app_inc = read_jsonl(repo / ".csk-app" / "logs" / "incidents.jsonl")
    if app_inc:
        report_lines.append("## App incidents (last 50)\n")
        for i in app_inc[-50:]:
            report_lines.append(f"- [{i.get('severity')}] {i.get('type')}: {i.get('summary')}")
        report_lines.append("")

    for m in reg.get("modules", []):
        mid = m["id"]
        mroot = repo / m["path"]
        inc = read_jsonl(mroot / ".csk" / "logs" / "incidents.jsonl")
        if not inc:
            continue
        report_lines.append(f"## Module `{mid}` incidents (last 50)\n")
        for i in inc[-50:]:
            report_lines.append(f"- [{i.get('severity')}] {i.get('type')}: {i.get('summary')}")
        report_lines.append("\n### Concrete patch checklist\n")
        report_lines.append("- [ ] Update Codex Local Environments setup/actions to prevent repeated env failures")
        report_lines.append("- [ ] Update toolchain.json to remove command ambiguity")
        report_lines.append("- [ ] Add regression tests for repeated defects")
        report_lines.append("- [ ] Tighten gates for risky areas (integration/e2e)")
        report_lines.append("- [ ] Consider adding/adjusting rules allowlist only if necessary\n")

    out_dir = repo / ".csk-app" / "run" / "retro"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"retro-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}.md"
    atomic_write_text(out, "\n".join(report_lines) + "\n")
    print(f"[csk] retro report written: {out}")


def cmd_retro_plan(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})
    module_filter = None
    if args.module_id:
        known = [str(m.get("id")) for m in reg.get("modules", []) if isinstance(m, dict) and m.get("id")]
        if args.module_id not in known:
            known_txt = ", ".join(known) if known else "<none>"
            raise SystemExit(f"Unknown module id for retro-plan: {args.module_id}. Known modules: {known_txt}")
        module_filter = args.module_id
    res = revo.create_retro_plan(
        repo=repo,
        modules=reg.get("modules", []),
        internet_research_mode=args.internet_research,
        top_candidates=max(1, int(args.top_candidates)),
        module_filter=module_filter,
    )
    print(f"[csk] retro-plan revision={res['revision_id']} root={res['revision_root']}")
    print(f"[csk] plan={res['plan_path']}")
    print(f"[csk] patchset={res['patchset_path']}")
    print(f"[csk] actions={res['actions_count']}")


def cmd_retro_approve(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    res = revo.approve_revision(
        repo=repo,
        revision_id=args.revision_id,
        approved_by=args.by or "user",
        note=args.note or "",
    )
    print(f"[csk] retro-approved revision={args.revision_id} approval={res['approval_path']}")


def cmd_retro_action_complete(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    res = revo.action_complete(
        repo=repo,
        revision_id=args.revision_id,
        action_id=args.action_id,
        evidence=args.evidence,
        waived=bool(args.waive),
    )
    print(f"[csk] retro-action updated action={args.action_id} status={res['status']}")


def cmd_retro_apply(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})
    validator = (lambda: _retro_validate_strict(repo)) if args.strict else None
    try:
        res = revo.apply_revision(
            repo=repo,
            modules=reg.get("modules", []),
            revision_id=args.revision_id,
            validate_fn=validator,
        )
    except RuntimeError as exc:
        msg = str(exc)
        if any(m in msg for m in ("overlay_hash_drift", "overlay_assets_hash_drift", "workflow_config_hash_drift")):
            _log_workflow_drift_incident(
                repo,
                f"retro-apply blocked for revision {args.revision_id} due to overlay drift.",
                evidence=msg,
            )
        raise SystemExit(f"retro-apply blocked: {msg}")
    print(f"[csk] retro-applied revision={args.revision_id} report={res['apply_report']}")
    print(f"[csk] operations={res['operations']}")


def cmd_retro_history(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    rows = revo.list_history(repo=repo, limit=max(1, int(args.limit)))
    if args.json:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
        return
    if not rows:
        print("[csk] retro-history empty")
        return
    print("[csk] retro-history")
    for row in rows:
        print(f"- {row.get('ts')} {row.get('event')} revision={row.get('revision_id')} success={row.get('success')}")


def cmd_retro_rollback(args: argparse.Namespace) -> None:
    revo = _require_retro_engine()
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    validator = (lambda: _retro_validate_strict(repo)) if args.strict else None
    try:
        res = revo.rollback_revision(
            repo=repo,
            revision_id=args.to,
            validate_fn=validator,
        )
    except RuntimeError as exc:
        raise SystemExit(f"retro-rollback blocked: {exc}")
    print(f"[csk] retro-rollback revision={args.to} restored_files={res['restored_files']}")


def cmd_toolchain_probe(args: argparse.Namespace) -> None:
    """
    Best-effort toolchain probe (no guessing):
    - Inspect canonical scripts (Makefile/package.json)
    - Run a minimal probe for candidate commands
    - Record probes in toolchain evidence
    """
    repo = find_repo_root(Path.cwd())
    m = get_module(repo, args.module_id)
    module_root = repo / m["path"]
    csk_dir = module_root / ".csk"
    toolchain_path = csk_dir / "toolchain.json"
    tc = load_json(toolchain_path, default=None)
    if not tc:
        tc = default_toolchain_for(detect_stack(module_root))

    evidence_files: List[str] = []
    probes: Dict[str, Any] = {}

    # Candidate commands from Makefile (common targets)
    makefile = module_root / "Makefile"
    if makefile.exists():
        evidence_files.append(str(makefile.relative_to(repo)).replace("\\","/"))
        # Try common targets; only keep if they succeed quickly
        candidates = [
            ("lint", ["make", "lint"]),
            ("unit", ["make", "test"]),
            ("unit", ["make", "unit"]),
            ("integration", ["make", "integration"]),
            ("e2e", ["make", "e2e"]),
            ("build", ["make", "build"]),
        ]
        for gate, cmd in candidates:
            r = run_cmd(cmd, cwd=module_root, timeout_sec=args.timeout_sec)
            probes[" ".join(cmd)] = {"exit": r["exit"], "seconds": None, "stdout_tail": r["stdout_tail"], "stderr_tail": r["stderr_tail"]}
            if r["exit"] == 0:
                if gate in tc["gates"]:
                    tc["gates"][gate]["cmd"] = cmd
                    tc["gates"][gate]["required"] = True if gate in ("lint","unit") else tc["gates"][gate]["required"]

    # Node: package.json scripts
    pkg = module_root / "package.json"
    if pkg.exists():
        evidence_files.append(str(pkg.relative_to(repo)).replace("\\","/"))
        try:
            pkgj = json.loads(pkg.read_text(encoding="utf-8"))
            scripts = pkgj.get("scripts") or {}
            # lockfile chooses pm (pnpm/yarn/npm)
            pm = "npm"
            if (module_root / "pnpm-lock.yaml").exists():
                pm = "pnpm"
                evidence_files.append(str((module_root/"pnpm-lock.yaml").relative_to(repo)).replace("\\","/"))
            elif (module_root / "yarn.lock").exists():
                pm = "yarn"
                evidence_files.append(str((module_root/"yarn.lock").relative_to(repo)).replace("\\","/"))
            elif (module_root / "package-lock.json").exists():
                evidence_files.append(str((module_root/"package-lock.json").relative_to(repo)).replace("\\","/"))

            # Install
            install_cmd = ["npm","ci"] if pm=="npm" else (["pnpm","install","--frozen-lockfile"] if pm=="pnpm" else ["yarn","install","--immutable"])
            r = run_cmd(install_cmd, cwd=module_root, timeout_sec=args.timeout_sec)
            probes[" ".join(install_cmd)] = {"exit": r["exit"], "stdout_tail": r["stdout_tail"], "stderr_tail": r["stderr_tail"]}
            if r["exit"] == 0:
                tc["gates"]["install"]["cmd"] = install_cmd
                tc["gates"]["install"]["required"] = True

            def run_script(name: str) -> Optional[List[str]]:
                if name not in scripts:
                    return None
                cmd = [pm, name] if pm != "npm" else ["npm","run",name]
                r = run_cmd(cmd, cwd=module_root, timeout_sec=args.timeout_sec)
                probes[" ".join(cmd)] = {"exit": r["exit"], "stdout_tail": r["stdout_tail"], "stderr_tail": r["stderr_tail"]}
                return cmd if r["exit"]==0 else None

            lint_cmd = run_script("lint") or run_script("check") or None
            if lint_cmd:
                tc["gates"]["lint"]["cmd"] = lint_cmd
                tc["gates"]["lint"]["required"] = True

            test_cmd = run_script("test") or run_script("unit") or None
            if test_cmd:
                tc["gates"]["unit"]["cmd"] = test_cmd
                tc["gates"]["unit"]["required"] = True
        except Exception as e:
            probes["package.json parse"] = {"exit": 1, "error": str(e)}

    # Python: pytest/ruff
    if (module_root / "pyproject.toml").exists() or (module_root / "requirements.txt").exists():
        evidence_files.append(str((module_root/"pyproject.toml").relative_to(repo)).replace("\\","/") if (module_root/"pyproject.toml").exists() else "")
        # Basic probe: python -m pytest, python -m ruff check .
        for gate, cmd in [
            ("lint", ["python","-m","ruff","check","."]),
            ("unit", ["python","-m","pytest","-q"]),
        ]:
            r = run_cmd(cmd, cwd=module_root, timeout_sec=args.timeout_sec)
            probes[" ".join(cmd)] = {"exit": r["exit"], "stdout_tail": r["stdout_tail"], "stderr_tail": r["stderr_tail"]}
            if r["exit"]==0:
                tc["gates"][gate]["cmd"] = cmd
                tc["gates"][gate]["required"] = True

    tc.setdefault("evidence", {})
    tc["evidence"]["files"] = sorted([f for f in evidence_files if f])
    tc["evidence"]["probes"] = probes
    atomic_write_json(toolchain_path, tc)
    print(f"[csk] toolchain probe updated: {toolchain_path}")

def derive_root_from_glob(glob_pat: str) -> Optional[str]:
    # crude: take substring before first wildcard
    pat = glob_pat.replace("\\","/")
    for token in ["**", "*", "?", "["]:
        idx = pat.find(token)
        if idx != -1:
            pat = pat[:idx]
            break
    pat = pat.rstrip("/")
    return pat or None

def cmd_backlog_add(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    ensure_app_skeleton(repo)
    entry = {
        "id": args.id or f"B-{_dt.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}-{slugify(args.title)[:20]}",
        "created_utc": utc_now_iso(),
        "module": slugify(args.module_id) if args.module_id else None,
        "type": args.type,
        "title": args.title,
        "status": args.status,
        "links": {"research": args.research or None, "task": args.task or None},
        "notes": args.notes or "",
        "priority": args.priority
    }
    if args.module_id:
        m = get_module(repo, args.module_id)
        mroot = repo / m["path"]
        append_jsonl(mroot / ".csk" / "backlog.jsonl", entry)
    else:
        append_jsonl(repo / ".csk-app" / "backlog.jsonl", entry)
    print(f"[csk] backlog added {entry['id']}")

def cmd_research_new(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    title_slug = slugify(args.title)[:30]
    rid = f"R-{_dt.datetime.utcnow().strftime('%Y%m%d')}-{title_slug}"
    if args.module_id:
        m = get_module(repo, args.module_id)
        mroot = repo / m["path"]
        rdir = mroot / ".csk" / "research"
    else:
        rdir = repo / ".csk-app" / "research"
    rdir.mkdir(parents=True, exist_ok=True)
    path = rdir / f"{rid}.md"
    if path.exists():
        print(f"[csk] research exists: {path}")
        return
    atomic_write_text(path, f"# Research {rid}\n\n## Question\n{args.title}\n\n## Findings\n- \n\n## Evidence\n- \n\n## Candidate backlog items\n- \n")
    print(f"[csk] research created: {path}")


# -------------------------
# Validation (schemas wrapper)
# -------------------------

def _is_str(x: Any) -> bool:
    return isinstance(x, str)

def _is_bool(x: Any) -> bool:
    return isinstance(x, bool)

def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)

def _is_list_of_str(x: Any) -> bool:
    return isinstance(x, list) and all(isinstance(i, str) for i in x)

def _try_jsonschema():
    try:
        import jsonschema  # type: ignore
        return jsonschema
    except Exception:
        return None

def _load_schema(repo: Path, filename: str) -> Optional[Dict[str, Any]]:
    p = repo / "schemas" / filename
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _validate_with_jsonschema(instance: Any, schema: Dict[str, Any]) -> List[str]:
    js = _try_jsonschema()
    if not js:
        return []
    try:
        js.validate(instance=instance, schema=schema)
        return []
    except Exception as e:
        return [str(e)]

def _validate_registry_obj(obj: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(obj, dict):
        return ["registry is not an object"], []
    if obj.get("schema_version") != 2:
        errors.append("registry.schema_version must be 2")
    proj = obj.get("project")
    if not isinstance(proj, dict):
        errors.append("registry.project missing or not object")
    else:
        if not _is_str(proj.get("name")):
            errors.append("registry.project.name missing or not string")
        if not _is_str(proj.get("created_utc")):
            errors.append("registry.project.created_utc missing or not string")
    modules = obj.get("modules")
    if not isinstance(modules, list):
        errors.append("registry.modules missing or not list")
        modules = []
    seen = set()
    for i, m in enumerate(modules):
        if not isinstance(m, dict):
            errors.append(f"registry.modules[{i}] not object")
            continue
        mid = m.get("id")
        if not _is_str(mid):
            errors.append(f"registry.modules[{i}].id missing or not string")
            continue
        if mid in seen:
            errors.append(f"duplicate module id: {mid}")
        seen.add(mid)
        for k in ["path", "public_api", "status"]:
            if not _is_str(m.get(k)):
                errors.append(f"module {mid}: missing or non-string {k}")
        if m.get("status") not in ("active", "archived"):
            errors.append(f"module {mid}: invalid status {m.get('status')}")
    if not _is_str(obj.get("public_api_index")):
        errors.append("registry.public_api_index missing or not string")
    if obj.get("backlog") is not None and not _is_str(obj.get("backlog")):
        errors.append("registry.backlog must be string if present")
    return errors, warnings

def _validate_toolchain_obj(obj: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(obj, dict):
        return ["toolchain is not an object"], []
    if obj.get("schema_version") != 1:
        errors.append("toolchain.schema_version must be 1")
    if not _is_str(obj.get("profile")):
        errors.append("toolchain.profile missing or not string")
    gates = obj.get("gates")
    if not isinstance(gates, dict):
        errors.append("toolchain.gates missing or not object")
        return errors, warnings
    for gname, g in gates.items():
        if not isinstance(g, dict):
            errors.append(f"gate {gname} not object")
            continue
        if "required" not in g or not _is_bool(g.get("required")):
            errors.append(f"gate {gname}.required missing or not bool")
        cmd = g.get("cmd")
        if cmd is None:
            errors.append(f"gate {gname}.cmd missing")
        elif not _is_list_of_str(cmd):
            errors.append(f"gate {gname}.cmd must be list[str]")
        else:
            if g.get("required") is True and len(cmd) == 0:
                errors.append(f"gate {gname} is required but cmd is empty")
        if "timeout_sec" in g and not _is_int(g.get("timeout_sec")):
            errors.append(f"gate {gname}.timeout_sec must be int")
    return errors, warnings

def _validate_slices_obj(obj: Any) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not isinstance(obj, dict):
        return ["slices.json is not an object"], []
    if obj.get("schema_version") != 2:
        errors.append("slices.schema_version must be 2")
    if not _is_str(obj.get("task_id")):
        errors.append("slices.task_id missing or not string")
    if not _is_str(obj.get("module")):
        errors.append("slices.module missing or not string")
    sl = obj.get("slices")
    if not isinstance(sl, list) or not sl:
        errors.append("slices.slices missing or empty list")
        return errors, warnings
    seen = set()
    for i, s in enumerate(sl):
        if not isinstance(s, dict):
            errors.append(f"slices[{i}] not object")
            continue
        sid = s.get("id")
        if not _is_str(sid):
            errors.append(f"slices[{i}].id missing or not string")
            continue
        if sid in seen:
            errors.append(f"duplicate slice id: {sid}")
        seen.add(sid)
        if not _is_str(s.get("title")):
            warnings.append(f"slice {sid}: title missing or not string")
        scope = s.get("scope")
        if not isinstance(scope, dict):
            errors.append(f"slice {sid}: scope missing or not object")
            continue
        allowed = scope.get("allowed_paths")
        forbidden = scope.get("forbidden_paths")
        if not _is_list_of_str(allowed) or len(allowed) == 0:
            errors.append(f"slice {sid}: scope.allowed_paths missing/empty or not list[str]")
        if forbidden is not None and not _is_list_of_str(forbidden):
            errors.append(f"slice {sid}: scope.forbidden_paths must be list[str]")
        req = s.get("required_gates")
        if not _is_list_of_str(req) or len(req) == 0:
            errors.append(f"slice {sid}: required_gates missing/empty or not list[str]")
    return errors, warnings

def _validate_jsonl(path: Path, required_keys: List[str], enums: Dict[str, List[str]] = {}) -> Tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    if not path.exists():
        return errors, warnings
    for idx, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception as e:
            errors.append(f"{path}: line {idx} invalid json: {e}")
            continue
        if not isinstance(obj, dict):
            errors.append(f"{path}: line {idx} is not object")
            continue
        for k in required_keys:
            if k not in obj:
                errors.append(f"{path}: line {idx} missing key {k}")
        for k, allowed in enums.items():
            if k in obj and obj.get(k) not in allowed:
                errors.append(f"{path}: line {idx} invalid {k}={obj.get(k)}")
    return errors, warnings


def _parse_version_str(value: str) -> tuple[int, ...]:
    nums = [int(x) for x in re.findall(r"\d+", value)]
    return tuple(nums) if nums else (0,)


def _version_cmp(a: str, b: str) -> int:
    pa = _parse_version_str(a)
    pb = _parse_version_str(b)
    if pa == pb:
        return 0
    return 1 if pa > pb else -1


def _validate_sync_pack_migration(repo: Path, strict: bool) -> tuple[List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []

    manifest_path = repo / "tools/csk" / "upstream_sync_manifest.json"
    state_path = repo / ".csk-app" / "sync" / "state.json"
    if not manifest_path.exists():
        warnings.append("missing tools/csk/upstream_sync_manifest.json; migration-state validation skipped.")
        return errors, warnings

    manifest = load_json(manifest_path, default={})
    manifest_pack = manifest.get("pack_version")
    if not isinstance(manifest_pack, str) or not manifest_pack.strip():
        warnings.append("upstream_sync_manifest.json missing pack_version; migration strict checks unavailable.")
        return errors, warnings

    state = load_json(state_path, default={})
    state_pack = state.get("current_pack_version")
    if not isinstance(state_pack, str) or not state_pack.strip():
        msg = "sync state missing current_pack_version; run sync_upstream plan/apply after migration update."
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
        return errors, warnings

    if _version_cmp(manifest_pack, state_pack) <= 0:
        return errors, warnings

    if not state.get("migration_pending", False):
        msg = (
            f"sync pack is behind manifest: state={state_pack}, manifest={manifest_pack}, "
            "migration_pending=false but upgrade exists."
        )
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
        return errors, warnings

    migration_file = state.get("last_migration_file")
    if not isinstance(migration_file, str) or not migration_file.strip():
        msg = "state indicates pending migration but no migration report path."
        warnings.append(msg if not strict else f"{msg} Run migration-status then migration-ack.")
        return errors, warnings

    migration_path = Path(migration_file)
    if not migration_path.exists():
        msg = f"migration file missing on disk: {migration_path}"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
        return errors, warnings

    migration_ack = Path(str(migration_path) + ".ack.json")
    if not migration_ack.exists():
        msg = (
            f"migration report is unacknowledged: {migration_path}. "
            f"Run migration-ack --migration-file {migration_path}"
        )
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)
    return errors, warnings


def _require_sync_pack_migration_ready(repo: Path) -> None:
    manifest_path = repo / "tools" / "csk" / "upstream_sync_manifest.json"
    if not manifest_path.exists():
        return

    errors, warnings = _validate_sync_pack_migration(repo, strict=True)
    issues: List[str] = []
    issues.extend(errors)
    issues.extend(warnings)
    if issues:
        raise SystemExit(
            "CSK workflow pack migration is required before READY. "
            "Run `python tools/csk/sync_upstream.py migration-status --migration-strict` "
            "and acknowledge with migration-ack. "
            + "; ".join(issues)
        )

def cmd_validate(args: argparse.Namespace) -> None:
    """
    Validate CSK contracts in-repo. Intended to catch manual edits early.

    If jsonschema is installed, this command will also validate against the JSON Schema files under /schemas.
    Otherwise it runs a strict built-in structural validation.
    """
    repo = find_repo_root(Path.cwd())
    errors: List[str] = []
    warnings: List[str] = []

    reg_path = repo / ".csk-app" / "registry.json"
    if not reg_path.exists():
        raise SystemExit("Missing .csk-app/registry.json (not a CSK repo).")
    reg = load_json(reg_path)

    # registry validation
    schema = _load_schema(repo, "registry.schema.json")
    if schema:
        errors += _validate_with_jsonschema(reg, schema)
    e, w = _validate_registry_obj(reg)
    errors += e; warnings += w

    # logs
    if args.logs or args.all:
        e, w = _validate_jsonl(repo/".csk-app"/"logs"/"incidents.jsonl",
                               required_keys=["ts","stage","severity","type","summary","status"],
                               enums={"severity":["P0","P1","P2","P3"], "status":["open","fixed","wontfix"]})
        errors += e; warnings += w
        e, w = _validate_jsonl(repo/".csk-app"/"logs"/"decisions.jsonl",
                               required_keys=["ts","scope","decision","recommended"])
        errors += e; warnings += w
        e, w = _validate_jsonl(repo/".csk-app"/"backlog.jsonl",
                               required_keys=["id","created_utc","title","status"])
        errors += e; warnings += w

    e, w = _validate_sync_pack_migration(repo, args.strict)
    errors += e
    warnings += w

    # module validation
    modules = reg.get("modules") or []
    module_filter = slugify(args.module_id) if args.module_id else None

    for m in modules:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if not mid or (module_filter and mid != module_filter):
            continue
        mroot = repo / m.get("path", "")
        if not mroot.exists():
            errors.append(f"module {mid}: path does not exist: {m.get('path')}")
            continue

        # module logs
        if args.logs or args.all:
            e, w = _validate_jsonl(mroot/".csk"/"logs"/"incidents.jsonl",
                                   required_keys=["ts","stage","severity","type","summary","status"],
                                   enums={"severity":["P0","P1","P2","P3"], "status":["open","fixed","wontfix"]})
            errors += e; warnings += w
            e, w = _validate_jsonl(mroot/".csk"/"logs"/"decisions.jsonl",
                                   required_keys=["ts","scope","decision","recommended"])
            errors += e; warnings += w

        # toolchain
        tc_path = mroot/".csk"/"toolchain.json"
        if not tc_path.exists():
            errors.append(f"module {mid}: missing .csk/toolchain.json")
        else:
            tc = load_json(tc_path)
            schema = _load_schema(repo, "toolchain.schema.json")
            if schema:
                errors += _validate_with_jsonschema(tc, schema)
            e, w = _validate_toolchain_obj(tc)
            errors += e; warnings += w

        # tasks
        tasks_dir = mroot/".csk"/"tasks"
        if not tasks_dir.exists():
            continue
        for tdir in sorted(tasks_dir.iterdir()):
            if not tdir.is_dir() or not tdir.name.startswith("T-"):
                continue
            if args.task_id and tdir.name != args.task_id:
                continue

            plan_path = tdir/"plan.md"
            slices_path = tdir/"slices.json"
            if not plan_path.exists():
                errors.append(f"{mid}/{tdir.name}: missing plan.md")
            if not slices_path.exists():
                errors.append(f"{mid}/{tdir.name}: missing slices.json")
                continue

            slices_obj = load_json(slices_path)
            schema = _load_schema(repo, "slices.schema.json")
            if schema:
                errors += _validate_with_jsonschema(slices_obj, schema)
            e, w = _validate_slices_obj(slices_obj)
            errors += e; warnings += w
            # slices.module should match module id
            if isinstance(slices_obj, dict) and slices_obj.get("module") and slices_obj.get("module") != mid:
                errors.append(f"{mid}/{tdir.name}: slices.json module mismatch ({slices_obj.get('module')} != {mid})")

            # freeze validation if exists
            freeze_path = tdir/"plan.freeze.json"
            if freeze_path.exists():
                ok, viol = validate_freeze(tdir)
                if not ok:
                    errors.append(f"{mid}/{tdir.name}: freeze invalid: " + "; ".join(viol))
            else:
                warnings.append(f"{mid}/{tdir.name}: no plan.freeze.json (task may be in planning)")

            # plan summary artifact (new file in this pack)
            summary_path = tdir/"plan.summary.md"
            if not summary_path.exists():
                if args.strict:
                    errors.append(f"{mid}/{tdir.name}: missing plan.summary.md (required by current workflow)")
                else:
                    warnings.append(f"{mid}/{tdir.name}: missing plan.summary.md (required in current workflow)")
            elif freeze_path.exists():
                freeze_obj = load_json(freeze_path, default={})
                if "plan_summary_sha256" not in freeze_obj:
                    msg = f"{mid}/{tdir.name}: plan.freeze.json missing plan_summary_sha256"
                    if args.strict:
                        errors.append(msg)
                    else:
                        warnings.append(msg)

            # user acceptance artifact (required for manual checks)
            user_acceptance_path = tdir / "user_acceptance.md"
            if not user_acceptance_path.exists():
                if args.strict:
                    errors.append(f"{mid}/{tdir.name}: missing user_acceptance.md (required by current workflow)")
                else:
                    warnings.append(f"{mid}/{tdir.name}: missing user_acceptance.md (required in current workflow)")

            # user-check proof
            user_check_path = tdir / "approvals" / "user-check.json"
            if user_check_path.exists():
                user_check = load_json(user_check_path)
                schema = _load_schema(repo, "user_check.schema.json")
                if schema:
                    errors += _validate_with_jsonschema(user_check, schema)
                e, w = _validate_user_check(user_check, tdir.name, mid, require_checks=False)
                errors += e
                warnings += w
                if user_acceptance_path.exists() and user_check.get("user_acceptance_sha256"):
                    try:
                        if user_check.get("user_acceptance_sha256") != sha256_file(user_acceptance_path):
                            warnings.append(f"{mid}/{tdir.name}: user-check proof hash mismatch (user_acceptance.md changed after recording)")
                    except Exception:
                        warnings.append(f"{mid}/{tdir.name}: failed to validate user-check hash drift")
            elif freeze_path.exists():
                msg = f"{mid}/{tdir.name}: task frozen but user-check proof missing (approvals/user-check.json)"
                if args.strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)

            # approvals sanity
            appr_plan = tdir/"approvals"/"plan.json"
            if freeze_path.exists() and not appr_plan.exists():
                warnings.append(f"{mid}/{tdir.name}: plan frozen but not approved (approvals/plan.json missing)")

    # workflow overlay evolution contracts
    infos: List[str] = []
    try:
        revo = _require_retro_engine()
        mids = [str(m.get("id")) for m in modules if isinstance(m, dict) and m.get("id")]
        e, w, i = revo.validate_contracts(repo, mids)
        errors += e
        warnings += w
        infos += i
    except SystemExit as e:
        warnings.append(str(e))

    # strict mode: upgrade warnings to errors (infos remain advisory)
    if args.strict and warnings:
        errors += [f"(as error) {w}" for w in warnings]
        warnings = []

    # output
    if args.json:
        out = {"ok": len(errors) == 0, "errors": errors, "warnings": warnings, "infos": infos}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if errors:
            print("CSK VALIDATE: FAIL")
            for e in errors:
                print(f"- ERROR: {e}")
        if warnings:
            print("CSK VALIDATE: WARN")
            for w in warnings:
                print(f"- WARN: {w}")
        if infos:
            print("CSK VALIDATE: INFO")
            for msg in infos:
                print(f"- INFO: {msg}")
        if not errors and not warnings and not infos:
            print("CSK VALIDATE: OK")

    if errors:
        sys.exit(1)


def _iter_reconcilable_tasks(
    repo: Path,
    module_id: Optional[str] = None,
    task_id: Optional[str] = None,
) -> list[tuple[str, Path]]:
    reg = load_json(repo / ".csk-app" / "registry.json", default={"modules": []})
    modules = reg.get("modules", [])
    if not isinstance(modules, list):
        modules = []
    if module_id:
        target_module = get_module(repo, module_id)
        modules = [target_module] if target_module else []

    out: list[tuple[str, Path]] = []
    for m in modules:
        if not isinstance(m, dict):
            continue
        mid = m.get("id")
        if not isinstance(mid, str):
            continue
        mroot = repo / m.get("path", "")
        if not mroot.exists():
            continue
        tasks_dir = mroot / ".csk" / "tasks"
        if not tasks_dir.exists():
            continue
        for tdir in sorted(tasks_dir.iterdir()):
            if not tdir.is_dir() or not tdir.name.startswith("T-"):
                continue
            if task_id and tdir.name != task_id:
                continue
            out.append((mid, tdir))
    return out


def cmd_reconcile_task_artifacts(args: argparse.Namespace) -> None:
    repo = find_repo_root(Path.cwd())
    tasks = _iter_reconcilable_tasks(repo, args.module_id, args.task_id)
    if not tasks:
        raise SystemExit("No matching tasks found for artifact reconciliation.")

    report = {
        "updated": 0,
        "missing_plan": 0,
        "errors": 0,
        "items": [],
    }

    for mid, tdir in tasks:
        item: dict[str, Any] = {"module": mid, "task": tdir.name}
        plan_path = tdir / "plan.md"
        if not plan_path.exists():
            report["missing_plan"] += 1
            item["status"] = "missing_plan"
            item["error"] = "plan.md missing"
            report["items"].append(item)
            continue

        title = task_title(tdir, tdir.name)
        try:
            sync_plan_summary(
                repo,
                plan_path,
                tdir / "plan.summary.md",
                mid,
                tdir.name,
                title,
                require_block=bool(args.require_block),
            )
            sync_user_acceptance(
                repo,
                plan_path,
                tdir / "user_acceptance.md",
                mid,
                tdir.name,
                title,
                require_block=bool(args.require_block),
            )
            report["updated"] += 1
            item["status"] = "updated"
        except SystemExit as e:
            report["errors"] += 1
            item["status"] = "error"
            item["error"] = str(e)
        report["items"].append(item)

    if args.json:
        report["status"] = "ok" if report["errors"] == 0 else "failed"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if report["errors"] and args.strict:
            raise SystemExit("reconcile-task-artifacts failed.")
        return

    print(
        f"[csk] reconcile-task-artifacts updated={report['updated']} "
        f"missing_plan={report['missing_plan']} errors={report['errors']}"
    )
    if report["errors"]:
        for item in report["items"]:
            if item.get("status") == "error":
                print(f"[csk] {item['module']}/{item['task']}: {item.get('error')}")
        if args.strict:
            raise SystemExit("reconcile-task-artifacts failed.")
    print(f"[csk] reconcile-task-artifacts completed for {len(report['items'])} tasks.")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="csk", description="CSK‑M Pro v4 helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("bootstrap")
    sp.add_argument("--apply-candidates", action="store_true")
    sp.set_defaults(fn=cmd_bootstrap)

    sp = sub.add_parser("add-module")
    sp.add_argument("module_id")
    sp.add_argument("path")
    sp.set_defaults(fn=cmd_add_module)

    sp = sub.add_parser("new-task")
    sp.add_argument("module_or_title")
    sp.add_argument("title", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.set_defaults(fn=cmd_new_task, module_mode="module_title")

    sp = sub.add_parser("freeze-plan")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.set_defaults(fn=cmd_freeze_plan, module_mode="module_task")

    sp = sub.add_parser("approve-plan")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--by", default="user")
    sp.add_argument("--note", default="")
    sp.set_defaults(fn=cmd_approve_plan, module_mode="module_task")

    sp = sub.add_parser("approve-ready")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--by", default="user")
    sp.add_argument("--note", default="")
    sp.set_defaults(fn=cmd_approve_ready, module_mode="module_task")

    sp = sub.add_parser("regen-plan-summary")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.set_defaults(fn=cmd_regen_plan_summary, module_mode="module_task")

    sp = sub.add_parser("regen-user-acceptance")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--require-block", action="store_true")
    sp.set_defaults(fn=cmd_regen_user_acceptance, module_mode="module_task")

    sp = sub.add_parser("reconcile-task-artifacts")
    sp.add_argument("--module-id", default=None, help="Limit to one module.")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--require-block", action="store_true", help="Fail if marker blocks are missing in plan.md.")
    sp.add_argument("--strict", action="store_true", help="Return non-zero if any task has missing blocks.")
    sp.add_argument("--json", action="store_true", help="Output JSON report.")
    sp.set_defaults(fn=cmd_reconcile_task_artifacts)

    sp = sub.add_parser("scope-check")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--slice", default=None)
    sp.set_defaults(fn=cmd_scope_check, module_mode="module_task")

    sp = sub.add_parser("verify")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--gates", default="all")
    sp.add_argument("--include-optional", action="store_true")
    sp.add_argument("--timeout-sec", type=int, default=1800)
    sp.add_argument("--allow-unfrozen", action="store_true")
    sp.add_argument("--allow-unapproved", action="store_true")
    sp.set_defaults(fn=cmd_verify, module_mode="module_task")

    sp = sub.add_parser("record-review")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--p0", type=int, default=0)
    sp.add_argument("--p1", type=int, default=0)
    sp.add_argument("--p2", type=int, default=0)
    sp.add_argument("--p3", type=int, default=0)
    sp.add_argument("--summary", required=True)
    sp.add_argument("--fail-on-blockers", action="store_true")
    sp.set_defaults(fn=cmd_record_review, module_mode="module_task")

    sp = sub.add_parser("record-user-check")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--result", required=True, choices=["pass", "fail"])
    sp.add_argument("--notes", required=True)
    sp.add_argument("--checks", nargs="+")
    sp.add_argument("--evidence", default="")
    sp.add_argument("--tested-by", default="user")
    sp.set_defaults(fn=cmd_record_user_check, module_mode="module_task")

    sp = sub.add_parser("validate-ready")
    sp.add_argument("module_or_task_id")
    sp.add_argument("task_id", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.set_defaults(fn=cmd_validate_ready, module_mode="module_task")

    sp = sub.add_parser("status")
    sp.set_defaults(fn=cmd_status)

    sp = sub.add_parser("api-sync")
    sp.set_defaults(fn=cmd_api_sync)

    sp = sub.add_parser("incident")
    sp.add_argument("--module-id", default=None)
    sp.add_argument("--stage", required=True)
    sp.add_argument("--severity", required=True, choices=["P0","P1","P2","P3"])
    sp.add_argument("--type", required=True)
    sp.add_argument("--summary", required=True)
    sp.add_argument("--evidence", default="")
    sp.add_argument("--fix", action="append", default=[])
    sp.set_defaults(fn=cmd_incident)

    sp = sub.add_parser("retro")
    sp.set_defaults(fn=cmd_retro)

    sp = sub.add_parser("retro-plan")
    sp.add_argument("--module-id", default=None)
    sp.add_argument("--internet-research", default="auto", choices=["auto", "off"])
    sp.add_argument("--top-candidates", type=int, default=5)
    sp.set_defaults(fn=cmd_retro_plan)

    sp = sub.add_parser("retro-approve")
    sp.add_argument("revision_id")
    sp.add_argument("--by", default="user")
    sp.add_argument("--note", default="")
    sp.set_defaults(fn=cmd_retro_approve)

    sp = sub.add_parser("retro-action-complete")
    sp.add_argument("revision_id")
    sp.add_argument("action_id")
    sp.add_argument("--evidence", required=True)
    sp.add_argument("--waive", action="store_true")
    sp.set_defaults(fn=cmd_retro_action_complete)

    sp = sub.add_parser("retro-apply")
    sp.add_argument("revision_id")
    sp.add_argument("--strict", action="store_true")
    sp.set_defaults(fn=cmd_retro_apply)

    sp = sub.add_parser("retro-history")
    sp.add_argument("--limit", type=int, default=20)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(fn=cmd_retro_history)

    sp = sub.add_parser("retro-rollback")
    sp.add_argument("--to", required=True)
    sp.add_argument("--strict", action="store_true")
    sp.set_defaults(fn=cmd_retro_rollback)

    sp = sub.add_parser("toolchain-probe")
    sp.add_argument("module_id_arg", nargs="?")
    sp.add_argument("--module-id", default=None, dest="module_id", help="Explicit module id override.")
    sp.add_argument("--timeout-sec", type=int, default=600)
    sp.set_defaults(fn=cmd_toolchain_probe, module_mode="module_only")


    sp = sub.add_parser("validate", help="Validate CSK contracts and logs (schemas wrapper).")
    sp.add_argument("--all", action="store_true", help="Validate everything (default).")
    sp.add_argument("--module-id", default=None, help="Validate only one module.")
    sp.add_argument("--task-id", default=None, help="Validate only one task id (requires module scope if ambiguous).")
    sp.add_argument("--logs", action="store_true", help="Validate incidents/decisions/backlog jsonl logs.")
    sp.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    sp.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    sp.set_defaults(fn=cmd_validate)

    sp = sub.add_parser("backlog-add")
    sp.add_argument("--module-id", default=None)
    sp.add_argument("--id", default=None)
    sp.add_argument("--type", default="research-followup")
    sp.add_argument("--title", required=True)
    sp.add_argument("--status", default="deferred", choices=["deferred","queued","active","done","wontfix"])
    sp.add_argument("--research", default=None)
    sp.add_argument("--task", default=None)
    sp.add_argument("--notes", default="")
    sp.add_argument("--priority", default="P2", choices=["P0","P1","P2","P3"])
    sp.set_defaults(fn=cmd_backlog_add)

    sp = sub.add_parser("research-new")
    sp.add_argument("--module-id", default=None)
    sp.add_argument("--title", required=True)
    sp.set_defaults(fn=cmd_research_new)

    args = p.parse_args(argv)
    repo = find_repo_root(Path.cwd())
    cwd = Path.cwd()
    if getattr(args, "module_mode", None) == "module_task":
        _normalize_module_task_args(args, repo, cwd)
    elif getattr(args, "module_mode", None) == "module_title":
        _normalize_module_title_args(args, repo, cwd)
    elif getattr(args, "module_mode", None) == "module_only":
        _normalize_module_only_args(args, repo, cwd)
    _enforce_overlay_guard_for_command(repo, args.cmd)
    args.fn(args)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
