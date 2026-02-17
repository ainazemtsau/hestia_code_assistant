from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SOURCE_URL = "https://github.com/ainazemtsau/hestia_code_assistant"
DEFAULT_SOURCE_REF = "main"
DEFAULT_MANIFEST = "tools/csk/upstream_sync_manifest.json"


@dataclass(frozen=True)
class SyncItem:
    path: str
    required: bool = True


class SyncError(RuntimeError):
    pass


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SyncError(f"Missing required file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_manifest(path: Path) -> list[SyncItem]:
    data = _load_json(path)
    items_raw = data.get("sync_paths", [])
    if not isinstance(items_raw, list) or not items_raw:
        raise SyncError("Manifest must contain non-empty array `sync_paths`.")

    items: list[SyncItem] = []
    for raw in items_raw:
        if isinstance(raw, str):
            items.append(SyncItem(path=raw, required=True))
            continue
        if not isinstance(raw, dict):
            raise SyncError("Each `sync_paths` item must be string or object.")
        path_value = raw.get("path")
        if not isinstance(path_value, str) or not path_value.strip():
            raise SyncError("`sync_paths[].path` must be non-empty string.")
        items.append(SyncItem(path=path_value, required=bool(raw.get("required", True))))
    return items


def _run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def _clone_source(source_url: str, source_ref: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    clone = _run(["git", "clone", "--depth", "1", "--branch", source_ref, source_url, str(target)])
    if clone.returncode != 0:
        raise SyncError(f"Failed to clone source repository:\n{clone.stderr.strip()}")


def _safe_rel(path: str) -> Path:
    rel = Path(path)
    if rel.is_absolute():
        raise SyncError(f"Manifest path must be relative: {path}")
    if ".." in rel.parts:
        raise SyncError(f"Manifest path cannot contain '..': {path}")
    return rel


def _copy_item(src_root: Path, dst_root: Path, rel: Path, apply: bool, backup_root: Path | None) -> dict[str, Any]:
    src = src_root / rel
    dst = dst_root / rel
    result: dict[str, Any] = {
        "path": str(rel).replace("\\", "/"),
        "source_exists": src.exists(),
        "destination_exists": dst.exists(),
        "action": "skip",
        "backup": None,
    }
    if not src.exists():
        return result

    result["action"] = "replace"
    if not apply:
        return result

    if backup_root is not None:
        try:
            backup_root.relative_to(dst)
            raise SyncError(
                f"Unsafe replacement blocked for {rel}: backup directory is nested under the destination path."
            )
        except ValueError:
            pass

    if dst.exists() and backup_root is not None:
        backup_target = backup_root / rel
        backup_target.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_dir():
            shutil.copytree(dst, backup_target, dirs_exist_ok=True)
        else:
            shutil.copy2(dst, backup_target)
        result["backup"] = str(backup_target).replace("\\", "/")

    if src.is_dir():
        if dst.exists() and not dst.is_dir():
            dst.unlink()
        dst.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return result


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
    errors: list[str] = []
    for idx, line in enumerate(header, start=2):
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"line {idx}: expected key: value")
            continue
        key, _value = line.split(":", 1)
        if not key.strip():
            errors.append(f"line {idx}: empty key")
    return errors


def _verify(root: Path, items: list[SyncItem]) -> list[str]:
    errors: list[str] = []
    for item in items:
        rel = _safe_rel(item.path)
        target = root / rel
        if item.required and not target.exists():
            errors.append(f"required path missing after sync: {item.path}")

    skills_root = root / ".agents" / "skills"
    if skills_root.exists():
        for skill_file in sorted(skills_root.glob("*/SKILL.md")):
            fm_errors = _frontmatter_errors(skill_file)
            for err in fm_errors:
                errors.append(f"{skill_file}: {err}")

    csk_py = root / "tools" / "csk" / "csk.py"
    if csk_py.exists():
        probe = _run([sys.executable, str(csk_py), "-h"], cwd=root)
        if probe.returncode != 0:
            errors.append(f"csk.py -h failed: {probe.stderr.strip() or probe.stdout.strip()}")
    return errors


def run_sync(
    root: Path,
    source_url: str,
    source_ref: str,
    manifest_path: Path,
    apply: bool,
    verify: bool,
) -> dict[str, Any]:
    items = _load_manifest(manifest_path)
    report: dict[str, Any] = {
        "source_url": source_url,
        "source_ref": source_ref,
        "mode": "apply" if apply else "dry-run",
        "started_at": _now_stamp(),
        "results": [],
        "backup_dir": None,
        "verify_errors": [],
        "success": False,
    }

    with tempfile.TemporaryDirectory(prefix="csk-upstream-") as tmp:
        source_dir = Path(tmp) / "source"
        _clone_source(source_url, source_ref, source_dir)

        backup_dir: Path | None = None
        if apply:
            backup_dir = root / ".csk-app" / "backups" / f"csk-sync-{_now_stamp()}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            report["backup_dir"] = str(backup_dir).replace("\\", "/")

        for item in items:
            rel = _safe_rel(item.path)
            result = _copy_item(source_dir, root, rel, apply=apply, backup_root=backup_dir)
            if item.required and not result["source_exists"]:
                raise SyncError(f"required path missing in source repository: {item.path}")
            report["results"].append(result)

    if verify and apply:
        report["verify_errors"] = _verify(root, items)
    report["finished_at"] = _now_stamp()
    report["success"] = len(report["verify_errors"]) == 0
    return report


def _save_report(root: Path, report: dict[str, Any]) -> Path:
    out_dir = root / ".csk-app" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"csk-sync-{_now_stamp()}.json"
    out.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    return out


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync CSK assets from upstream GitHub repository.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--source-url", default=DEFAULT_SOURCE_URL, help="Upstream Git URL.")
    parser.add_argument("--source-ref", default=DEFAULT_SOURCE_REF, help="Upstream branch or tag.")
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST,
        help="Relative path to sync manifest from repository root.",
    )
    parser.add_argument("--apply", action="store_true", help="Apply changes. Omit for dry-run.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip post-apply verification checks.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    root = Path(args.root).resolve()
    manifest_path = (root / args.manifest).resolve()

    try:
        report = run_sync(
            root=root,
            source_url=args.source_url,
            source_ref=args.source_ref,
            manifest_path=manifest_path,
            apply=args.apply,
            verify=not args.skip_verify,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[csk-sync] failed: {exc}")
        return 1

    report_path = _save_report(root, report)
    print(f"[csk-sync] mode={report['mode']} success={report['success']}")
    print(f"[csk-sync] report={report_path}")
    if report["backup_dir"]:
        print(f"[csk-sync] backup={report['backup_dir']}")
    if report["verify_errors"]:
        print("[csk-sync] verification errors:")
        for err in report["verify_errors"]:
            print(f"- {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
