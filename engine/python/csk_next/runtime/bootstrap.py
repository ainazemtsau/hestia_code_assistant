"""Bootstrap logic for CSK project initialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from csk_next.domain.state import ensure_registry
from csk_next.io.files import copy_tree, ensure_dir, write_json, write_text
from csk_next.runtime.modules import registry_detect
from csk_next.runtime.paths import Layout
from csk_next.skills.generator import generate_skills
from csk_next.runtime.time import utc_now_iso


def bundled_engine_pack_path() -> Path:
    here = Path(__file__).resolve().parent
    return here.parent / "assets" / "engine_pack"


def _ensure_local(layout: Layout) -> None:
    ensure_dir(layout.local)
    ensure_dir(layout.local / "profiles")
    ensure_dir(layout.local / "skills_override")
    ensure_dir(layout.local / "hooks")

    config_path = layout.local / "config.json"
    if not config_path.exists():
        write_json(
            config_path,
            {
                "schema_version": "1.0.0",
                "created_at": utc_now_iso(),
                "user_check_mode": "profile_optional",
            },
        )

    mcp_path = layout.local / "mcp_recommendations.json"
    if not mcp_path.exists():
        write_json(
            mcp_path,
            {
                "schema_version": "1.0.0",
                "items": [],
                "updated_at": utc_now_iso(),
            },
        )


def _ensure_app(layout: Layout) -> None:
    ensure_dir(layout.app)
    ensure_dir(layout.missions)
    ensure_dir(layout.app_logs)
    ensure_dir(layout.research)
    ensure_registry(layout.registry)
    if not layout.backlog.exists():
        write_text(layout.backlog, "")


def _ensure_engine(layout: Layout) -> None:
    if layout.engine.exists():
        return
    source = bundled_engine_pack_path()
    ensure_dir(layout.engine)
    copy_tree(source, layout.engine)


def _ensure_root_agents(layout: Layout) -> None:
    if layout.root_agents.exists():
        return
    write_text(
        layout.root_agents,
        """# AGENTS.md\n\nUse `$csk` as the single entrypoint.\n\nWorkflow phases are enforced by CLI gates.\n""",
    )


def bootstrap(layout: Layout) -> dict[str, Any]:
    _ensure_engine(layout)
    _ensure_local(layout)
    _ensure_app(layout)
    _ensure_root_agents(layout)

    generate_skills(
        engine_skills_src=layout.engine / "skills_src",
        local_override=layout.local / "skills_override",
        output_dir=layout.agents_skills,
    )

    registry = ensure_registry(layout.registry)
    if not registry["modules"]:
        detect_result = registry_detect(layout)
        registry = ensure_registry(layout.registry)
    else:
        detect_result = {"created_count": 0, "module_count": len(registry["modules"])}

    return {
        "status": "ok",
        "root": str(layout.root),
        "registry_modules": len(registry["modules"]),
        "registry_detect_created": int(detect_result.get("created_count", 0)),
        "engine_version": (layout.engine / "VERSION").read_text(encoding="utf-8").strip()
        if (layout.engine / "VERSION").exists()
        else "unknown",
    }
