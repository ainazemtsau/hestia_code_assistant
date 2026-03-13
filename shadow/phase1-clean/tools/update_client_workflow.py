from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_install_lib():
    module_path = Path(__file__).with_name("install_lib.py")
    spec = importlib.util.spec_from_file_location("shadow_phase1_install_lib_update", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load install_lib from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def update_client_workflow(workflow_root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    install_lib = _load_install_lib()
    workflow_root_real = install_lib.resolve_workflow_root(workflow_root)
    manifest_real = install_lib.resolve_manifest_path(workflow_root_real, manifest_path)
    manifest = install_lib.load_install_manifest(manifest_real)
    project_root = workflow_root_real.parent
    results = install_lib.apply_manifest(workflow_root_real, project_root, manifest)
    return {
        "mode": "update",
        "workflow_root": str(workflow_root_real),
        "project_root": str(project_root),
        "updated_assets": results,
    }


def _default_workflow_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update the managed workflow base in the parent project.")
    parser.add_argument("--workflow-root", default=None, help="Workflow checkout root. Defaults to this script's package root.")
    parser.add_argument("--manifest", default=None, help="Manifest path inside the workflow checkout.")
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    workflow_root = _default_workflow_root() if args.workflow_root is None else Path(args.workflow_root)
    manifest_path = None if args.manifest is None else Path(args.manifest)

    try:
        summary = update_client_workflow(workflow_root, manifest_path)
    except Exception as exc:  # noqa: BLE001
        print(f"[csk-update] failed: {exc}")
        return 1

    print(
        f"[csk-update] project_root={summary['project_root']} "
        f"assets={len(summary['updated_assets'])}"
    )
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
