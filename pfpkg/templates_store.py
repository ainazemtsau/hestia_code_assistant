"""Template loading for pf init and scaffolding."""

from __future__ import annotations

from pathlib import Path

from pfpkg.paths import detect_docpack_templates

FALLBACK_TEMPLATES = {
    "AGENTS.md": "# AGENTS.md\n\nUse pf status and pf context build before actions.\n",
    "AGENTS.module.override.md": "# AGENTS.override.md\n\nModule-specific constraints here.\n",
    "PLAN.md.template": "# Plan (module: <module_id>)\n\n## Goal\n\n",
    "KNOWLEDGE.md.template": "# Knowledge / Runbook (module: <module_id>)\n",
    "DECISIONS.md.template": "# Decisions (module: <module_id>)\n",
    "task.md.template": "# Task <task_id>\n",
    "mission_spec.md.template": "# Mission <mission_id>\n",
    "SLICES.json.template": '{\n  "version": 1,\n  "slices": []\n}\n',
    "retro.md.template": "# Retro <YYYY-MM-DD>\n",
}

SKILL_REL_PATHS = [
    "skills/pf/entrypoint/SKILL.md",
    "skills/pf/intake/SKILL.md",
    "skills/pf/planner/SKILL.md",
    "skills/pf/plan-review/SKILL.md",
    "skills/pf/executor/SKILL.md",
    "skills/pf/release/SKILL.md",
    "skills/pf/retro/SKILL.md",
]


def _local_templates_root() -> Path:
    return Path(__file__).resolve().parent / "templates"


def resolve_templates_root(repo_root: Path) -> Path | None:
    packaged = _local_templates_root()
    if packaged.exists():
        return packaged
    return detect_docpack_templates(repo_root)


def load_template(repo_root: Path, rel_path: str) -> str:
    root = resolve_templates_root(repo_root)
    if root is not None:
        source = root / rel_path
        if source.exists():
            return source.read_text(encoding="utf-8")
    if rel_path in FALLBACK_TEMPLATES:
        return FALLBACK_TEMPLATES[rel_path]
    raise FileNotFoundError(f"template not found: {rel_path}")
