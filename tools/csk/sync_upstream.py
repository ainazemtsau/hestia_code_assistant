from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import shutil
import subprocess
import sys
import tempfile
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_URL = "https://github.com/ainazemtsau/hestia_code_assistant"
DEFAULT_SOURCE_REF = "main"
DEFAULT_MANIFEST = "tools/csk/upstream_sync_manifest.json"
DEFAULT_OVERLAY_ROOT = ".csk-app/overlay"
DEFAULT_STATE_FILE = ".csk-app/sync/state.json"
DEFAULT_MIGRATION_DIR = ".csk-app/sync/migrations"
DEFAULT_CONFIDENCE_THRESHOLD = 0.75
DEFAULT_TOP_CANDIDATES = 5
MERGE_MODES = {"replace_core", "overlay_allowed", "manual_only"}


@dataclass(frozen=True)
class SyncItem:
    path: str
    required: bool = True
    merge_mode: str = "overlay_allowed"


class SyncError(RuntimeError):
    pass


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_rel(path: str) -> Path:
    rel = Path(path)
    if rel.is_absolute():
        raise SyncError(f"Manifest path must be relative: {path}")
    if ".." in rel.parts:
        raise SyncError(f"Manifest path cannot contain '..': {path}")
    return rel


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SyncError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_json_optional(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=True) + "\n")


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_tree(path: Path) -> str:
    h = hashlib.sha256()
    for child in sorted(path.rglob("*")):
        rel = child.relative_to(path).as_posix()
        if child.is_dir():
            h.update(f"D:{rel}\n".encode("utf-8"))
            continue
        if child.is_file():
            h.update(f"F:{rel}:".encode("utf-8"))
            h.update(_hash_file(child).encode("ascii"))
            h.update(b"\n")
    return h.hexdigest()


def _path_hash(path: Path) -> str | None:
    if not path.exists():
        return None
    if path.is_file():
        return f"file:{_hash_file(path)}"
    if path.is_dir():
        return f"dir:{_hash_tree(path)}"
    return None


def _manifest_hash(path: Path) -> str:
    return _hash_bytes(path.read_bytes())


def _parse_pack_version(raw: Any) -> tuple[int, ...]:
    if not isinstance(raw, str):
        return (0,)
    nums = [int(x) for x in re.findall(r"\d+", raw)]
    return tuple(nums) if nums else (0,)


def _version_cmp(a: str, b: str) -> int:
    ta = _parse_pack_version(a)
    tb = _parse_pack_version(b)
    if ta == tb:
        return 0
    return 1 if ta > tb else -1


def _load_manifest_payload(path: Path) -> dict[str, Any]:
    return _load_json(path)


def _manifest_pack_version(manifest: dict[str, Any]) -> str:
    value = manifest.get("pack_version")
    if not isinstance(value, str) or not value.strip():
        return "0.0.0"
    return value.strip()


def _extract_migration_steps(manifest: dict[str, Any], from_version: str, to_version: str) -> list[dict[str, Any]]:
    raw = manifest.get("migration_steps")
    if not isinstance(raw, list):
        return []

    start_ver = _parse_pack_version(from_version)
    end_ver = _parse_pack_version(to_version)
    selected: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue

        introduced = item.get("introduced_in", "0.0.0")
        item_ver = _parse_pack_version(introduced)
        if not isinstance(item.get("id"), str) or not item.get("id").strip():
            continue
        if not item_ver:
            continue
        if item_ver <= end_ver and item_ver > start_ver:
            selected.append(item)
    selected.sort(key=lambda x: _parse_pack_version(x.get("introduced_in", "0.0.0")))
    return selected


def _build_migration_id(from_version: str, to_version: str) -> str:
    clean_from = "".join(ch for ch in from_version if ch.isalnum() or ch in "._-")
    clean_to = "".join(ch for ch in to_version if ch.isalnum() or ch in "._-")
    if not clean_from:
        clean_from = "unversioned"
    if not clean_to:
        clean_to = "unknown"
    return f"migration-{clean_from}-to-{clean_to}-{_now_stamp()}"


def _ensure_migration_dir(root: Path) -> Path:
    out = root / DEFAULT_MIGRATION_DIR
    out.mkdir(parents=True, exist_ok=True)
    return out


def _write_migration_checklist(
    root: Path,
    title: str,
    pack_from: str,
    pack_to: str,
    steps: list[dict[str, Any]],
) -> Path:
    out = _ensure_report_dir(root)
    out = out / f"csk-sync-migration-{_now_stamp()}.md"
    body = [
        f"# {title}",
        "",
        f"Version transition: `{pack_from}` → `{pack_to}`",
        "",
        "## Required update actions",
        "",
    ]
    if not steps:
        body.append("No migration steps are required for this transition.")
    else:
        for idx, step in enumerate(steps, start=1):
            sid = str(step.get("id", f"step-{idx}"))
            title_ = str(step.get("title", sid))
            scope = step.get("scope", "global")
            required = bool(step.get("required", True))
            req_label = "required" if required else "optional"
            body.append(f"{idx}. **[{req_label}][{scope}] {title_}** (`{sid}`)")
            summary = step.get("summary") or step.get("description") or "No summary."
            body.append(f"   - {summary}")
            actions = step.get("actions")
            if isinstance(actions, list) and actions:
                body.append("   - Actions:")
                for action in actions:
                    body.append(f"     - {action}")
            compatibility = step.get("compatibility")
            if isinstance(compatibility, list) and compatibility:
                body.append("   - Compatibility notes:")
                for note in compatibility:
                    body.append(f"     - {note}")
            if step.get("docs"):
                body.append(f"   - Docs: {step['docs']}")
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out


def _write_migration_report(
    root: Path,
    source_url: str,
    source_ref: str,
    source_commit: str,
    pack_from: str,
    pack_to: str,
    migration_notes: str,
    steps: list[dict[str, Any]],
    command_surface: dict[str, Any] | None = None,
) -> tuple[Path, list[dict[str, Any]], Path]:
    migration_dir = _ensure_migration_dir(root)
    migration_id = _build_migration_id(pack_from, pack_to)
    report_path = migration_dir / f"{migration_id}.json"
    checklist_path = _write_migration_checklist(
        root=root,
        title="CSK migration checklist",
        pack_from=pack_from,
        pack_to=pack_to,
        steps=steps,
    )
    payload = {
        "migration_id": migration_id,
        "pack_from": pack_from,
        "pack_to": pack_to,
        "migration_notes": migration_notes,
        "source_url": source_url,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "generated_at": _iso_now(),
        "status": "pending",
        "steps": steps,
        "steps_count": len(steps),
        "report_path": str(report_path),
        "checklist_path": str(checklist_path),
    }
    if command_surface is not None:
        payload["command_surface"] = command_surface
    _write_json(report_path, payload)
    return report_path, steps, checklist_path


def _load_migration_status(state: dict[str, Any]) -> tuple[bool, str]:
    pending = bool(state.get("migration_pending", False))
    migration_file = state.get("last_migration_file")
    if not pending:
        return False, ""
    if not migration_file:
        return True, "missing_migration_file"
    mf = Path(str(migration_file))
    if not mf.exists():
        return True, "missing_migration_report"
    ack = Path(str(mf) + ".ack.json")
    if not ack.exists():
        return True, "pending_migration_ack"
    return False, ""


def _resolve_migration_file(root: Path, migration_file: str) -> Path | None:
    candidate = Path(migration_file)
    if candidate.is_absolute():
        if candidate.exists():
            return candidate
        return None
    raw = root / candidate
    if raw.exists():
        return raw
    return None
def _clone_source(source_url: str, source_ref: str, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    clone = _run(["git", "clone", "--depth", "1", "--branch", source_ref, source_url, str(target)])
    if clone.returncode != 0:
        raise SyncError(f"Failed to clone source repository:\n{clone.stderr.strip()}")
    rev = _run(["git", "rev-parse", "HEAD"], cwd=target)
    if rev.returncode != 0:
        raise SyncError(f"Failed to resolve source commit:\n{rev.stderr.strip() or rev.stdout.strip()}")
    return rev.stdout.strip()


def _replace_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        if dst.exists() and not dst.is_dir():
            dst.unlink()
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return

    if dst.exists():
        if dst.is_dir():
            shutil.rmtree(dst)
        else:
            dst.unlink()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _backup_path(src: Path, backup_target: Path) -> None:
    backup_target.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, backup_target, dirs_exist_ok=True)
    else:
        shutil.copy2(src, backup_target)


def _try_yaml() -> Any | None:
    try:
        import yaml  # type: ignore

        return yaml
    except Exception:
        return None


def _frontmatter_errors(skill_path: Path) -> list[str]:
    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return ["missing YAML frontmatter opening '---'"]
    try:
        end_idx = lines[1:].index("---") + 1
    except ValueError:
        return ["missing YAML frontmatter closing '---'"]
    header = lines[1:end_idx]
    ymod = _try_yaml()
    if ymod is None:
        return [
            "strict YAML frontmatter parser unavailable. Install PyYAML: "
            "`python -m pip install pyyaml`"
        ]
    payload = "\n".join(header) + "\n"
    try:
        parsed = ymod.safe_load(payload)
    except Exception as exc:  # noqa: BLE001
        return [f"invalid YAML frontmatter ({exc})"]
    if not isinstance(parsed, dict):
        return ["frontmatter must be a YAML mapping/object"]
    errors: list[str] = []
    for key in ("name", "description"):
        value = parsed.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"frontmatter requires non-empty string field `{key}`")
    return errors


def _manifest_skill_files(root: Path, items: list[SyncItem]) -> list[Path]:
    """Return SKILL.md files that are actually covered by manifest paths."""
    skill_files: set[Path] = set()
    base = root / ".agents" / "skills"
    if not base.exists():
        return []

    for item in items:
        p = _safe_rel(item.path)
        if p == Path(".agents", "skills"):
            for skill_file in base.rglob("SKILL.md"):
                skill_files.add(skill_file)
            continue

        if not str(p).startswith(".agents/skills/"):
            continue

        candidate = root / p
        if candidate.name == "SKILL.md":
            if candidate.exists():
                skill_files.add(candidate)
            continue

        if candidate.is_dir():
            for skill_file in candidate.rglob("SKILL.md"):
                skill_files.add(skill_file)

    return sorted(skill_files, key=lambda pth: pth.as_posix())


def _preflight_dependencies(root: Path, items: list[SyncItem]) -> list[str]:
    errors: list[str] = []
    skill_files = _manifest_skill_files(root, items)
    if skill_files and _try_yaml() is None:
        errors.append("preflight: strict YAML parser unavailable; install PyYAML (`python -m pip install pyyaml`)")

    needs_csk_cli_probe = any(
        item.path == "tools/csk/csk.py" or item.path.startswith("tools/csk/")
        for item in items
    )
    if needs_csk_cli_probe:
        csk_py = root / "tools" / "csk" / "csk.py"
        if not csk_py.exists():
            errors.append("preflight: csk.py is missing in checked paths")
        else:
            probe = _run([sys.executable, str(csk_py), "-h"], cwd=root)
            if probe.returncode != 0:
                errors.append(f"preflight: csk.py -h failed: {probe.stderr.strip() or probe.stdout.strip()}")

    return errors


def _content_health_check(root: Path, items: list[SyncItem]) -> list[str]:
    errors: list[str] = []
    for item in items:
        rel = _safe_rel(item.path)
        target = root / rel
        if item.required and not target.exists():
            errors.append(f"required path missing after sync: {item.path}")

    for skill_file in _manifest_skill_files(root, items):
        if not skill_file.exists():
            # Missing optional skill paths are handled by required-path checks above.
            continue
        fm_errors = _frontmatter_errors(skill_file)
        if fm_errors:
            for err in fm_errors:
                errors.append(f"{skill_file}: {err}")

    return errors


def _extract_parser_commands(help_text: str) -> set[str]:
    """Extract top-level argparse subcommand names from ``-h`` output."""
    if not help_text:
        return set()

    normalized = " ".join(help_text.split())
    match = re.search(r"\{([^{}]+)\}", normalized)
    if not match:
        return set()

    commands: set[str] = set()
    for token in match.group(1).split(","):
        name = token.strip()
        if name and name != "...":
            commands.add(name)
    return commands


def _extract_string_constant(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Str):
        return node.s
    return None


def _extract_parser_commands_from_source(script: Path) -> tuple[set[str], str]:
    """Extract subcommand names from source using AST parsing.

    Returns (commands, error). If AST parse fails, falls back to regex extraction.
    """
    if not script.exists():
        return set(), f"missing: {script}"

    try:
        source_text = script.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return set(), f"{script}: failed to read: {exc}"

    commands: set[str] = set()
    try:
        tree = ast.parse(source_text)
    except Exception as exc:  # noqa: BLE001
        pattern = re.compile(r"\.add_parser\(\s*([\"'])(?P<name>.+?)\1")
        for match in pattern.finditer(source_text):
            name = match.group("name").strip()
            if not name or name == "..." or name.startswith("-"):
                continue
            commands.add(name)

        if commands:
            return commands, ""

        return set(), f"{script}: ast parse failed ({exc})"

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue

        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_parser":
            continue

        arg_value = None
        if node.args:
            arg_value = _extract_string_constant(node.args[0])
        else:
            for kw in node.keywords:
                if kw.arg == "name":
                    arg_value = _extract_string_constant(kw.value)
                    break

        if not arg_value:
            continue
        name = arg_value.strip()
        if not name or name == "..." or name.startswith("-"):
            continue
        commands.add(name)

    if commands:
        return commands, ""

    return set(), f"{script}: unable to resolve parser commands from source"


def _probe_parser_commands_detailed(script: Path, repo_root: Path) -> tuple[set[str], str, str]:
    """Return parser commands, optional error and probe mode."""
    source_commands, source_error = _extract_parser_commands_from_source(script)
    if source_commands:
        return source_commands, "", "source-ast"

    fallback = source_error or ""

    if not script.exists():
        return set(), fallback or f"missing: {script}", "source-missing"

    probe = _run([sys.executable, str(script), "-h"], cwd=repo_root)
    if probe.returncode != 0:
        return (
            set(),
            fallback or f"{script}: {probe.stderr.strip() or probe.stdout.strip()}",
            "runtime-help-failed",
        )

    return _extract_parser_commands(probe.stdout), "", "runtime-help"


def _probe_parser_commands(script: Path, repo_root: Path) -> tuple[set[str], str]:
    """Backward-compatible alias with error only."""
    commands, error, _ = _probe_parser_commands_detailed(script, repo_root)
    return commands, error


def _safe_command_set(raw: Any) -> set[str]:
    if not isinstance(raw, list):
        return set()

    out: set[str] = set()
    for item in raw:
        if not isinstance(item, str):
            continue
        name = item.strip()
        if name:
            out.add(name)
    return out


def _verify(root: Path, items: list[SyncItem]) -> list[str]:
    # Backward-compatible shim: runtime preflight now explicit; verify checks content only.
    return _content_health_check(root, items)


def _snapshot_state(
    root: Path,
    target: Path,
    backup_root: Path,
    snapshots: list[dict[str, Any]],
    seen: set[str],
) -> None:
    rel = target.relative_to(root)
    key = rel.as_posix()
    if key in seen:
        return
    seen.add(key)

    entry: dict[str, Any] = {
        "path": key,
        "existed": target.exists(),
        "is_dir": target.is_dir(),
        "backup": None,
    }
    if target.exists():
        backup_path = backup_root / key
        _backup_path(target, backup_path)
        entry["backup"] = str(backup_path)
        entry["backup_is_dir"] = backup_path.is_dir()
    snapshots.append(entry)


def _restore_state(root: Path, backup_root: Path, snapshots: list[dict[str, Any]]) -> None:
    for entry in sorted(snapshots, key=lambda x: len(x["path"]), reverse=True):
        target = root / entry["path"]
        if target.exists() and not target.is_symlink():
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        elif target.exists():
            target.unlink()

        backup = entry.get("backup")
        if not backup:
            continue

        backup_path = Path(backup)
        if not backup_path.exists():
            continue

        if backup_path.is_dir():
            if not backup_path.is_relative_to(backup_root):
                # legacy safety: do not restore from unknown locations
                continue
            shutil.copytree(backup_path, target)
        elif backup_path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, target)


def _load_manifest(path: Path) -> list[SyncItem]:
    data = _load_json(path)
    items_raw = data.get("sync_paths", [])
    if not isinstance(items_raw, list) or not items_raw:
        raise SyncError("Manifest must contain non-empty array `sync_paths`.")

    items: list[SyncItem] = []
    for raw in items_raw:
        if isinstance(raw, str):
            items.append(SyncItem(path=raw, required=True, merge_mode="overlay_allowed"))
            continue
        if not isinstance(raw, dict):
            raise SyncError("Each `sync_paths` item must be string or object.")
        path_value = raw.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise SyncError("`sync_paths[].path` must be non-empty string.")
        merge_mode = str(raw.get("merge_mode", "overlay_allowed"))
        if merge_mode not in MERGE_MODES:
            raise SyncError(
                f"Invalid merge_mode for {path_value}: {merge_mode}. Expected one of {sorted(MERGE_MODES)}"
            )
        items.append(
            SyncItem(
                path=path_value,
                required=bool(raw.get("required", True)),
                merge_mode=merge_mode,
            )
        )
    return items


def _git_dirty_paths(root: Path, items: list[SyncItem]) -> list[str]:
    rel_paths = [item.path for item in items]
    status = _run(["git", "status", "--porcelain", "--", *rel_paths], cwd=root)
    if status.returncode != 0:
        return []
    dirty: list[str] = []
    for line in status.stdout.splitlines():
        if len(line) < 4:
            continue
        dirty.append(line[3:].strip())
    return dirty


def _parse_backup_stamp(name: str) -> datetime | None:
    prefix = "csk-sync-"
    if not name.startswith(prefix):
        return None
    stamp = name[len(prefix) :]
    try:
        dt = datetime.strptime(stamp, "%Y%m%dT%H%M%SZ")
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc)


def _build_backup_candidates(root: Path, items: list[SyncItem], source_ref: str) -> list[dict[str, Any]]:
    backups_root = root / ".csk-app" / "backups"
    if not backups_root.exists():
        return []

    current_hashes: dict[str, str | None] = {}
    for item in items:
        rel = _safe_rel(item.path)
        current_hashes[item.path] = _path_hash(root / rel)

    candidates: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for backup_dir in sorted(backups_root.glob("csk-sync-*"), reverse=True):
        if not backup_dir.is_dir():
            continue

        present = 0
        compared = 0
        equal = 0
        for item in items:
            rel = _safe_rel(item.path)
            b_hash = _path_hash(backup_dir / rel)
            if b_hash is not None:
                present += 1
            c_hash = current_hashes[item.path]
            if b_hash is not None and c_hash is not None:
                compared += 1
                if b_hash == c_hash:
                    equal += 1

        coverage_ratio = present / len(items)
        path_similarity = (equal / compared) if compared else 0.0

        report_ref = None
        report_url = None
        report_path = root / ".csk-app" / "reports" / f"{backup_dir.name}.json"
        if report_path.exists():
            try:
                report = _load_json_optional(report_path, default={})
                report_ref = report.get("source_ref")
                report_url = report.get("source_url")
            except json.JSONDecodeError:
                report_ref = None
                report_url = None

        ref_match = 1.0 if report_ref == source_ref else 0.0

        age_days = None
        recency_score = 0.0
        parsed = _parse_backup_stamp(backup_dir.name)
        if parsed is not None:
            age_days = (now - parsed).total_seconds() / 86400.0
            recency_score = max(0.0, 1.0 - (age_days / 30.0))

        score = (coverage_ratio * 0.45) + (path_similarity * 0.35) + (ref_match * 0.15) + (recency_score * 0.05)
        candidates.append(
            {
                "backup_name": backup_dir.name,
                "backup_path": str(backup_dir),
                "coverage_ratio": round(coverage_ratio, 4),
                "path_similarity": round(path_similarity, 4),
                "ref_match": round(ref_match, 4),
                "recency_score": round(recency_score, 4),
                "age_days": None if age_days is None else round(age_days, 2),
                "score": round(score, 4),
                "source_ref": report_ref,
                "source_url": report_url,
            }
        )

    candidates.sort(key=lambda x: (x["score"], x["coverage_ratio"], x["recency_score"]), reverse=True)
    return candidates


def _ensure_decision_dir(root: Path) -> Path:
    out = root / ".csk-app" / "sync" / "decisions"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _ensure_report_dir(root: Path) -> Path:
    out = root / ".csk-app" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    return out


def _save_report(root: Path, report: dict[str, Any]) -> Path:
    out_dir = _ensure_report_dir(root)
    out = out_dir / f"csk-sync-{_now_stamp()}.json"
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return out


def _write_checklist(root: Path, title: str, lines: list[str]) -> Path:
    out_dir = _ensure_report_dir(root)
    out = out_dir / f"csk-sync-checklist-{_now_stamp()}.md"
    body = [f"# {title}", "", "## Required actions", ""]
    for idx, line in enumerate(lines, start=1):
        body.append(f"{idx}. {line}")
    out.write_text("\n".join(body) + "\n", encoding="utf-8")
    return out


def _write_decision_template(
    root: Path,
    candidates: list[dict[str, Any]],
    source_url: str,
    source_ref: str,
    top_candidates: int,
) -> Path:
    decision_dir = _ensure_decision_dir(root)
    out = decision_dir / f"decision-{_now_stamp()}.json"
    payload = {
        "selected_backup": None,
        "confidence": 0.0,
        "rationale": "AI assistant must select backup from candidate_table.",
        "candidate_table": candidates[:top_candidates],
        "approved_by_human": False,
        "approved_at": None,
        "source_url": source_url,
        "source_ref": source_ref,
        "created_at": _iso_now(),
    }
    _write_json(out, payload)
    return out


def _resolve_backup_path(root: Path, selected: str | None) -> Path | None:
    if selected is None:
        return None

    raw = Path(selected)
    if raw.is_absolute() and raw.exists() and raw.is_dir():
        return raw

    if not raw.is_absolute():
        candidates = [
            root / raw,
            root / ".csk-app" / "backups" / selected,
        ]
        for c in candidates:
            if c.exists() and c.is_dir():
                return c
    return None


def _validate_decision_file(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    if not isinstance(data, dict):
        raise SyncError("Decision file must be a JSON object.")

    if "selected_backup" not in data:
        raise SyncError("Decision file: missing required `selected_backup`.")
    if "confidence" not in data:
        raise SyncError("Decision file: missing required `confidence`.")
    if "rationale" not in data:
        raise SyncError("Decision file: missing required `rationale`.")
    if "candidate_table" not in data:
        raise SyncError("Decision file: missing required `candidate_table`.")
    if "approved_by_human" not in data:
        raise SyncError("Decision file: missing required `approved_by_human`.")
    if "approved_at" not in data:
        raise SyncError("Decision file: missing required `approved_at`.")

    if data["selected_backup"] is not None and not isinstance(data["selected_backup"], str):
        raise SyncError("Decision file: `selected_backup` must be string or null.")

    if not isinstance(data["confidence"], (float, int)) or isinstance(data["confidence"], bool):
        raise SyncError("Decision file: `confidence` must be a number.")
    conf = float(data["confidence"])
    if not math.isfinite(conf) or conf < 0.0 or conf > 1.0:
        raise SyncError("Decision file: `confidence` must be in [0, 1].")
    if "candidate_table" in data and not isinstance(data["candidate_table"], list):
        raise SyncError("Decision file: `candidate_table` must be an array.")
    if data["candidate_table"] and any(not isinstance(x, dict) for x in data["candidate_table"]):
        raise SyncError("Decision file: `candidate_table` must contain only objects.")
    if "rationale" in data and not isinstance(data["rationale"], str):
        raise SyncError("Decision file: `rationale` must be a string.")
    if not isinstance(data["approved_by_human"], bool):
        raise SyncError("Decision file: `approved_by_human` must be boolean.")
    if data["approved_at"] is not None and not isinstance(data["approved_at"], str):
        raise SyncError("Decision file: `approved_at` must be string or null.")

    return data


def _validate_json_path(path: Path) -> list[str]:
    errors: list[str] = []
    if path.is_file() and path.suffix.lower() == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
        return errors

    if path.is_dir():
        for child in sorted(path.rglob("*.json")):
            try:
                json.loads(child.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{child}: invalid JSON ({exc})")
    return errors


def _plan_overlay_actions(
    root: Path,
    source_root: Path,
    overlay_root: Path,
    items: list[SyncItem],
    selected_backup: Path | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str], list[str], list[str], list[str]]:
    write_actions: list[dict[str, Any]] = []
    apply_actions: list[dict[str, Any]] = []
    blockers: list[str] = []
    backup_fallback_paths: list[str] = []
    existing_overlay_paths: list[str] = []
    bootstrap_overlay_paths: list[str] = []

    for item in items:
        if item.merge_mode == "manual_only":
            blockers.append(f"manual_only path requires explicit manual migration: {item.path}")
            continue

        rel = _safe_rel(item.path)
        overlay_path = overlay_root / rel
        upstream_path = source_root / rel
        if overlay_path.exists():
            existing_overlay_paths.append(item.path)
            if item.merge_mode == "replace_core":
                blockers.append(f"replace_core path cannot have overlay overrides: {item.path}")
                continue
            json_errors = _validate_json_path(overlay_path)
            if json_errors:
                blockers.extend(json_errors)
                continue
            apply_actions.append(
                {
                    "type": "apply_overlay",
                    "path": item.path,
                    "overlay_source": str(overlay_path),
                }
            )
            continue

        backup_path = (selected_backup / rel) if selected_backup is not None else None
        current_path = root / rel
        source_path: Path | None = None
        source_kind: str | None = None
        if backup_path is not None and backup_path.exists():
            source_path = backup_path
            source_kind = "backup"
        elif current_path.exists():
            source_path = current_path
            source_kind = "current"
            backup_fallback_paths.append(item.path)
        if source_path is None:
            continue

        if _path_hash(source_path) == _path_hash(upstream_path):
            continue

        if item.merge_mode == "replace_core":
            blockers.append(f"replace_core path has local divergence and cannot be auto-migrated: {item.path}")
            continue
        json_errors = _validate_json_path(source_path)
        if json_errors:
            blockers.extend(json_errors)
            continue

        overlay_target = overlay_root / rel
        write_actions.append(
            {
                "type": "write_overlay",
                "path": item.path,
                "source": str(source_path),
                "source_kind": source_kind,
                "overlay_target": str(overlay_target),
            }
        )
        apply_actions.append(
            {
                "type": "apply_overlay",
                "path": item.path,
                "overlay_source": str(overlay_target),
            }
        )
        bootstrap_overlay_paths.append(item.path)

    return (
        write_actions,
        apply_actions,
        blockers,
        backup_fallback_paths,
        existing_overlay_paths,
        bootstrap_overlay_paths,
    )


def _apply_overlay_actions(root: Path, actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for action in actions:
        if action["type"] == "write_overlay":
            src = Path(action["source"])
            dst = Path(action["overlay_target"])
            _replace_path(src, dst)
            results.append(
                {
                    "path": action["path"],
                    "action": "overlay_written",
                    "source_kind": action.get("source_kind"),
                    "overlay_path": str(dst),
                }
            )
            continue

        if action["type"] == "apply_overlay":
            src = Path(action["overlay_source"])
            dst = root / _safe_rel(action["path"])
            _replace_path(src, dst)
            results.append(
                {
                    "path": action["path"],
                    "action": "overlay_applied",
                    "overlay_path": str(src),
                }
            )
            continue

        raise SyncError(f"Unknown overlay action type: {action['type']}")
    return results


def _apply_core_sync(
    root: Path,
    source_root: Path,
    items: list[SyncItem],
    backup_dir: Path,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for item in items:
        rel = _safe_rel(item.path)
        src = source_root / rel
        dst = root / rel

        result: dict[str, Any] = {
            "path": item.path,
            "source_exists": src.exists(),
            "destination_exists": dst.exists(),
            "action": "skip",
            "backup": None,
            "merge_mode": item.merge_mode,
        }

        if not src.exists():
            if item.required:
                raise SyncError(f"required path missing in source repository: {item.path}")
            results.append(result)
            continue

        result["action"] = "replace_core"
        if dst.exists():
            try:
                backup_dir.relative_to(dst)
                raise SyncError(
                    f"Unsafe replacement blocked for {item.path}: backup directory is nested under destination."
                )
            except ValueError:
                pass

            backup_target = backup_dir / rel
            _backup_path(dst, backup_target)
            result["backup"] = str(backup_target)

        _replace_path(src, dst)
        results.append(result)

    return results


def _write_state(
    state_path: Path,
    source_url: str,
    source_ref: str,
    source_commit: str,
    manifest_hash: str,
    pack_version: str | None = None,
    migration_pending: bool | None = None,
    migration_file: str | None = None,
) -> None:
    state = {
        "current_source_url": source_url,
        "current_source_ref": source_ref,
        "current_source_commit": source_commit,
        "last_sync_at": _iso_now(),
        "manifest_hash": manifest_hash,
        "overlay_version": 1,
    }
    if pack_version is not None:
        state["current_pack_version"] = pack_version
    if migration_pending is not None:
        state["migration_pending"] = migration_pending
    if migration_file is not None:
        state["last_migration_file"] = migration_file
    _write_json(state_path, state)


def _append_history(
    history_path: Path,
    mode: str,
    source_url: str,
    source_ref: str,
    source_commit: str | None,
    selected_backup: str | None,
    confidence: float | None,
    outcome: str,
    conflicts: list[str],
    report_path: Path | None,
    decision_path: Path | None,
    migration_file: Path | None = None,
) -> None:
    event = {
        "timestamp": _iso_now(),
        "mode": mode,
        "source_url": source_url,
        "source_ref": source_ref,
        "source_commit": source_commit,
        "selected_backup": selected_backup,
        "confidence": confidence,
        "outcome": outcome,
        "conflicts": conflicts,
        "report_path": None if report_path is None else str(report_path),
        "decision_path": None if decision_path is None else str(decision_path),
        "migration_file": None if migration_file is None else str(migration_file),
    }
    _append_jsonl(history_path, event)


def _load_last_migration_report(
    root: Path,
    state_path: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    state = _load_json_optional(state_path, default={})
    last_migration_file = state.get("last_migration_file")
    if not last_migration_file:
        return None, None

    path = _resolve_migration_file(root, str(last_migration_file))
    if path is None:
        return None, "missing"
    try:
        payload = _load_json(path)
    except Exception:
        return None, "invalid-json"
    if not isinstance(payload, dict):
        return None, "invalid-payload"
    return payload, None


def run_migration_status(root: Path, manifest_path: Path, state_path: Path, strict: bool = False) -> dict[str, Any]:
    manifest = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest)
    state = _load_json_optional(state_path, default={})
    state_pack = str(state.get("current_pack_version", "0.0.0"))
    last_migration_file = state.get("last_migration_file")
    migration_report, migration_report_error = _load_last_migration_report(root, state_path)

    report: dict[str, Any] = {
        "mode": "migration-status",
        "started_at": _now_stamp(),
        "pack_version": manifest_pack,
        "state_pack_version": state_pack,
        "success": True,
        "pending": False,
        "reasons": [],
        "last_migration_file": last_migration_file,
    }

    migration_needed = _version_cmp(manifest_pack, state_pack) > 0
    report["migration_needed"] = migration_needed

    if migration_needed:
        report["pending"] = True
        report["reasons"].append("pack_version increased, migration proof is required")
        steps = _extract_migration_steps(manifest, state_pack, manifest_pack)
        report["steps_count"] = len(steps)
        report["step_ids"] = [s.get("id") for s in steps]
        if steps:
            if not last_migration_file:
                report["reasons"].append("missing migration report path in state")
            else:
                path = _resolve_migration_file(root, str(last_migration_file))
                if path is None:
                    report["reasons"].append("migration report file is missing")
                elif migration_report_error == "invalid-json":
                    report["reasons"].append("migration report has invalid JSON")
                elif migration_report_error == "invalid-payload":
                    report["reasons"].append("migration report has invalid payload")
                elif migration_report is None:
                    report["reasons"].append("migration report cannot be loaded")
                else:
                    if not path.exists():
                        report["reasons"].append("migration report file is missing")
                    else:
                        ack = path.with_suffix(path.suffix + ".ack.json")
                        if not ack.exists():
                            report["reasons"].append("migration report has not been acknowledged")
                            report["ack_required"] = str(ack)

            report["steps_count"] = len(steps)
            report["steps"] = steps
            report["steps_hash"] = _hash_bytes(json.dumps(steps, sort_keys=True).encode("utf-8"))
    
    elif state.get("migration_pending", False):
        report["pending"] = True
        report["reasons"].append("migration_pending flag is set in state despite up-to-date pack version")
        if migration_report_error == "missing":
            report["reasons"].append("migration pending is set but last migration report is missing")
        elif migration_report_error == "invalid-json":
            report["reasons"].append("migration pending is set but last migration report has invalid JSON")
        elif migration_report_error == "invalid-payload":
            report["reasons"].append("migration pending is set but last migration report has invalid payload")
        if migration_report:
            report["steps"] = migration_report.get("steps", [])
            report["steps_count"] = len(report.get("steps", []))
            report["steps_hash"] = _hash_bytes(
                json.dumps(report["steps"], sort_keys=True).encode("utf-8")
            ).rstrip("\n")
            report["migration_pack_from"] = migration_report.get("pack_from")
            report["migration_pack_to"] = migration_report.get("pack_to")
            report["migration_report_source_ref"] = migration_report.get("source_ref")
            report["migration_report_source_url"] = migration_report.get("source_url")

    if strict and report["pending"] and report["reasons"]:
        report["success"] = False

    report["finished_at"] = _now_stamp()
    return report


def _iter_task_dirs(root: Path) -> list[Path]:
    modules_root = root / "modules"
    if not modules_root.exists():
        return []

    task_dirs: list[Path] = []
    for module in sorted(modules_root.iterdir()):
        if not module.is_dir():
            continue
        csk_dir = module / ".csk" / "tasks"
        if not csk_dir.exists():
            continue
        for task_dir in sorted(p for p in csk_dir.iterdir() if p.is_dir()):
            if task_dir.name.startswith("T-"):
                task_dirs.append(task_dir)
    return task_dirs


def _iter_initiative_dirs(root: Path) -> list[Path]:
    initiatives_root = root / ".csk-app" / "initiatives"
    if not initiatives_root.exists():
        return []
    return [p for p in sorted(initiatives_root.iterdir()) if p.is_dir()]


def _build_workflow_profile(root: Path) -> dict[str, Any]:
    task_dirs = _iter_task_dirs(root)
    initiative_dirs = _iter_initiative_dirs(root)

    tasks_without_plan_summary = 0
    tasks_without_user_acceptance = 0
    for task_dir in task_dirs:
        if not (task_dir / "plan.summary.md").exists():
            tasks_without_plan_summary += 1
        if not (task_dir / "user_acceptance.md").exists():
            tasks_without_user_acceptance += 1

    initiatives_missing_summary = 0
    initiatives_missing_status = 0
    for initiative_dir in initiative_dirs:
        if not (initiative_dir / "initiative.summary.md").exists():
            initiatives_missing_summary += 1
        if not (initiative_dir / "initiative.status.json").exists():
            initiatives_missing_status += 1

    modules_dir = root / "modules"
    module_count = len([m for m in modules_dir.iterdir() if m.is_dir()]) if modules_dir.exists() else 0

    csk_py = root / "tools" / "csk" / "csk.py"
    csk_commands, csk_commands_error = _probe_parser_commands(csk_py, root)

    return {
        "module_count": module_count,
        "task_count": len(task_dirs),
        "tasks_without_plan_summary": tasks_without_plan_summary,
        "tasks_without_user_acceptance": tasks_without_user_acceptance,
        "initiative_count": len(initiative_dirs),
        "initiatives_missing_summary": initiatives_missing_summary,
        "initiatives_missing_status": initiatives_missing_status,
        "deployed_csk_commands": sorted(csk_commands),
        "deployed_csk_commands_error": csk_commands_error,
    }


def _build_wizard_step_recommendation(
    step: dict[str, Any],
    workflow: dict[str, Any],
) -> dict[str, Any]:
    step_id = str(step.get("id", "unknown"))
    required = bool(step.get("required", True))
    title = str(step.get("title", step_id))
    scope = str(step.get("scope", "global"))
    summary = str(step.get("summary", "No summary."))
    actions = [str(a) for a in (step.get("actions") or []) if isinstance(a, str) and a.strip()]
    compatibility = [str(a) for a in (step.get("compatibility") or []) if isinstance(a, str) and a.strip()]
    docs = str(step.get("docs", ""))

    recommended_actions: list[str] = actions.copy()
    risk_notes: list[str] = []
    status = "ready"
    transition = "keep current path and adopt with minimal change"
    if step_id == "plan-summary-contract":
        missing = workflow["tasks_without_plan_summary"]
        if missing > 0:
            status = "pending"
            risk_notes.append(f"{missing} existing tasks do not yet have plan.summary.md.")
            transition = (
                "Keep new-task module flow intact and add shareable artifacts by running "
                "reconcile-task-artifacts (per-module if needed)."
            )
            recommended_actions.extend(
                [
                    "python tools/csk/csk.py reconcile-task-artifacts --strict",
                    "python tools/csk/csk.py reconcile-task-artifacts --module-id <module> --strict",
                ]
            )
    elif step_id == "user-check-gate":
        missing = workflow["tasks_without_user_acceptance"]
        if missing > 0:
            status = "pending"
            risk_notes.append(f"{missing} existing tasks miss user_acceptance.md.")
            transition = (
                "Keep existing tasks. For each legacy task, generate user_acceptance.md and record manual user-check."
            )
            recommended_actions.extend(
                [
                    "python tools/csk/csk.py regen-user-acceptance <module> <task>",
                    "python tools/csk/csk.py record-user-check <module> <task> --result pass",
                ]
            )
    elif step_id == "initiative-orchestration":
        has_initiative_artefacts = bool(workflow["initiative_count"])
        has_initiative_commands = "initiative-new" in workflow["deployed_csk_commands"]
        if not has_initiative_artefacts and not has_initiative_commands:
            risk_notes.append("Initiative feature is not currently visible to users.")
            transition = (
                "Add initiative flow as optional layer: continue existing new-task work, "
                "then pilot initiative for cross-module work only."
            )
            status = "recommended"
            recommended_actions.extend(
                [
                    "python tools/csk/csk.py initiative-new \"<initiative-title>\" --goal \"...\"",
                    "python tools/csk/csk.py initiative-edit <I-id> --add-milestone \"...\"",
                    "python tools/csk/csk.py initiative-run <I-id> --next --apply",
                    "python tools/csk/csk.py initiative-status <I-id>",
                ]
            )
        elif has_initiative_artefacts and has_initiative_commands:
            status = "in_progress"
            transition = (
                "Initiative artifacts already exist. Continue module-first for legacy scope and use initiative "
                "only for multi-module trajectories."
            )
        else:
            status = "in_progress"
            transition = "Verify initiative command surface and reconcile existing artifacts."
    elif step_id == "csk-ready-pack-gate":
        if workflow.get("migration_pending", False):
            status = "blocking"
            transition = (
                "Before any READY/approve-ready, close migration check and acknowledge migration file."
            )
            recommended_actions.extend(
                [
                    "python tools/csk/sync_upstream.py migration-status --migration-strict",
                    "python tools/csk/sync_upstream.py migration-ack --migration-file <migration-report> --migration-by <name> --migration-notes \"...\"",
                ]
            )
            risk_notes.append("READY is blocked while migration is pending.")
        else:
            transition = "Migration gate is cleared; enforce checks in normal READY flow."
    else:
        if "required" in str(step_id) or required:
            transition = "Enforce by running the migration checklist and updating docs/approvals."

    return {
        "id": step_id,
        "title": title,
        "required": required,
        "scope": scope,
        "summary": summary,
        "docs": docs,
        "status": status,
        "compatibility": compatibility,
        "commands": sorted(set(recommended_actions)) if recommended_actions else actions,
        "transition": transition,
        "risk_notes": risk_notes,
    }


def _build_wizard_transition_plan(workflow: dict[str, Any]) -> dict[str, Any]:
    if workflow["initiative_count"] > 0 and workflow["task_count"] > 0:
        strategy = "mixed"
    elif workflow["initiative_count"] > 0:
        strategy = "initiative_first"
    elif workflow["task_count"] > 0:
        strategy = "module_first_preserve"
    else:
        strategy = "bootstrap_ready"

    phases: list[dict[str, Any]] = [
        {
            "phase": "0",
            "name": "No breaking change",
            "goal": "Continue existing module-first flow for current tasks.",
            "commands": ["python tools/csk/csk.py new-task <module> \"...\""],
        }
    ]
    if strategy in {"module_first_preserve", "mixed"}:
        phases.append(
            {
                "phase": "1",
                "name": "Targeted pilot",
                "goal": "Apply initiative orchestration only for cross-module work.",
                "commands": [
                    "python tools/csk/csk.py initiative-new \"...\" --goal \"...\"",
                    "python tools/csk/csk.py initiative-run <I-id> --next --apply",
                ],
            }
        )
    if strategy in {"initiative_first", "mixed", "module_first_preserve"}:
        phases.append(
            {
                "phase": "2",
                "name": "Convergence",
                "goal": "Run migration artifacts cleanup and strict checks before READY.",
                "commands": [
                    "python tools/csk/csk.py reconcile-task-artifacts --strict",
                    "python tools/csk/csk.py reconcile-initiative-artifacts --strict",
                    "python tools/csk/csk.py validate --all --strict",
                ],
            }
        )

    return {
        "strategy": strategy,
        "phases": phases,
    }


def _build_migration_adoption_coaching(
    state_pack: str,
    manifest_pack: str,
    steps: list[dict[str, Any]],
    workflow: dict[str, Any],
    command_profile: dict[str, Any],
) -> dict[str, Any]:
    source_commands = set(command_profile.get("source_commands", []))
    deployed_commands = set(command_profile.get("deployed_after", []))
    command_delta = command_profile.get("command_delta", {})

    has_initiative_in_source = "initiative-new" in source_commands
    has_initiative_deployed = "initiative-new" in deployed_commands

    new_features: list[dict[str, Any]] = []
    for step in steps:
        sid = str(step.get("id", ""))
        if not sid:
            continue
        title = str(step.get("title", sid))
        summary = str(step.get("summary", step.get("description", "")))
        actions = [str(a) for a in step.get("actions", []) if isinstance(a, str) and a.strip()]
        compatibility = [
            str(a) for a in step.get("compatibility", []) if isinstance(a, str) and a.strip()
        ]
        new_features.append(
            {
                "id": sid,
                "title": title,
                "scope": str(step.get("scope", "global")),
                "required": bool(step.get("required", True)),
                "summary": summary,
                "actions": actions,
                "compatibility": compatibility,
                "docs": step.get("docs", ""),
            }
        )

    if not new_features:
        new_features.append(
            {
                "id": "noop",
                "title": "No new migration features",
                "scope": "global",
                "required": False,
                "summary": "No migration steps apply for the current pack transition.",
                "actions": [],
                "compatibility": [],
                "docs": "",
            }
        )

    task_count = int(workflow.get("task_count", 0))
    initiative_count = int(workflow.get("initiative_count", 0))
    added_delta = sorted(_safe_command_set(command_delta.get("added")))
    removed_delta = sorted(_safe_command_set(command_delta.get("removed")))
    extra_delta = sorted(_safe_command_set(command_delta.get("extra")))
    new_initiative_commands = [cmd for cmd in added_delta if cmd.startswith("initiative-")]
    has_new_initiative_capability = has_initiative_in_source and new_initiative_commands
    blockers: list[str] = []

    can_pilot_initiatives = (
        has_initiative_in_source
        and has_initiative_deployed
        and (initiative_count > 0 or bool(has_new_initiative_capability) or task_count > 6)
    )

    initiative_command_blocked = has_initiative_in_source and not has_initiative_deployed
    needs_task_artifacts = task_count > 0
    needs_initiative_artifacts = initiative_count > 0
    should_validate = needs_task_artifacts or needs_initiative_artifacts or bool(blockers)
    recommended_profile = "module_first" if task_count >= initiative_count else "mixed"

    profiles: list[dict[str, Any]] = []

    profiles.append(
        {
            "name": "module_first",
            "applies_when": (
                "module tasks present"
                if needs_task_artifacts
                else "no module tasks yet"
            ),
            "goal": "Сохранить `new-task` и прогнать обязательные миграционные артефакты.",
            "condition": "recommended" if needs_task_artifacts else "fallback",
            "commands": [
                "python tools/csk/sync_upstream.py migration-status --migration-strict",
                "python tools/csk/sync_upstream.py migration-wizard",
                "python tools/csk/csk.py reconcile-task-artifacts --strict",
                "python tools/csk/csk.py validate --all --strict",
            ],
        }
    )

    mixed_commands = [
        "python tools/csk/csk.py initiative-new \"<initiative-title>\" --goal \"...\"",
        "python tools/csk/csk.py initiative-edit <I-id> --add-milestone \"...\"",
        "python tools/csk/csk.py initiative-run <I-id> --next --apply",
        "python tools/csk/csk.py initiative-status <I-id>",
        "python tools/csk/csk.py reconcile-task-artifacts --strict",
        "python tools/csk/csk.py validate --all --strict",
    ]
    if needs_initiative_artifacts:
        mixed_commands.insert(5, "python tools/csk/csk.py reconcile-initiative-artifacts --strict")

    profiles.append(
        {
            "name": "mixed",
            "applies_when": "Есть cross-module кандидаты, но часть legacy потоков ещё module-first.",
            "goal": "Включать initiative для крупных сквозных задач.",
            "condition": "strong_candidate" if task_count > 0 else "default",
            "commands": mixed_commands,
        }
    )

    initiative_profile_condition = (
        "available_now"
        if has_initiative_in_source and has_initiative_deployed
        else ("blocked_by_command_surface" if has_initiative_in_source else "not_applicable")
    )
    initiative_commands = [
        "python tools/csk/csk.py initiative-new \"<initiative-title>\" --goal \"...\"",
        "python tools/csk/csk.py initiative-edit <I-id> --add-milestone \"...\"",
        "python tools/csk/csk.py initiative-split <I-id> --mode auto",
        "python tools/csk/csk.py initiative-run <I-id> --next --apply",
        "python tools/csk/csk.py initiative-status <I-id> --json",
        "python tools/csk/csk.py validate --all --strict",
    ]
    if needs_initiative_artifacts:
        initiative_commands.insert(5, "python tools/csk/csk.py reconcile-initiative-artifacts --strict")

    profiles.append(
        {
            "name": "initiative_first",
            "applies_when": (
                "Команда готова к инициативному потоку."
                if can_pilot_initiatives
                else "Рекомендуется сначала закрыть blockers и закрыть command-surface."
            ),
            "goal": "Вести масштабные изменения через initiative orchestration как стандарт.",
            "condition": initiative_profile_condition,
            "commands": initiative_commands,
            "risk": (
                "initiative-first blocked: deployed CLI still missing initiative-new."
                if initiative_command_blocked
                else "initiative-first available."
            ),
        }
    )

    missing_delta = sorted(_safe_command_set(source_commands - deployed_commands))
    if missing_delta:
        blockers.append(
            "Command surface still misses expected commands from source: "
            + ", ".join(missing_delta)
        )
    if extra_delta:
        blockers.append(
            "Source and deployed CLI have extra commands; check if they are intentional overlay changes."
        )
    if added_delta:
        blockers.append(
            "Migration introduces new CLI commands. Validate command surface first before changing your own automation."
        )
    if has_initiative_in_source and not has_initiative_deployed:
        blockers.append(
            "Source has initiative commands, but deployed CLI lacks initiative-new; do not switch to initiative-first yet."
        )
    should_validate = bool(
        needs_task_artifacts or needs_initiative_artifacts or bool(blockers)
    )

    return {
        "pack_transition": {
            "from_pack": state_pack,
            "to_pack": manifest_pack,
            "source_has_initiative": has_initiative_in_source,
            "deployed_has_initiative": has_initiative_deployed,
            "delta_added": sorted(_safe_command_set(command_delta.get("added"))),
            "delta_removed": sorted(_safe_command_set(command_delta.get("removed"))),
            "delta_extra": extra_delta,
            "task_count": workflow.get("task_count", 0),
            "initiative_count": workflow.get("initiative_count", 0),
        },
        "new_features": new_features,
        "recommended_profile": recommended_profile,
        "adoption_profiles": profiles,
        "risk_blockers": blockers,
        "needs_task_artifact_reconcile": needs_task_artifacts,
        "needs_initiative_artifact_reconcile": needs_initiative_artifacts,
        "should_validate": should_validate,
        "summary_note": (
            f"Pack transition {state_pack} -> {manifest_pack}; "
            f"{task_count} module tasks, {initiative_count} initiative artifacts."
        ),
        "first_steps": list(
            dict.fromkeys(
                [
                    "python tools/csk/sync_upstream.py migration-status --migration-strict",
                    "python tools/csk/sync_upstream.py migration-wizard",
                ]
                + (["python tools/csk/csk.py reconcile-task-artifacts --strict"] if needs_task_artifacts else [])
                + (
                    ["python tools/csk/csk.py initiative-new \"<initiative-title>\" --goal \"...\"",
                     "python tools/csk/csk.py initiative-edit <I-id> --add-milestone \"...\"",
                     "python tools/csk/csk.py initiative-run <I-id> --next --apply"]
                    if can_pilot_initiatives
                    else []
                )
                + (["python tools/csk/csk.py reconcile-initiative-artifacts --strict"] if needs_initiative_artifacts else [])
                + (["python tools/csk/csk.py validate --all --strict"] if should_validate else []),
            )
        ),
        "ai_prompt_starters": [
            "Какие 2-3 инициативы уже реально cross-module и их лучше перевести в initiative-first в текущем квартале?"
            if can_pilot_initiatives
            else "Какие legacy задачи дают наибольший риск и где лучше оставить module-first?",
            "Какие legacy задачи можно оставить module-first без риска и почему?",
            "Какие blockers из command_surface нужно закрыть до того, как ассистент начнет рекомендовать initiative-first flow?",
        ],
        "transition_overview": {
            "added_delta": added_delta,
            "removed_delta": removed_delta,
            "extra_delta": extra_delta,
            "recommendation_flags": {
                "can_pilot_initiatives": can_pilot_initiatives,
                "initiative_command_blocked": initiative_command_blocked,
                "has_new_initiative_capability": bool(has_new_initiative_capability),
            },
        },
    }


def _build_migration_wizard_payload(
    root: Path,
    manifest_path: Path,
    state_path: Path,
) -> dict[str, Any]:
    manifest_obj = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest_obj)
    state = _load_json_optional(state_path, default={})
    state_pack = str(state.get("current_pack_version", "0.0.0"))
    migration_pending = bool(state.get("migration_pending", False))
    migration_file = state.get("last_migration_file")

    migration_report, _ = _load_last_migration_report(root, state_path)

    migration_status = run_migration_status(root=root, manifest_path=manifest_path, state_path=state_path, strict=False)
    steps = migration_report.get("steps", []) if migration_report else []
    if not steps and migration_status.get("migration_needed"):
        steps = _extract_migration_steps(manifest_obj, migration_status["state_pack_version"], migration_status["pack_version"])

    workflow = _build_workflow_profile(root)
    workflow["migration_pending"] = migration_pending
    if not workflow["deployed_csk_commands"]:
        workflow["deployed_csk_commands"] = []

    recommendations = [
        _build_wizard_step_recommendation(step, workflow) for step in steps
    ]
    mandatory = [r for r in recommendations if r["required"] and r["status"] != "ready"]
    recommended = [r for r in recommendations if (not r["required"]) and r["status"] != "ready"]
    optional = [r for r in recommendations if not r["required"] and r["status"] == "ready"]

    transition = _build_wizard_transition_plan(workflow)

    command_gap: list[str] = []
    command_profile: dict[str, Any] = {
        "source_commands": [],
        "deployed_before": [],
        "deployed_after": [],
        "command_delta": {
            "added": [],
            "removed": [],
            "extra": [],
        },
    }
    if workflow["deployed_csk_commands_error"]:
        command_gap.append(
            f"deployed csk command surface parse issue: {workflow['deployed_csk_commands_error']}"
        )
    else:
        source_commands = set()
        if isinstance(migration_report, dict):
            surface = migration_report.get("command_surface")
            if isinstance(surface, dict):
                source_commands = _safe_command_set(surface.get("expected_commands"))
                command_profile["source_commands"] = sorted(source_commands)
                command_profile["deployed_before"] = sorted(
                    _safe_command_set(surface.get("deployed_before"))
                )
                command_profile["deployed_after"] = sorted(
                    _safe_command_set(surface.get("deployed_after"))
                )
                delta = surface.get("command_delta", {})
                if isinstance(delta, dict):
                    command_profile["command_delta"]["added"] = sorted(_safe_command_set(delta.get("added")))
                    command_profile["command_delta"]["removed"] = sorted(
                        _safe_command_set(delta.get("removed"))
                    )
                    command_profile["command_delta"]["extra"] = sorted(
                        _safe_command_set(delta.get("extra"))
                    )
        if source_commands:
            missing_in_deployed = sorted(source_commands - set(workflow["deployed_csk_commands"]))
            if missing_in_deployed:
                command_gap.append(
                    f"deployed csk.py currently missing parser entries from source migration snapshot: "
                    f"{', '.join(missing_in_deployed)}"
                )
            extra_in_deployed = sorted(set(workflow["deployed_csk_commands"]) - source_commands)
            if extra_in_deployed:
                command_gap.append(
                    f"deployed csk.py has parser entries not present in migration snapshot: "
                    f"{', '.join(extra_in_deployed)}"
                )
            if not command_profile["deployed_after"]:
                command_profile["deployed_after"] = sorted(workflow["deployed_csk_commands"])
        if not source_commands:
            command_profile["deployed_after"] = sorted(workflow["deployed_csk_commands"])
            if workflow["deployed_csk_commands_error"]:
                command_gap.append(
                    "command surface snapshot is unavailable; run `csk-sync migration-wizard` after refresh for a concrete diff."
                )

    return {
        "mode": "migration-wizard",
        "generated_at": _iso_now(),
        "source_pack_version": manifest_pack,
        "state_pack_version": state_pack,
        "migration_pending": migration_pending,
        "migration_file": migration_file,
        "migration_steps_count": len(steps),
        "migration_steps": [s.get("id") for s in steps],
        "migration_status": migration_status,
        "workflow_signature": workflow,
        "command_surface": {
            "deployed_csk_commands": workflow["deployed_csk_commands"],
            "command_profile": command_profile,
            "command_gaps": command_gap,
        },
        "assistant_coaching": _build_migration_adoption_coaching(
            state_pack=state_pack,
            manifest_pack=manifest_pack,
            steps=steps,
            workflow=workflow,
            command_profile=command_profile,
        ),
        "recommendations": {
            "mandatory": mandatory,
            "recommended": recommended,
            "optional": optional,
        },
        "transition_plan": transition,
    }


def _write_migration_wizard_markdown(
    root: Path,
    payload: dict[str, Any],
) -> tuple[Path, Path]:
    out = _ensure_report_dir(root)
    stamp = _now_stamp()
    json_path = out / f"csk-sync-migration-wizard-{stamp}.json"
    md_path = out / f"csk-sync-wizard-{stamp}.md"

    _write_json(json_path, payload)

    lines = [
        "# CSK migration wizard",
        "",
        f"Generated: {payload.get('generated_at')}",
        f"Migration pending: {payload.get('migration_pending')}",
        f"State pack version: {payload.get('state_pack_version')}",
        f"Source pack version: {payload.get('source_pack_version')}",
        f"Migration file: {payload.get('migration_file') or 'N/A'}",
        "",
        "## Workflow compatibility snapshot",
        f"- Modules: {payload['workflow_signature']['module_count']}",
        f"- Module tasks: {payload['workflow_signature']['task_count']}",
        f"- Initiative artifacts: {payload['workflow_signature']['initiative_count']}",
        f"- Legacy tasks without `plan.summary.md`: {payload['workflow_signature']['tasks_without_plan_summary']}",
        f"- Legacy tasks without `user_acceptance.md`: {payload['workflow_signature']['tasks_without_user_acceptance']}",
        f"- Initiatives without summary: {payload['workflow_signature']['initiatives_missing_summary']}",
        f"- Initiatives without status: {payload['workflow_signature']['initiatives_missing_status']}",
        "",
        "## Migration status snapshot",
    ]
    for reason in payload["migration_status"].get("reasons", []):
        lines.append(f"- {reason}")
    lines += ["", "## Command surface profile", ""]
    profile = payload["command_surface"].get("command_profile", {})
    if profile:
        lines.append(f"- source commands: {len(profile.get('source_commands', []))}")
        lines.append(f"- deployed before: {len(profile.get('deployed_before', []))}")
        lines.append(f"- deployed after: {len(profile.get('deployed_after', []))}")
        delta = profile.get("command_delta", {})
        if isinstance(delta, dict):
            if delta.get("added"):
                lines.append(f"- added by migration: {len(delta.get('added', []))}")
            if delta.get("removed"):
                lines.append(f"- removed by migration: {len(delta.get('removed', []))}")
            if delta.get("extra"):
                lines.append(f"- extra/unknown commands: {len(delta.get('extra', []))}")
        lines.append("")

    lines += ["## Recommended execution strategy", f"- strategy: {payload['transition_plan']['strategy']}", ""]
    for phase in payload["transition_plan"]["phases"]:
        lines.append(f"### Phase {phase['phase']}: {phase['name']}")
        lines.append(f"- goal: {phase['goal']}")
        for command in phase["commands"]:
            lines.append(f"  - {command}")
        lines.append("")

    lines += ["## Mandatory actions", ""]
    for rec in payload["recommendations"]["mandatory"]:
        lines.append(f"- [{rec['id']}] {rec['title']} ({rec['scope']})")
        lines.append(f"  - status: {rec['status']}")
        lines.append(f"  - {rec['summary']}")
        for action in rec.get("commands", []):
            lines.append(f"  - {action}")
        for note in rec.get("risk_notes", []):
            lines.append(f"  - note: {note}")
        lines.append("")

    lines += ["## Optional / recommended follow-up", ""]
    for rec in payload["recommendations"]["recommended"]:
        lines.append(f"- [{rec['id']}] {rec['title']}")
        lines.append(f"  - status: {rec['status']}")
        lines.append(f"  - transition: {rec['transition']}")
        lines.append("")

    if payload["command_surface"].get("command_gaps"):
        lines += [
            "## Command surface gaps",
            *[f"- {i}" for i in payload["command_surface"].get("command_gaps", [])],
            "",
        ]

    coaching = payload.get("assistant_coaching", {})
    if coaching:
        lines += ["## AI migration coaching", ""]
        transition = coaching.get("pack_transition", {})
        lines.append(
            f"- Pack transition: {transition.get('from_pack')} -> {transition.get('to_pack')}"
        )
        lines.append(f"- Recommended profile: {coaching.get('recommended_profile')}")
        lines.append(f"- Source has initiative commands: {transition.get('source_has_initiative')}")
        lines.append(f"- Deployed has initiative commands: {transition.get('deployed_has_initiative')}")
        lines.append("")

        lines += ["### New features in this transition", ""]
        for feature in coaching.get("new_features", []):
            lines.append(f"- [{feature.get('id')}] {feature.get('title')} ({'required' if feature.get('required') else 'optional'})")
            if feature.get("summary"):
                lines.append(f"  - {feature.get('summary')}")
            if feature.get("scope"):
                lines.append(f"  - scope: {feature.get('scope')}")
            if feature.get("actions"):
                lines.append("  - actions:")
                for act in feature.get("actions", []):
                    lines.append(f"    - {act}")
            if feature.get("docs"):
                lines.append(f"  - docs: {feature.get('docs')}")
            lines.append("")

        lines += ["### Adoption profiles", ""]
        for profile in coaching.get("adoption_profiles", []):
            lines.append(f"- {profile.get('name')}: {profile.get('applies_when')}")
            lines.append(f"  - goal: {profile.get('goal')}")
            lines.append(f"  - condition: {profile.get('condition')}")
            lines.append("  - command plan:")
            for command in profile.get("commands", []):
                lines.append(f"    - {command}")
            if profile.get("risk"):
                lines.append(f"  - risk: {profile.get('risk')}")
            lines.append("")

        if coaching.get("risk_blockers"):
            lines += ["### Risks before profile switch", ""]
            for item in coaching.get("risk_blockers", []):
                lines.append(f"- {item}")
            lines.append("")

        lines += ["### First actions for AI assistant", ""]
        for command in coaching.get("first_steps", []):
            lines.append(f"- {command}")
        lines.append("")

        if coaching.get("ai_prompt_starters"):
            lines += ["### Ready-to-use AI prompts", ""]
            for item in coaching.get("ai_prompt_starters", []):
                lines.append(f"- {item}")
            lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _write_csk_update_session_markdown(
    root: Path,
    payload: dict[str, Any],
) -> tuple[Path, Path]:
    out = _ensure_report_dir(root)
    stamp = _now_stamp()
    json_path = out / f"csk-update-session-{stamp}.json"
    md_path = out / f"csk-update-session-{stamp}.md"

    _write_json(json_path, payload)

    lines = [
        "# CSK update session",
        "",
        f"Run started: {payload.get('started_at')}",
        f"Source: {payload.get('source_url')}@{payload.get('source_ref')}",
        f"Pack: {payload.get('state_pack_version_before')} -> {payload.get('pack_version')}",
        f"Pack after: {payload.get('state_pack_version_after', 'unknown')}",
        f"Mode: {payload.get('mode')}",
        f"Success: {payload.get('success')}",
        "",
        "## Update status",
        f"- plan: {'ok' if payload.get('plan_success') else 'failed'} ({payload.get('plan_report')})",
        f"- apply/migrate: {'ok' if payload.get('apply_success') else 'failed'} ({payload.get('apply_report')})",
        f"- migration pending after apply: {payload.get('migration_pending_after', False)}",
        f"- state pack after: {payload.get('state_pack_version_after', 'unknown')}",
    ]

    if payload.get("conflicts"):
        lines.append(f"- conflicts: {payload.get('conflicts')}")
    if payload.get("plan_checklist"):
        lines.append(f"- Plan checklist: {payload.get('plan_checklist')}")
    if payload.get("apply_checklist"):
        lines.append(f"- Apply checklist: {payload.get('apply_checklist')}")
    if payload.get("migration_status_report"):
        lines.append(f"- Migration status report: {payload.get('migration_status_report')}")
    if payload.get("wizard_report"):
        lines.append(f"- Migration wizard report: {payload.get('wizard_report')}")

    migration_status = payload.get("migration_status") or {}
    lines += [
        "",
        "## Migration status",
        f"- Pending: {migration_status.get('pending', False)}",
        f"- Pending reasons: {len(migration_status.get('reasons', []))}",
    ]
    for reason in migration_status.get("reasons", []):
        lines.append(f"  - {reason}")

    coaching = payload.get("assistant_coaching", {})
    if coaching:
        transition = coaching.get("pack_transition", {})
        lines += [
            "",
            "## AI coaching for this transition",
            f"- Pack transition: {transition.get('from_pack')} -> {transition.get('to_pack')}",
            f"- Recommended profile: {coaching.get('recommended_profile')}",
            f"- Source has initiative commands: {transition.get('source_has_initiative')}",
            f"- Deployed has initiative commands: {transition.get('deployed_has_initiative')}",
            "- Immediate first steps:",
        ]
        for step in coaching.get("first_steps", []):
            lines.append(f"  - {step}")

    if payload.get("next_actions"):
        lines += [
            "",
            "## Recommended project actions",
        ]
        for action in payload.get("next_actions", []):
            lines.append(f"- {action}")

    if payload.get("command_surface"):
        surface = payload["command_surface"]
        lines += [
            "",
            "## Command surface snapshot",
            f"- expected commands: {len(surface.get('expected_commands', []))}",
            f"- deployed before: {len(surface.get('deployed_before', []))}",
            f"- deployed after: {len(surface.get('deployed_after', []))}",
        ]

    if surface := payload.get("command_surface"):
        if surface.get("source_probe_mode"):
            lines.append(f"- source probe mode: {surface.get('source_probe_mode')}")
        if surface.get("deployed_probe_mode_before"):
            lines.append(f"- deployed probe mode before: {surface.get('deployed_probe_mode_before')}")
        if surface.get("deployed_probe_mode_after"):
            lines.append(f"- deployed probe mode after: {surface.get('deployed_probe_mode_after')}")
        if surface.get("source_probe_error"):
            lines.append(f"- source probe error: {surface.get('source_probe_error')}")
        if surface.get("deployed_probe_error_before"):
            lines.append(f"- deployed probe error before: {surface.get('deployed_probe_error_before')}")
        if surface.get("deployed_probe_error_after"):
            lines.append(f"- deployed probe error after: {surface.get('deployed_probe_error_after')}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _build_post_update_plan(payload: dict[str, Any], migration_status: dict[str, Any]) -> list[str]:
    migration_file = migration_status.get("last_migration_file")
    migration_file_clause = (
        f" --migration-file {migration_file}"
        if migration_file
        else " --migration-file <migration-report-path>"
    )
    coaching = payload.get("assistant_coaching", {})

    actions = [
        "python tools/csk/sync_upstream.py migration-status --migration-strict",
        "python tools/csk/sync_upstream.py migration-wizard",
    ]
    if coaching.get("needs_task_artifact_reconcile", False):
        actions.append("python tools/csk/csk.py reconcile-task-artifacts --strict")
    if coaching.get("needs_initiative_artifact_reconcile", False):
        actions.append("python tools/csk/csk.py reconcile-initiative-artifacts --strict")
    if coaching.get("should_validate", False):
        actions.append("python tools/csk/csk.py validate --all --strict")

    if migration_status.get("pending"):
        actions.insert(
            2,
            "python tools/csk/sync_upstream.py migration-ack --migration-by <name> --migration-notes \"...\""
            + migration_file_clause,
        )

    if coaching.get("first_steps"):
        actions = list(dict.fromkeys(actions + list(coaching["first_steps"])))

    if coaching.get("summary_note"):
        actions.insert(0, f"[Transition] {coaching['summary_note']}")

    return actions


def run_csk_update(
    root: Path,
    source_url: str,
    source_ref: str,
    manifest_path: Path,
    overlay_root: Path,
    state_path: Path,
    decision_path: Path,
    approve_decision: bool,
    verify: bool,
    confidence_threshold: float,
    allow_dirty: bool,
    run_postchecks: bool = True,
) -> dict[str, Any]:
    manifest_obj = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest_obj)
    state = _load_json_optional(state_path, default={})
    state_pack = str(state.get("current_pack_version", "0.0.0"))

    session: dict[str, Any] = {
        "mode": "csk-update",
        "started_at": _now_stamp(),
        "source_url": source_url,
        "source_ref": source_ref,
        "pack_version": manifest_pack,
        "state_pack_version_before": state_pack,
        "success": False,
        "steps": ["plan", "apply", "postchecks"],
        "conflicts": [],
        "plan_success": False,
        "apply_success": False,
        "plan_checklist": None,
        "apply_checklist": None,
        "migration_status": {},
        "migration_status_report": None,
        "state_pack_version_after": None,
        "migration_pending_after": False,
        "wizard_report": None,
        "wizard_markdown": None,
        "wizard": {},
        "assistant_coaching": {},
        "migration_report": None,
        "migration_checklist": None,
        "approved_decision": None,
        "next_actions": [],
        "command_surface": {},
    }

    plan_report = run_plan(
        root=root,
        source_url=source_url,
        source_ref=source_ref,
        manifest_path=manifest_path,
        state_path=state_path,
        top_candidates=DEFAULT_TOP_CANDIDATES,
    )
    plan_path = _save_report(root, plan_report)
    session["plan_report"] = str(plan_path)
    session["plan_success"] = bool(plan_report.get("success"))
    if not session["plan_success"]:
        session["success"] = False
        session["conflicts"].append("plan_failed")
        session["finished_at"] = _now_stamp()
        session["plan_checklist"] = plan_report.get("checklist")
        return _finalize_csk_update_session(root, session)

    if plan_report.get("checklist"):
        session["plan_checklist"] = plan_report.get("checklist")

    apply_report = run_apply_or_migrate(
        mode="migrate",
        root=root,
        source_url=source_url,
        source_ref=source_ref,
        manifest_path=manifest_path,
        overlay_root=overlay_root,
        state_path=state_path,
        decision_path=decision_path,
        approve_decision=approve_decision,
        verify=verify,
        confidence_threshold=confidence_threshold,
        allow_dirty=allow_dirty,
        run_postchecks=False,
    )
    apply_path = _save_report(root, apply_report)
    session["apply_report"] = str(apply_path)
    session["apply_success"] = bool(apply_report.get("success"))
    if not session["apply_success"]:
        session["success"] = False
        session["conflicts"].append("apply_failed")
        session["finished_at"] = _now_stamp()
        session["apply_checklist"] = apply_report.get("checklist")
        if apply_report.get("command_surface"):
            session["command_surface"] = apply_report["command_surface"]
        return _finalize_csk_update_session(root, session)

    if apply_report.get("checklist"):
        session["apply_checklist"] = apply_report.get("checklist")
    if apply_report.get("command_surface"):
        session["command_surface"] = apply_report["command_surface"]

    state_after = _load_json_optional(state_path, default={})
    session["state_pack_version_after"] = str(state_after.get("current_pack_version", "0.0.0"))
    session["migration_pending_after"] = bool(state_after.get("migration_pending", False))

    if run_postchecks:
        migration_status = run_migration_status(
            root=root,
            manifest_path=manifest_path,
            state_path=state_path,
            strict=False,
        )
        migration_status_path = _save_report(root, migration_status)
        session["migration_status_report"] = str(migration_status_path)
        session["migration_status"] = migration_status

        wizard_report = run_migration_wizard(root=root, manifest_path=manifest_path, state_path=state_path)
        wizard_path = _save_report(root, wizard_report)
        session["wizard_report"] = str(wizard_path)
        session["wizard"] = wizard_report

        coaching = wizard_report.get("assistant_coaching", {})
        if coaching:
            session["assistant_coaching"] = coaching

        if wizard_report.get("command_surface"):
            session["command_surface"] = wizard_report["command_surface"]

        session["next_actions"] = _build_post_update_plan(wizard_report, migration_status)
        if migration_status.get("pending"):
            session["conflicts"].append("migration_pending")
    else:
        session["next_actions"] = ["Run migration-status and migration-wizard manually after this session"]

    if apply_report.get("migration_report"):
        session["migration_report"] = apply_report.get("migration_report")
    if apply_report.get("migration_checklist"):
        session["migration_checklist"] = apply_report.get("migration_checklist")
    if apply_report.get("approved_decision"):
        session["approved_decision"] = apply_report.get("approved_decision")

    session["success"] = True
    session["finished_at"] = _now_stamp()
    return _finalize_csk_update_session(root, session)


def _finalize_csk_update_session(root: Path, session: dict[str, Any]) -> dict[str, Any]:
    session_json, session_md = _write_csk_update_session_markdown(root, session)
    session["session_report"] = str(session_json)
    session["session_markdown"] = str(session_md)
    return session


def run_migration_wizard(
    root: Path,
    manifest_path: Path,
    state_path: Path,
) -> dict[str, Any]:
    payload = _build_migration_wizard_payload(root, manifest_path, state_path)
    wizard_json, wizard_md = _write_migration_wizard_markdown(root, payload)
    payload["wizard_report"] = str(wizard_json)
    payload["wizard_markdown"] = str(wizard_md)
    payload["mode"] = "migration-wizard"
    payload["success"] = True
    payload["finished_at"] = _now_stamp()
    return payload


def run_migration_ack(
    root: Path,
    migration_file: str,
    state_path: Path,
    by: str,
    notes: str,
) -> dict[str, Any]:
    if not migration_file:
        raise SyncError("migration-ack requires --migration-file.")
    path = _resolve_migration_file(root, migration_file)
    if path is None:
        raise SyncError(f"migration file does not exist: {migration_file!r}")

    raw = _load_json(path)
    if not isinstance(raw, dict):
        raise SyncError("migration report must be JSON object.")

    state = _load_json_optional(state_path, default={})
    ack = {
        "migration_file": str(path),
        "acknowledged_by": by,
        "acknowledged_at": _iso_now(),
        "notes": notes,
        "migration_id": raw.get("migration_id"),
    }
    ack_path = path.with_suffix(path.suffix + ".ack.json")
    _write_json(ack_path, ack)

    state["migration_pending"] = False
    state["last_migration_file"] = str(path)
    state["last_migration_ack_file"] = str(ack_path)
    state["migration_acknowledged_by"] = by
    state["migration_acknowledged_at"] = _iso_now()
    _write_json(state_path, state)

    report: dict[str, Any] = {
        "mode": "migration-ack",
        "started_at": _now_stamp(),
        "migration_file": str(path),
        "ack_file": str(ack_path),
        "ack_by": by,
        "notes": notes,
        "success": True,
        "finished_at": _now_stamp(),
    }
    return report


def run_dry_run(
    root: Path,
    source_url: str,
    source_ref: str,
    manifest_path: Path,
) -> dict[str, Any]:
    items = _load_manifest(manifest_path)
    manifest_obj = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest_obj)
    report: dict[str, Any] = {
        "source_url": source_url,
        "source_ref": source_ref,
        "mode": "dry-run",
        "started_at": _now_stamp(),
        "pack_version": manifest_pack,
        "results": [],
        "backup_dir": None,
        "verify_errors": [],
        "success": False,
    }

    with tempfile.TemporaryDirectory(prefix="csk-upstream-") as tmp:
        source_dir = Path(tmp) / "source"
        source_commit = _clone_source(source_url, source_ref, source_dir)
        report["source_commit"] = source_commit

        for item in items:
            rel = _safe_rel(item.path)
            src = source_dir / rel
            dst = root / rel
            result = {
                "path": item.path,
                "source_exists": src.exists(),
                "destination_exists": dst.exists(),
                "action": "replace" if src.exists() else "skip",
                "backup": None,
                "merge_mode": item.merge_mode,
            }
            if item.required and not src.exists():
                raise SyncError(f"required path missing in source repository: {item.path}")
            report["results"].append(result)

    report["finished_at"] = _now_stamp()
    report["success"] = True
    return report


def run_plan(
    root: Path,
    source_url: str,
    source_ref: str,
    manifest_path: Path,
    state_path: Path,
    top_candidates: int,
) -> dict[str, Any]:
    items = _load_manifest(manifest_path)
    manifest_obj = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest_obj)
    dirty_paths = _git_dirty_paths(root, items)
    state = _load_json_optional(state_path, default={})
    state_pack = str(state.get("current_pack_version", "0.0.0"))
    candidates = _build_backup_candidates(root, items, source_ref)
    decision_template = _write_decision_template(
        root=root,
        candidates=candidates,
        source_url=source_url,
        source_ref=source_ref,
        top_candidates=top_candidates,
    )

    report: dict[str, Any] = {
        "source_url": source_url,
        "source_ref": source_ref,
        "pack_version": manifest_pack,
        "state_pack_version": state_pack,
        "mode": "plan",
        "started_at": _now_stamp(),
        "state": state,
        "candidate_count": len(candidates),
        "candidate_table": candidates[:top_candidates],
        "decision_template": str(decision_template),
        "dirty_paths": dirty_paths,
        "warnings": [],
        "success": True,
    }

    if dirty_paths:
        report["warnings"].append(
            "Dirty worktree detected on synced paths. apply/migrate will be blocked unless --allow-dirty is set."
        )

    if _version_cmp(manifest_pack, state_pack) > 0:
        report["warnings"].append(
            "Manifest pack version is newer than state version. After apply, migration checklist and ack may be required."
        )
        migration_steps = _extract_migration_steps(manifest_obj, state_pack, manifest_pack)
        if migration_steps:
            report["planned_migration_steps"] = [step.get("id") for step in migration_steps]
            report["planned_migration_count"] = len(migration_steps)

    if not candidates:
        checklist = _write_checklist(
            root,
            "CSK migration requires manual backup decision",
            [
                "No backup candidates were found under .csk-app/backups/csk-sync-*.",
                "Run AI assistant to inspect current files and generate decision JSON.",
                "Set selected_backup to null, provide rationale, and keep confidence below threshold if uncertain.",
            ],
        )
        report["warnings"].append("No backup candidates found.")
        report["checklist"] = str(checklist)

    report["finished_at"] = _now_stamp()
    return report


def run_apply_or_migrate(
    mode: str,
    root: Path,
    source_url: str,
    source_ref: str,
    manifest_path: Path,
    overlay_root: Path,
    state_path: Path,
    decision_path: Path,
    approve_decision: bool,
    verify: bool,
    confidence_threshold: float,
    allow_dirty: bool,
    run_postchecks: bool = False,
) -> dict[str, Any]:
    if not approve_decision:
        raise SyncError("apply/migrate requires --approve-decision.")

    manifest_obj = _load_manifest_payload(manifest_path)
    manifest_pack = _manifest_pack_version(manifest_obj)
    prior_state = _load_json_optional(state_path, default={})
    prior_pack = str(prior_state.get("current_pack_version", "0.0.0"))

    items = _load_manifest(manifest_path)
    decision_raw = _validate_decision_file(decision_path)

    selected_raw = decision_raw.get("selected_backup")
    confidence = float(decision_raw.get("confidence", 0.0))
    rationale = decision_raw.get("rationale", "")
    selected_backup = _resolve_backup_path(root, selected_raw)
    if selected_raw is not None and selected_backup is None:
        raise SyncError(
            "Decision selected_backup does not resolve to an existing backup directory: "
            f"{selected_raw!r}."
        )

    dirty_paths = _git_dirty_paths(root, items)

    report: dict[str, Any] = {
        "source_url": source_url,
        "source_ref": source_ref,
        "pack_version": manifest_pack,
        "state_pack_version": prior_pack,
        "mode": mode,
        "started_at": _now_stamp(),
        "results": [],
        "overlay_results": [],
        "backup_dir": None,
        "preflight_errors": [],
        "verify_errors": [],
        "post_verify_blocked": False,
        "success": False,
        "decision_file": str(decision_path),
        "decision": {
            "selected_backup": selected_raw,
            "resolved_backup": None if selected_backup is None else str(selected_backup),
            "confidence": confidence,
            "rationale": rationale,
            "approved_by_human": True,
            "approved_at": _iso_now(),
        },
        "dirty_paths": dirty_paths,
        "checklist": None,
        "conflicts": [],
        "overlay_root": str(overlay_root),
        "migration_report": None,
        "migration_checklist": None,
        "migration_pending": False,
        "migration_status": {},
        "migration_status_report": None,
        "wizard_report": None,
        "wizard_markdown": None,
        "assistant_coaching": {},
        "next_actions": [],
    }
    migration_steps = _extract_migration_steps(manifest_obj, prior_pack, manifest_pack)
    report["migration_needed"] = bool(migration_steps)
    report["migration_step_count"] = len(migration_steps)
    migration_report: Path | None = None
    migration_checklist: Path | None = None
    report["rollback"] = {
        "performed": False,
        "manifest": None,
        "errors": [],
    }

    history_path = state_path.parent / "history.jsonl"

    if dirty_paths and not allow_dirty:
        checklist = _write_checklist(
            root,
            "Dirty worktree blocks csk apply/migrate",
            [
                "Commit or stash local changes on sync paths.",
                "Or rerun with --allow-dirty if you intentionally accept overwrite risk.",
            ],
        )
        report["checklist"] = str(checklist)
        report["conflicts"].append("dirty_worktree")
        report["finished_at"] = _now_stamp()
        report_path = _save_report(root, report)
        report["_saved_report_path"] = str(report_path)
        _append_history(
            history_path,
            mode,
            source_url,
            source_ref,
            None,
            None if selected_backup is None else str(selected_backup),
            confidence,
            "blocked",
            report["conflicts"],
            report_path,
            decision_path,
            migration_report,
        )
        return report

    if selected_backup is None or confidence < confidence_threshold:
        checklist = _write_checklist(
            root,
            "Low-confidence backup decision",
            [
                "AI assistant must select a valid backup directory under .csk-app/backups or provide stronger rationale.",
                f"Current selected_backup={selected_raw!r}, confidence={confidence:.2f}, required >= {confidence_threshold:.2f}.",
                "Review candidate_table from plan mode and create updated decision JSON.",
            ],
        )
        report["checklist"] = str(checklist)
        report["conflicts"].append("low_confidence_decision")
        report["finished_at"] = _now_stamp()
        report_path = _save_report(root, report)
        report["_saved_report_path"] = str(report_path)
        _append_history(
            history_path,
            mode,
            source_url,
            source_ref,
            None,
            None if selected_backup is None else str(selected_backup),
            confidence,
            "blocked",
            report["conflicts"],
            report_path,
            decision_path,
            migration_report,
        )
        return report

    preflight_errors = _preflight_dependencies(root, items)
    if preflight_errors:
        report["preflight_errors"] = preflight_errors
        report["conflicts"].append("preflight_blocked")
        checklist = _write_checklist(
            root,
            "Preflight checks blocked csk apply/migrate",
            [
                "Install missing runtime dependencies and rerun apply/migrate.",
                *preflight_errors,
            ],
        )
        report["checklist"] = str(checklist)
        report["finished_at"] = _now_stamp()
        report_path = _save_report(root, report)
        report["_saved_report_path"] = str(report_path)
        _append_history(
            history_path,
            mode,
            source_url,
            source_ref,
            None,
            None if selected_backup is None else str(selected_backup),
            confidence,
            "blocked",
            report["conflicts"],
            report_path,
            decision_path,
            migration_report,
        )
        return report

    with tempfile.TemporaryDirectory(prefix="csk-upstream-") as tmp:
        source_dir = Path(tmp) / "source"
        source_commit = _clone_source(source_url, source_ref, source_dir)
        report["source_commit"] = source_commit

        (
            overlay_bootstrap_actions,
            overlay_apply_actions,
            blockers,
            backup_fallback_paths,
            existing_overlay_paths,
            bootstrap_overlay_paths,
        ) = _plan_overlay_actions(
            root=root,
            source_root=source_dir,
            overlay_root=overlay_root,
            items=items,
            selected_backup=selected_backup,
        )
        report["overlay_bootstrap_needed"] = bool(overlay_bootstrap_actions)
        report["overlay_bootstrap_paths"] = bootstrap_overlay_paths
        report["overlay_existing_paths"] = existing_overlay_paths
        report["backup_fallback_paths"] = backup_fallback_paths
        if blockers:
            report["conflicts"].extend(blockers)

        if report["conflicts"]:
            checklist = _write_checklist(
                root,
                "CSK migrate conflicts",
                [
                    "Resolve listed conflicts before rerunning apply/migrate.",
                    "For manual_only paths, complete manual migration and keep them out of auto-apply scope.",
                    "For replace_core paths, remove overlay/local divergence or change merge_mode in manifest.",
                ],
            )
            report["checklist"] = str(checklist)
            report["finished_at"] = _now_stamp()
            report_path = _save_report(root, report)
            report["_saved_report_path"] = str(report_path)
            _append_history(
                history_path,
                mode,
                source_url,
                source_ref,
                source_commit,
                None if selected_backup is None else str(selected_backup),
                confidence,
                "blocked",
                report["conflicts"],
                report_path,
                decision_path,
                migration_report,
            )
            return report

        backup_dir = root / ".csk-app" / "backups" / f"csk-sync-{_now_stamp()}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        report["backup_dir"] = str(backup_dir)
        backup_manifest_path = backup_dir / "backup_manifest.json"
        pre_state: list[dict[str, Any]] = []
        seen_snapshot: set[str] = set()

        try:
            for item in items:
                rel = _safe_rel(item.path)
                upstream_path = source_dir / rel
                if upstream_path.exists():
                    _snapshot_state(root, root / rel, backup_dir, pre_state, seen_snapshot)
            for action in overlay_apply_actions:
                _snapshot_state(
                    root,
                    root / _safe_rel(str(action["path"])),
                    backup_dir,
                    pre_state,
                    seen_snapshot,
                )
            for action in overlay_bootstrap_actions:
                overlay_target = Path(action["overlay_target"])
                _snapshot_state(root, overlay_target, backup_dir, pre_state, seen_snapshot)

            if pre_state:
                _write_json(
                    backup_manifest_path,
                    {
                        "created_at": _iso_now(),
                        "source_url": source_url,
                        "source_ref": source_ref,
                        "mode": mode,
                        "items": pre_state,
                    },
                )
                report["backup_manifest"] = str(backup_manifest_path)

            if overlay_bootstrap_actions:
                report["overlay_results"].extend(_apply_overlay_actions(root, overlay_bootstrap_actions))
            report["results"] = _apply_core_sync(root, source_dir, items, backup_dir)
            if overlay_apply_actions:
                report["overlay_results"].extend(_apply_overlay_actions(root, overlay_apply_actions))

            source_csk = source_dir / "tools" / "csk" / "csk.py"
            deployed_csk = root / "tools" / "csk" / "csk.py"
            expected_commands, expected_error, expected_probe_mode = _probe_parser_commands_detailed(
                source_csk, source_dir
            )
            deployed_commands_before, deployed_error_before, deployed_probe_mode_before = _probe_parser_commands_detailed(
                deployed_csk, root
            )
            deployed_commands_after = set(deployed_commands_before)
            deployed_error_after = deployed_error_before
            deployed_probe_mode_after = deployed_probe_mode_before

            if expected_error:
                report["verify_errors"].append(
                    f"source csk.py -h probe failed before command-surface check: {expected_error}"
                )
            if deployed_error_before:
                report["verify_errors"].append(
                    f"deployed csk.py -h probe failed before command-surface check: {deployed_error_before}"
                )

            if expected_commands and not expected_error:
                missing_from_deployed = expected_commands - deployed_commands_before
                if missing_from_deployed:
                    _replace_path(source_csk, deployed_csk)
                    report["overlay_results"].append(
                        {
                            "path": "tools/csk/csk.py",
                            "action": "command-surface-restore",
                            "restored_from": str(source_csk),
                            "missing_commands": sorted(missing_from_deployed),
                            "probe_mode_before": deployed_probe_mode_before,
                        }
                    )
                    repaired_commands, repaired_error, repaired_mode = _probe_parser_commands_detailed(
                        deployed_csk, root
                    )
                    deployed_commands_after = repaired_commands
                    deployed_error_after = repaired_error
                    deployed_probe_mode_after = repaired_mode
                    if repaired_error:
                        report["verify_errors"].append(
                            f"deployed csk.py -h probe failed after restore: {repaired_error}"
                        )
                    else:
                        still_missing = sorted(expected_commands - repaired_commands)
                        if still_missing:
                            report["verify_errors"].append(
                                "deployed csk.py is still missing commands from upstream source: "
                                + ", ".join(still_missing)
                            )

            command_surface_report: dict[str, Any] = {
                "source_file": str(source_csk),
                "expected_commands": sorted(expected_commands),
                "deployed_before": sorted(deployed_commands_before),
                "deployed_after": sorted(deployed_commands_after),
                "source_probe_error": expected_error,
                "deployed_probe_error_before": deployed_error_before,
                "deployed_probe_error_after": deployed_error_after,
                "source_probe_mode": expected_probe_mode,
                "deployed_probe_mode_before": deployed_probe_mode_before,
                "deployed_probe_mode_after": deployed_probe_mode_after,
                "command_delta": {
                    "added": sorted(deployed_commands_after - deployed_commands_before),
                    "removed": sorted(deployed_commands_before - deployed_commands_after),
                    "extra": sorted(set(deployed_commands_after) - set(expected_commands)),
                },
            }
            report["command_surface"] = command_surface_report

            if verify:
                report["verify_errors"].extend(_content_health_check(root, items))
                if report["verify_errors"]:
                    report["post_verify_blocked"] = True
                    raise SyncError("postapply content verification failed")
        except Exception as exc:  # noqa: BLE001
            try:
                if pre_state:
                    _restore_state(root, backup_dir, pre_state)
                    report["rollback"]["performed"] = True
                backup_manifest_path = backup_dir / "restore.json"
                _write_json(
                    backup_manifest_path,
                    {
                        "created_at": _iso_now(),
                        "status": "restored",
                        "error": str(exc),
                    },
                )
                report["rollback"]["manifest"] = str(backup_manifest_path)
            except Exception as rollback_exc:  # noqa: BLE001
                report["rollback"]["errors"].append(f"rollback failed: {rollback_exc}")

            report["finished_at"] = _now_stamp()
            if report.get("verify_errors"):
                report["conflicts"].append("postverify_blocked")
            else:
                report["conflicts"].append("mutation_failed")

            report_path = _save_report(root, report)
            report["_saved_report_path"] = str(report_path)
            _append_history(
                history_path,
                mode,
                source_url,
                source_ref,
                report.get("source_commit"),
                None if selected_backup is None else str(selected_backup),
                confidence,
                "failed",
                report["conflicts"],
                report_path,
                decision_path,
                migration_report,
            )
            return report

    if _version_cmp(manifest_pack, prior_pack) > 0:
        try:
            migration_report, _selected_steps, migration_checklist = _write_migration_report(
                root=root,
                source_url=source_url,
                source_ref=source_ref,
                source_commit=str(report.get("source_commit", "")),
                pack_from=prior_pack,
                pack_to=manifest_pack,
                migration_notes=(manifest_obj.get("migration_notes") or ""),
                steps=migration_steps,
                command_surface=report.get("command_surface"),
            )
            report["migration_report"] = str(migration_report)
            report["migration_checklist"] = str(migration_checklist)
            report["migration_pending"] = bool(migration_steps)
        except Exception as exc:  # noqa: BLE001
            report["conflicts"].append(f"Failed to create migration report: {exc}")
            report["migration_pending"] = False

    _write_state(
        state_path=state_path,
        source_url=source_url,
        source_ref=source_ref,
        source_commit=str(report.get("source_commit", "")),
        manifest_hash=_manifest_hash(manifest_path),
        pack_version=manifest_pack,
        migration_pending=bool(report.get("migration_pending", False)),
        migration_file=None if migration_report is None else str(migration_report),
    )

    if run_postchecks:
        migration_status = run_migration_status(
            root=root,
            manifest_path=manifest_path,
            state_path=state_path,
            strict=False,
        )
        migration_status_path = _save_report(root, migration_status)
        report["migration_status"] = migration_status
        report["migration_status_report"] = str(migration_status_path)

        wizard = run_migration_wizard(
            root=root,
            manifest_path=manifest_path,
            state_path=state_path,
        )
        report["wizard_report"] = wizard.get("wizard_report")
        report["wizard_markdown"] = wizard.get("wizard_markdown")
        report["assistant_coaching"] = wizard.get("assistant_coaching", {})
        report["next_actions"] = _build_post_update_plan(wizard, migration_status)
        if migration_status.get("pending"):
            report["conflicts"].append("migration_pending")
    else:
        report["next_actions"] = ["Run migration-status and migration-wizard manually after this session"]

    # Persist approval snapshot as immutable artifact.
    approved_decision = {
        **decision_raw,
        "selected_backup": str(selected_backup),
        "confidence": confidence,
        "rationale": rationale,
        "approved_by_human": True,
        "approved_at": _iso_now(),
        "source_url": source_url,
        "source_ref": source_ref,
    }
    approved_decision_path = _ensure_decision_dir(root) / f"decision-{_now_stamp()}-approved.json"
    _write_json(approved_decision_path, approved_decision)
    report["approved_decision"] = str(approved_decision_path)

    report["finished_at"] = _now_stamp()
    report["success"] = True
    report_path = _save_report(root, report)
    report["_saved_report_path"] = str(report_path)
    _append_history(
        history_path,
        mode,
        source_url,
        source_ref,
        report.get("source_commit"),
        None if selected_backup is None else str(selected_backup),
        confidence,
        "success",
        [],
        report_path,
        approved_decision_path,
        migration_report,
    )
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync CSK assets from upstream GitHub repository.")
    parser.add_argument(
        "mode",
        nargs="?",
        default="dry-run",
        choices=[
            "dry-run",
            "plan",
            "migrate",
            "apply",
            "migration-status",
            "migration-ack",
            "migration-wizard",
            "csk-update",
        ],
        help="Execution mode. Default is dry-run.",
    )
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help="Upstream Git URL.")
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF, help="Upstream branch or tag.")
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST,
        help="Relative path to sync manifest from repository root.",
    )
    parser.add_argument("--apply", action="store_true", help="Compatibility alias for mode=apply.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-apply verification checks.")
    parser.add_argument(
        "--skip-postchecks",
        action="store_true",
        help=(
            "Skip post-update checks after apply/migrate/csk-update "
            "(migration-status/migration-wizard/reconcile commands)."
        ),
    )
    parser.add_argument(
        "--decision-file",
        help="Decision JSON produced/filled by AI assistant. Required for apply/migrate/csk-update.",
    )
    parser.add_argument(
        "--approve-decision",
        action="store_true",
        help="Human approval gate. Required for apply/migrate/csk-update.",
    )
    parser.add_argument(
        "--migration-file",
        help="Path to migration report to acknowledge in migration-ack mode.",
    )
    parser.add_argument(
        "--migration-by",
        default="assistant",
        help="Identity that acknowledges migration status.",
    )
    parser.add_argument(
        "--migration-notes",
        default="",
        help="Notes for migration acknowledgment.",
    )
    parser.add_argument(
        "--migration-strict",
        action="store_true",
        help="In migration-status mode, return non-zero code when pending migration is unresolved.",
    )
    parser.add_argument(
        "--overlay-root",
        default=DEFAULT_OVERLAY_ROOT,
        help="Overlay root directory (relative to repo root).",
    )
    parser.add_argument(
        "--state-file",
        default=DEFAULT_STATE_FILE,
        help="State file path (relative to repo root).",
    )
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=DEFAULT_CONFIDENCE_THRESHOLD,
        help="Minimum decision confidence required for apply/migrate.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow apply/migrate when git has local modifications in synced paths.",
    )
    parser.add_argument(
        "--top-candidates",
        type=int,
        default=DEFAULT_TOP_CANDIDATES,
        help="Number of backup candidates included in plan output.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    root = Path(args.root).resolve()
    manifest_path = (root / args.manifest).resolve()
    overlay_root = (root / args.overlay_root).resolve()
    state_path = (root / args.state_file).resolve()

    mode = args.mode
    if args.apply:
        mode = "apply"

    try:
        if mode == "dry-run":
            report = run_dry_run(
                root=root,
                source_url=args.source_url,
                source_ref=args.source_ref,
                manifest_path=manifest_path,
            )
        elif mode == "plan":
            report = run_plan(
                root=root,
                source_url=args.source_url,
                source_ref=args.source_ref,
                manifest_path=manifest_path,
                state_path=state_path,
                top_candidates=max(1, args.top_candidates),
            )
        elif mode in {"apply", "migrate"}:
            if not args.decision_file:
                raise SyncError("apply/migrate requires --decision-file.")
            report = run_apply_or_migrate(
                mode=mode,
                root=root,
                source_url=args.source_url,
                source_ref=args.source_ref,
                manifest_path=manifest_path,
                overlay_root=overlay_root,
                state_path=state_path,
                decision_path=Path(args.decision_file).resolve(),
                approve_decision=args.approve_decision,
                verify=not args.skip_verify,
                confidence_threshold=args.confidence_threshold,
                allow_dirty=args.allow_dirty,
                run_postchecks=not args.skip_postchecks,
            )
        elif mode == "migration-status":
            report = run_migration_status(
                root=root,
                manifest_path=manifest_path,
                state_path=state_path,
                strict=args.migration_strict,
            )
        elif mode == "migration-ack":
            report = run_migration_ack(
                root=root,
                migration_file=args.migration_file,
                state_path=state_path,
                by=args.migration_by,
                notes=args.migration_notes,
            )
        elif mode == "migration-wizard":
            report = run_migration_wizard(
                root=root,
                manifest_path=manifest_path,
                state_path=state_path,
            )
        elif mode == "csk-update":
            if not args.decision_file:
                raise SyncError("csk-update requires --decision-file.")
            report = run_csk_update(
                root=root,
                source_url=args.source_url,
                source_ref=args.source_ref,
                manifest_path=manifest_path,
                overlay_root=overlay_root,
                state_path=state_path,
                decision_path=Path(args.decision_file).resolve(),
                approve_decision=args.approve_decision,
                verify=not args.skip_verify,
                confidence_threshold=args.confidence_threshold,
                allow_dirty=args.allow_dirty,
                run_postchecks=not args.skip_postchecks,
            )
        else:
            raise SyncError(f"Unsupported mode: {mode}")
    except Exception as exc:  # noqa: BLE001
        print(f"[csk-sync] failed: {exc}")
        return 1

    if report.get("_saved_report_path"):
        report_path = Path(str(report["_saved_report_path"]))
    else:
        report_path = _save_report(root, report)
    print(f"[csk-sync] mode={report['mode']} success={report['success']}")
    print(f"[csk-sync] report={report_path}")
    if report.get("backup_dir"):
        print(f"[csk-sync] backup={report['backup_dir']}")
    if report.get("decision_template"):
        print(f"[csk-sync] decision_template={report['decision_template']}")
    if report.get("session_markdown"):
        print(f"[csk-sync] csk_update_session={report['session_markdown']}")
    if report.get("conflicts"):
        print("[csk-sync] conflicts:")
        for conflict in report["conflicts"]:
            print(f"- {conflict}")
    if report.get("checklist"):
        print(f"[csk-sync] checklist={report['checklist']}")
    if report.get("preflight_errors"):
        print("[csk-sync] preflight errors:")
        for err in report["preflight_errors"]:
            print(f"- {err}")
    if report.get("migration_report"):
        print(f"[csk-sync] migration_report={report['migration_report']}")
    if report.get("migration_checklist"):
        print(f"[csk-sync] migration_checklist={report['migration_checklist']}")
    if report.get("migration_pending"):
        print("[csk-sync] migration_pending=true")
    if report.get("wizard_report"):
        print(f"[csk-sync] migration_wizard_report={report['wizard_report']}")
    if report.get("wizard_markdown"):
        print(f"[csk-sync] migration_wizard={report['wizard_markdown']}")
    if report.get("next_actions"):
        print("[csk-sync] recommended_next_actions:")
        for action in report["next_actions"]:
            print(f"- {action}")
    if report.get("ack_file"):
        print(f"[csk-sync] migration_ack={report['ack_file']}")
    if report.get("rollback"):
        rollback = report["rollback"]
        if rollback.get("performed"):
            print("[csk-sync] rollback executed.")
        if rollback.get("errors"):
            print("[csk-sync] rollback issues:")
            for err in rollback["errors"]:
                print(f"- {err}")
        if rollback.get("manifest"):
            print(f"[csk-sync] rollback_manifest={rollback['manifest']}")
    if report.get("verify_errors"):
        print("[csk-sync] verification errors:")
        for err in report["verify_errors"]:
            print(f"- {err}")
        return 1
    if report.get("mode") == "migration-status" and report.get("pending") and report.get("reasons"):
        print("[csk-sync] migration status: pending")
        for reason in report.get("reasons", []):
            print(f"- {reason}")
        return 1
    if not report.get("success", False):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
