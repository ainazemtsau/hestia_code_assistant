from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

SCHEMA_VERSION = 1
REVISION_PREFIX = "REV-"
WORKFLOW_ROOT_REL = Path(".csk-app") / "overlay" / "workflow"
WORKFLOW_CONFIG_REL = WORKFLOW_ROOT_REL / "config"
WORKFLOW_ASSETS_REL = WORKFLOW_ROOT_REL / "assets"
WORKFLOW_REVISIONS_REL = WORKFLOW_ROOT_REL / "revisions"
WORKFLOW_STATE_REL = WORKFLOW_ROOT_REL / "state.json"
WORKFLOW_HISTORY_REL = WORKFLOW_ROOT_REL / "history.jsonl"

ACTION_STATUSES = {"open", "completed", "waived", "blocked"}
ACTION_TYPES = {
    "mcp_install",
    "mcp_remove",
    "skill_download",
    "skill_create",
    "skill_remove",
}
PATCH_OPS = {"upsert_json_file", "upsert_text_file", "remove_file", "patch_module_toolchain"}


def utc_now_iso() -> str:
    return _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def now_stamp() -> str:
    return _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _safe_rel(path: str) -> Path:
    rel = Path(path)
    if rel.is_absolute():
        raise RuntimeError(f"Path must be relative: {path}")
    if ".." in rel.parts:
        raise RuntimeError(f"Path cannot contain '..': {path}")
    return rel


def _atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _atomic_write_json(path: Path, obj: Any) -> None:
    _atomic_write_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def _load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _try_jsonschema() -> Any | None:
    try:
        import jsonschema  # type: ignore

        return jsonschema
    except Exception:
        return None


def _load_schema(repo: Path, filename: str) -> Dict[str, Any] | None:
    path = repo / "schemas" / filename
    if not path.exists():
        return None
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    return obj


def _validate_with_jsonschema(instance: Any, schema: Dict[str, Any]) -> List[str]:
    js = _try_jsonschema()
    if js is None:
        return []
    try:
        js.validate(instance=instance, schema=schema)
        return []
    except Exception as exc:  # noqa: BLE001
        return [str(exc)]


def _append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_tree(path: Path) -> str:
    h = hashlib.sha256()
    if not path.exists():
        return h.hexdigest()
    for child in sorted(path.rglob("*")):
        rel = child.relative_to(path).as_posix()
        if child.is_file():
            h.update(f"F:{rel}:".encode("utf-8"))
            h.update(_sha256_file(child).encode("ascii"))
            h.update(b"\n")
    return h.hexdigest()


def _new_revision_id() -> str:
    return f"{REVISION_PREFIX}{now_stamp()}"


def _paths(repo: Path) -> Dict[str, Path]:
    root = repo / WORKFLOW_ROOT_REL
    return {
        "workflow_root": root,
        "config_root": repo / WORKFLOW_CONFIG_REL,
        "assets_root": repo / WORKFLOW_ASSETS_REL,
        "revisions_root": repo / WORKFLOW_REVISIONS_REL,
        "state": repo / WORKFLOW_STATE_REL,
        "history": repo / WORKFLOW_HISTORY_REL,
        "phase_profiles": repo / WORKFLOW_CONFIG_REL / "phase_profiles.json",
        "review_profiles": repo / WORKFLOW_CONFIG_REL / "review_profiles.json",
        "module_overrides": repo / WORKFLOW_CONFIG_REL / "module_overrides",
        "capability_catalog": repo / WORKFLOW_CONFIG_REL / "capability_catalog.json",
        "trust_policy": repo / WORKFLOW_CONFIG_REL / "trust_policy.json",
    }


def _default_phase_profiles() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "default_phase_profile": "base",
        "profiles": {
            "base": {
                "phases": [
                    "planning",
                    "planning-approval",
                    "execution",
                    "verify",
                    "review",
                    "ready",
                    "retro",
                ]
            }
        },
        "stack_overrides": {},
        "risk_overrides": {
            "high": {"phase_profile": "base", "review_profile": "strict"},
            "medium": {"phase_profile": "base", "review_profile": "standard"},
            "low": {"phase_profile": "base", "review_profile": "light"},
        },
    }


def _default_review_profiles() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "default_review_profile": "standard",
        "profiles": {
            "light": {
                "max_allowed": {"p0": 0, "p1": 0, "p2": 5, "p3": 10},
                "required_checks": ["scope", "verify"],
            },
            "standard": {
                "max_allowed": {"p0": 0, "p1": 0, "p2": 3, "p3": 8},
                "required_checks": ["scope", "verify", "review"],
            },
            "strict": {
                "max_allowed": {"p0": 0, "p1": 0, "p2": 0, "p3": 3},
                "required_checks": ["scope", "verify", "review", "ready-validation"],
            },
        },
    }


def _default_capability_catalog() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "entries": [
            {
                "id": "playwright-mcp",
                "kind": "mcp",
                "description": "Browser automation MCP for UI/E2E workflows.",
                "source": "github.com",
                "url": "https://github.com/microsoft/playwright-mcp",
                "tags": ["ui-e2e", "browser"],
                "risk_score": 0.65,
                "install_steps": ["codex mcp add playwright -- npx -y @playwright/mcp", "codex mcp list"],
                "verify_steps": ["run smoke e2e scenario"],
            },
            {
                "id": "skill-creator",
                "kind": "skill",
                "description": "Guided flow to create local reusable skills.",
                "source": "local",
                "url": "",
                "tags": ["skilling", "workflow"],
                "risk_score": 0.2,
                "install_steps": ["create skill draft in overlay and review"],
                "verify_steps": ["load SKILL.md and validate frontmatter"],
            },
        ],
    }


def _default_trust_policy() -> Dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "allowed_sources": ["local", "github.com"],
        "max_risk_score": 0.7,
        "notes": "Safety-first defaults: unknown sources are blocked.",
    }


def _default_state(repo: Path) -> Dict[str, Any]:
    p = _paths(repo)
    assets_hash = _hash_tree(p["assets_root"])
    config_hash = _hash_tree(p["config_root"])
    return {
        "schema_version": SCHEMA_VERSION,
        "retro_only_enforced": True,
        "last_applied_revision": None,
        "overlay_assets_hash": assets_hash,
        "workflow_config_hash": config_hash,
        # Legacy compatibility: older state readers may still use `overlay_hash`.
        "overlay_hash": assets_hash,
        "last_validated_at": None,
    }


def _template_or_default(repo: Path, rel: Path, fallback: Dict[str, Any]) -> Dict[str, Any]:
    path = repo / rel
    if not path.exists():
        return fallback
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback
    if not isinstance(obj, dict):
        return fallback
    return obj


def ensure_scaffold(repo: Path) -> Dict[str, Path]:
    p = _paths(repo)
    p["workflow_root"].mkdir(parents=True, exist_ok=True)
    p["config_root"].mkdir(parents=True, exist_ok=True)
    p["assets_root"].mkdir(parents=True, exist_ok=True)
    p["revisions_root"].mkdir(parents=True, exist_ok=True)
    p["module_overrides"].mkdir(parents=True, exist_ok=True)

    defaults = {
        p["phase_profiles"]: _template_or_default(
            repo,
            Path("templates") / "workflow_overlay" / "config" / "phase_profiles.json",
            _default_phase_profiles(),
        ),
        p["review_profiles"]: _template_or_default(
            repo,
            Path("templates") / "workflow_overlay" / "config" / "review_profiles.json",
            _default_review_profiles(),
        ),
        p["capability_catalog"]: _template_or_default(
            repo,
            Path("templates") / "workflow_overlay" / "config" / "capability_catalog.json",
            _default_capability_catalog(),
        ),
        p["trust_policy"]: _template_or_default(
            repo,
            Path("templates") / "workflow_overlay" / "config" / "trust_policy.json",
            _default_trust_policy(),
        ),
    }
    for path, payload in defaults.items():
        if not path.exists():
            _atomic_write_json(path, payload)

    if not p["state"].exists():
        _atomic_write_json(p["state"], _default_state(repo))
    if not p["history"].exists():
        _atomic_write_text(p["history"], "")
    return p


def load_state(repo: Path) -> Dict[str, Any]:
    p = _paths(repo)
    state = _load_json(p["state"], default=None)
    if not state:
        ensure_scaffold(repo)
        state = _load_json(p["state"], default={})
    return state


def overlay_hash(repo: Path) -> str:
    # Legacy helper alias used by older callers.
    return workflow_hashes(repo)["overlay_assets_hash"]


def workflow_hashes(repo: Path) -> Dict[str, str]:
    p = _paths(repo)
    return {
        "overlay_assets_hash": _hash_tree(p["assets_root"]),
        "workflow_config_hash": _hash_tree(p["config_root"]),
    }


def _detect_stack(path: Path) -> str:
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


def resolve_profiles(repo: Path, modules: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    p = _paths(repo)
    phase_cfg = _load_json(p["phase_profiles"], default=_default_phase_profiles())
    review_cfg = _load_json(p["review_profiles"], default=_default_review_profiles())
    overrides_dir = p["module_overrides"]

    risk_overrides = phase_cfg.get("risk_overrides", {}) if isinstance(phase_cfg, dict) else {}
    stack_overrides = phase_cfg.get("stack_overrides", {}) if isinstance(phase_cfg, dict) else {}

    out: Dict[str, Dict[str, Any]] = {}
    for m in modules:
        mid = str(m.get("id", ""))
        mpath = repo / str(m.get("path", ""))
        stack = _detect_stack(mpath)

        tc = _load_json(mpath / ".csk" / "toolchain.json", default={})
        risk = str(tc.get("risk", "medium")) if isinstance(tc, dict) else "medium"
        phase_profile = str(phase_cfg.get("default_phase_profile", "base"))
        review_profile = str(review_cfg.get("default_review_profile", "standard"))

        if stack in stack_overrides:
            o = stack_overrides.get(stack) or {}
            phase_profile = str(o.get("phase_profile", phase_profile))
            review_profile = str(o.get("review_profile", review_profile))

        if risk in risk_overrides:
            o = risk_overrides.get(risk) or {}
            phase_profile = str(o.get("phase_profile", phase_profile))
            review_profile = str(o.get("review_profile", review_profile))

        o_path = overrides_dir / f"{mid}.json"
        if o_path.exists():
            mo = _load_json(o_path, default={})
            if isinstance(mo, dict):
                phase_profile = str(mo.get("phase_profile", phase_profile))
                review_profile = str(mo.get("review_profile", review_profile))

        out[mid] = {
            "module_id": mid,
            "stack": stack,
            "risk": risk,
            "phase_profile": phase_profile,
            "review_profile": review_profile,
        }
    return out


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out: List[Dict[str, Any]] = []
    for ln in path.read_text(encoding="utf-8").splitlines():
        ln = ln.strip()
        if not ln:
            continue
        try:
            obj = json.loads(ln)
        except Exception:
            continue
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _collect_incidents(repo: Path, modules: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    app_incidents = _read_jsonl(repo / ".csk-app" / "logs" / "incidents.jsonl")
    module_map: Dict[str, List[Dict[str, Any]]] = {}
    for m in modules:
        mid = str(m.get("id", ""))
        mpath = repo / str(m.get("path", ""))
        module_map[mid] = _read_jsonl(mpath / ".csk" / "logs" / "incidents.jsonl")
    return app_incidents, module_map


def _derive_capability_gaps(app_incidents: List[Dict[str, Any]], module_incidents: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    gaps: Dict[str, Dict[str, Any]] = {}

    def touch(gid: str, label: str, module_id: Optional[str], sev: str) -> None:
        item = gaps.setdefault(
            gid,
            {
                "id": gid,
                "label": label,
                "count": 0,
                "modules": set(),
                "severity_counts": {"P0": 0, "P1": 0, "P2": 0, "P3": 0},
            },
        )
        item["count"] += 1
        if module_id:
            item["modules"].add(module_id)
        if sev in item["severity_counts"]:
            item["severity_counts"][sev] += 1

    def classify(inc: Dict[str, Any], module_id: Optional[str]) -> None:
        stage = str(inc.get("stage", "")).lower()
        itype = str(inc.get("type", "")).lower()
        summary = str(inc.get("summary", "")).lower()
        sev = str(inc.get("severity", "P2"))

        if "toolchain" in itype or "command" in summary or "verify" in stage:
            touch("toolchain-ambiguity", "Toolchain command ambiguity", module_id, sev)
        if any(k in summary for k in ["e2e", "browser", "ui", "playwright"]):
            touch("ui-e2e-capability", "UI/E2E capability gap", module_id, sev)
        if any(k in summary for k in ["docs", "documentation", "readme"]):
            touch("docs-capability", "Documentation capability gap", module_id, sev)
        if "review" in stage or "review" in itype:
            touch("review-policy-tuning", "Review policy tuning", module_id, sev)
        if "scope" in stage or "scope" in itype:
            touch("scope-policy-tuning", "Scope policy tuning", module_id, sev)

    for inc in app_incidents:
        classify(inc, None)
    for mid, incidents in module_incidents.items():
        for inc in incidents:
            classify(inc, mid)

    out: List[Dict[str, Any]] = []
    for g in gaps.values():
        out.append(
            {
                "id": g["id"],
                "label": g["label"],
                "count": g["count"],
                "modules": sorted(g["modules"]),
                "severity_counts": g["severity_counts"],
            }
        )
    out.sort(key=lambda x: (x["count"], x["severity_counts"].get("P0", 0), x["severity_counts"].get("P1", 0)), reverse=True)
    return out


def _trust_eval(entry: Dict[str, Any], policy: Dict[str, Any]) -> Tuple[bool, float, str]:
    allowed_sources = set(policy.get("allowed_sources", []))
    max_risk = float(policy.get("max_risk_score", 0.7))
    source = str(entry.get("source", ""))
    risk = float(entry.get("risk_score", 1.0))
    trust_score = max(0.0, 1.0 - risk)
    if source not in allowed_sources:
        return False, trust_score, f"source_not_allowed:{source}"
    if risk > max_risk:
        return False, trust_score, f"risk_above_threshold:{risk}"
    return True, trust_score, "ok"


def _derive_candidates_for_gaps(gaps: List[Dict[str, Any]], catalog: Dict[str, Any], policy: Dict[str, Any], top_candidates: int) -> Dict[str, Dict[str, Any]]:
    entries = catalog.get("entries", []) if isinstance(catalog, dict) else []
    candidates: Dict[str, Dict[str, Any]] = {}

    gap_tag_map = {
        "ui-e2e-capability": ["ui-e2e", "browser"],
        "docs-capability": ["docs"],
        "toolchain-ambiguity": ["toolchain", "workflow"],
        "review-policy-tuning": ["review", "workflow"],
    }

    for gap in gaps:
        gid = str(gap.get("id"))
        tags = set(gap_tag_map.get(gid, []))
        allowed: List[Dict[str, Any]] = []
        blocked: List[Dict[str, Any]] = []
        for entry in entries:
            e_tags = set(entry.get("tags", [])) if isinstance(entry.get("tags"), list) else set()
            if tags and not (tags & e_tags):
                continue
            ok, trust_score, reason = _trust_eval(entry, policy)
            row = {
                "id": entry.get("id"),
                "kind": entry.get("kind"),
                "source": entry.get("source"),
                "url": entry.get("url"),
                "risk_score": entry.get("risk_score", 1.0),
                "trust_score": round(trust_score, 4),
                "reason": reason,
            }
            if ok:
                allowed.append(row)
            else:
                blocked.append(row)
        allowed.sort(key=lambda x: x.get("trust_score", 0.0), reverse=True)
        blocked.sort(key=lambda x: x.get("trust_score", 0.0), reverse=True)
        candidates[gid] = {
            "allowed": allowed[:top_candidates],
            "blocked": blocked[:top_candidates],
        }
    return candidates


def _write_action_ticket(revision_root: Path, action: Dict[str, Any]) -> None:
    actions_dir = revision_root / "actions"
    actions_dir.mkdir(parents=True, exist_ok=True)
    aid = str(action["id"])
    jpath = actions_dir / f"{aid}.json"
    mpath = actions_dir / f"{aid}.md"
    _atomic_write_json(jpath, action)

    lines = [
        f"# Action {aid}",
        "",
        f"- Type: `{action.get('type')}`",
        f"- Target: `{action.get('target')}`",
        f"- Blocking: `{action.get('blocking')}`",
        f"- Status: `{action.get('status')}`",
        f"- Reason: {action.get('reason')}",
        f"- Risk score: {action.get('risk_score')}",
        "",
        "## Install steps",
    ]
    for i, step in enumerate(action.get("install_steps", []), start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Verify steps")
    for i, step in enumerate(action.get("verify_steps", []), start=1):
        lines.append(f"{i}. {step}")
    lines.append("")
    lines.append("## Sources")
    for src in action.get("source_urls", []):
        lines.append(f"- {src}")
    _atomic_write_text(mpath, "\n".join(lines) + "\n")


def _generate_patchset(revision_id: str, gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    ops: List[Dict[str, Any]] = [
        {
            "op": "upsert_json_file",
            "path": f".csk-app/overlay/workflow/assets/generated/{revision_id}-summary.json",
            "content": {
                "schema_version": SCHEMA_VERSION,
                "generated_at": utc_now_iso(),
                "revision_id": revision_id,
                "gaps": gaps,
            },
        }
    ]

    for gap in gaps:
        gid = str(gap.get("id"))
        if gid == "toolchain-ambiguity":
            for mid in gap.get("modules", []):
                ops.append(
                    {
                        "op": "patch_module_toolchain",
                        "module_id": mid,
                        "append_note": "Retro evolution applied: clarify gate commands and remove ambiguity.",
                    }
                )
        if gid == "review-policy-tuning":
            ops.append(
                {
                    "op": "upsert_json_file",
                    "path": ".csk-app/overlay/workflow/assets/generated/review-policy-hints.json",
                    "content": {
                        "schema_version": SCHEMA_VERSION,
                        "generated_at": utc_now_iso(),
                        "hint": "Consider stricter review profile for repeated review incidents.",
                    },
                }
            )
    return {"schema_version": SCHEMA_VERSION, "revision_id": revision_id, "operations": ops}


def create_retro_plan(
    repo: Path,
    modules: List[Dict[str, Any]],
    internet_research_mode: str = "auto",
    top_candidates: int = 5,
    module_filter: Optional[str] = None,
) -> Dict[str, Any]:
    ensure_scaffold(repo)
    revision_id = _new_revision_id()
    p = _paths(repo)
    revision_root = p["revisions_root"] / revision_id
    revision_root.mkdir(parents=True, exist_ok=True)
    (revision_root / "approvals").mkdir(parents=True, exist_ok=True)
    (revision_root / "actions").mkdir(parents=True, exist_ok=True)

    selected_modules = modules
    if module_filter:
        selected_modules = [m for m in modules if str(m.get("id")) == module_filter]

    app_inc, module_inc = _collect_incidents(repo, selected_modules)
    gaps = _derive_capability_gaps(app_inc, module_inc)

    catalog = _load_json(p["capability_catalog"], default=_default_capability_catalog())
    trust = _load_json(p["trust_policy"], default=_default_trust_policy())
    candidates = _derive_candidates_for_gaps(gaps, catalog, trust, top_candidates=top_candidates)

    actions: List[Dict[str, Any]] = []
    idx = 1
    for gap in gaps:
        gid = str(gap.get("id"))
        for cand in candidates.get(gid, {}).get("allowed", []):
            kind = str(cand.get("kind", ""))
            if kind not in {"mcp", "skill"}:
                continue
            action_type = "mcp_install" if kind == "mcp" else "skill_download"
            action = {
                "schema_version": SCHEMA_VERSION,
                "id": f"ACT-{idx:03d}",
                "type": action_type,
                "target": cand.get("id"),
                "blocking": True,
                "status": "open",
                "reason": f"Address capability gap: {gid}",
                "risk_score": cand.get("risk_score", 1.0),
                "source_urls": [u for u in [cand.get("url")] if u],
                "install_steps": [f"Install {cand.get('id')} ({kind}) according to project policy."],
                "verify_steps": ["Run related workflow check and confirm capability is available."],
                "created_at": utc_now_iso(),
                "completed_at": None,
                "completion_evidence": None,
            }
            actions.append(action)
            _write_action_ticket(revision_root, action)
            idx += 1

    patchset = _generate_patchset(revision_id=revision_id, gaps=gaps)
    _atomic_write_json(revision_root / "patchset.json", patchset)

    profiles = resolve_profiles(repo, selected_modules)

    plan = {
        "schema_version": SCHEMA_VERSION,
        "revision_id": revision_id,
        "created_at": utc_now_iso(),
        "status": "planned",
        "module_filter": module_filter,
        "internet_research_mode": internet_research_mode,
        "internet_research_required": bool(gaps) and internet_research_mode == "auto",
        "incidents_summary": {
            "app_count": len(app_inc),
            "module_counts": {k: len(v) for k, v in module_inc.items()},
        },
        "capability_gaps": gaps,
        "candidates": candidates,
        "actions": [
            {
                "id": a["id"],
                "type": a["type"],
                "target": a["target"],
                "status": a["status"],
                "blocking": a["blocking"],
            }
            for a in actions
        ],
        "profiles": profiles,
        "patchset_operation_count": len(patchset.get("operations", [])),
    }
    _atomic_write_json(revision_root / "plan.json", plan)

    return {
        "revision_id": revision_id,
        "revision_root": str(revision_root),
        "plan_path": str(revision_root / "plan.json"),
        "patchset_path": str(revision_root / "patchset.json"),
        "actions_count": len(actions),
    }


def approve_revision(repo: Path, revision_id: str, approved_by: str, note: str) -> Dict[str, Any]:
    p = _paths(repo)
    revision_root = p["revisions_root"] / revision_id
    plan_path = revision_root / "plan.json"
    if not plan_path.exists():
        raise RuntimeError(f"Unknown revision: {revision_id}")
    approval = {
        "schema_version": SCHEMA_VERSION,
        "revision_id": revision_id,
        "approved_at": utc_now_iso(),
        "approved_by": approved_by or "user",
        "note": note or "",
        "plan_sha256": _sha256_file(plan_path),
    }
    out = revision_root / "approvals" / "retro.json"
    _atomic_write_json(out, approval)
    return {"approval_path": str(out)}


def action_complete(repo: Path, revision_id: str, action_id: str, evidence: str, waived: bool = False) -> Dict[str, Any]:
    p = _paths(repo)
    jpath = p["revisions_root"] / revision_id / "actions" / f"{action_id}.json"
    if not jpath.exists():
        raise RuntimeError(f"Unknown action: {action_id}")
    action = _load_json(jpath, default={})
    if not isinstance(action, dict):
        raise RuntimeError("Invalid action payload.")
    action["status"] = "waived" if waived else "completed"
    action["completed_at"] = utc_now_iso()
    action["completion_evidence"] = evidence
    _atomic_write_json(jpath, action)
    return {"action_path": str(jpath), "status": action["status"]}


def list_history(repo: Path, limit: int = 20) -> List[Dict[str, Any]]:
    p = _paths(repo)
    rows = _read_jsonl(p["history"])
    return rows[-max(1, limit) :]


def _set_dotted(obj: Dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = obj
    for part in parts[:-1]:
        nxt = cur.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[part] = nxt
        cur = nxt
    cur[parts[-1]] = value


def _backup_once(repo: Path, revision_root: Path, rel_path: str, backed_up: Dict[str, Dict[str, Any]]) -> None:
    if rel_path in backed_up:
        return
    rel = _safe_rel(rel_path)
    dst = repo / rel
    entry: Dict[str, Any] = {"path": rel_path, "existed": dst.exists(), "backup": None}
    if dst.exists():
        b = revision_root / "backups" / rel
        b.parent.mkdir(parents=True, exist_ok=True)
        if dst.is_dir():
            shutil.copytree(dst, b, dirs_exist_ok=True)
        else:
            shutil.copy2(dst, b)
        entry["backup"] = str(b.relative_to(revision_root)).replace("\\", "/")
    backed_up[rel_path] = entry


def _preflight_patchset(
    repo: Path,
    modules_by_id: Dict[str, Dict[str, Any]],
    patchset: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], List[str]]:
    operations = patchset.get("operations", []) if isinstance(patchset, dict) else []
    if not isinstance(operations, list):
        raise RuntimeError("Invalid patchset.operations")
    validated_ops: List[Dict[str, Any]] = []
    target_paths: List[str] = []

    for op in operations:
        if not isinstance(op, dict):
            raise RuntimeError("Patchset operation must be object")
        kind = str(op.get("op", ""))
        if kind not in PATCH_OPS:
            raise RuntimeError(f"Unsupported patch op: {kind}")

        if kind in {"upsert_json_file", "upsert_text_file", "remove_file"}:
            rel_path = str(op.get("path", ""))
            rel = _safe_rel(rel_path)
            allowed_prefix = str(WORKFLOW_ROOT_REL).replace("\\", "/") + "/"
            if not rel.as_posix().startswith(allowed_prefix):
                raise RuntimeError(f"Operation path outside workflow overlay: {rel_path}")
            target_paths.append(rel.as_posix())
            validated_ops.append(op)
            continue

        if kind == "patch_module_toolchain":
            module_id = str(op.get("module_id", ""))
            if module_id not in modules_by_id:
                raise RuntimeError(f"Unknown module for toolchain patch: {module_id}")
            mroot = repo / str(modules_by_id[module_id].get("path", ""))
            tc_path = mroot / ".csk" / "toolchain.json"
            if tc_path.exists():
                tc = _load_json(tc_path, default=None)
                if tc is not None and not isinstance(tc, dict):
                    raise RuntimeError(f"Invalid toolchain json for module {module_id}")
            rel_path = str(tc_path.relative_to(repo)).replace("\\", "/")
            target_paths.append(rel_path)
            validated_ops.append(op)
            continue

    unique_targets = list(dict.fromkeys(target_paths))
    return validated_ops, unique_targets


def _build_backup_manifest(repo: Path, revision_root: Path, target_paths: List[str]) -> List[Dict[str, Any]]:
    backed_up: Dict[str, Dict[str, Any]] = {}
    for rel_path in target_paths:
        _backup_once(repo, revision_root, rel_path, backed_up)
    backup_manifest = list(backed_up.values())
    _atomic_write_json(revision_root / "backup_manifest.json", {"schema_version": SCHEMA_VERSION, "files": backup_manifest})
    return backup_manifest


def _apply_patchset_operations(
    repo: Path,
    modules_by_id: Dict[str, Dict[str, Any]],
    operations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    applied: List[Dict[str, Any]] = []

    for op in operations:
        kind = str(op.get("op", ""))

        if kind in {"upsert_json_file", "upsert_text_file", "remove_file"}:
            rel_path = str(op.get("path", ""))
            rel = _safe_rel(rel_path)
            dst = repo / rel
            if kind == "upsert_json_file":
                _atomic_write_json(dst, op.get("content", {}))
            elif kind == "upsert_text_file":
                _atomic_write_text(dst, str(op.get("content", "")))
            elif kind == "remove_file":
                if dst.exists() and dst.is_dir():
                    shutil.rmtree(dst)
                elif dst.exists():
                    dst.unlink()
            applied.append({"op": kind, "path": rel_path})
            continue

        if kind == "patch_module_toolchain":
            module_id = str(op.get("module_id", ""))
            mroot = repo / str(modules_by_id[module_id].get("path", ""))
            rel_path = str((mroot / ".csk" / "toolchain.json").relative_to(repo)).replace("\\", "/")
            tc_path = repo / _safe_rel(rel_path)
            tc = _load_json(tc_path, default={})
            if not isinstance(tc, dict):
                raise RuntimeError(f"Invalid toolchain json for module {module_id}")

            set_payload = op.get("set", {})
            if isinstance(set_payload, dict):
                for dotted, value in set_payload.items():
                    _set_dotted(tc, str(dotted), value)

            append_note = str(op.get("append_note", "")).strip()
            if append_note:
                prev = str(tc.get("notes", "")).strip()
                if prev:
                    tc["notes"] = prev + "\n" + append_note
                else:
                    tc["notes"] = append_note

            _atomic_write_json(tc_path, tc)
            applied.append({"op": kind, "module_id": module_id, "path": rel_path})
            continue

    return applied


def _restore_from_backup_manifest(repo: Path, revision_root: Path, backup_manifest: List[Dict[str, Any]]) -> None:
    for entry in backup_manifest:
        rel_path = str(entry.get("path", ""))
        rel = _safe_rel(rel_path)
        dst = repo / rel
        existed = bool(entry.get("existed", False))
        backup_rel = entry.get("backup")

        if existed:
            if not backup_rel:
                raise RuntimeError(f"Backup missing for path: {rel_path}")
            src = revision_root / str(backup_rel)
            if dst.exists() and dst.is_dir():
                shutil.rmtree(dst)
            elif dst.exists():
                dst.unlink()
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)
            continue

        if dst.exists() and dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()


def _blocking_actions_pending(actions_dir: Path) -> List[Dict[str, Any]]:
    pending: List[Dict[str, Any]] = []
    if not actions_dir.exists():
        return pending
    for action_file in sorted(actions_dir.glob("*.json")):
        action = _load_json(action_file, default={})
        if not isinstance(action, dict):
            continue
        if not bool(action.get("blocking", True)):
            continue
        status = str(action.get("status", "open"))
        if status not in {"completed", "waived"}:
            pending.append({"id": action.get("id"), "status": status, "path": str(action_file)})
    return pending


def apply_revision(
    repo: Path,
    modules: List[Dict[str, Any]],
    revision_id: str,
    validate_fn: Optional[Callable[[], Tuple[bool, List[str], List[str]]]] = None,
) -> Dict[str, Any]:
    ensure_scaffold(repo)
    p = _paths(repo)
    revision_root = p["revisions_root"] / revision_id
    plan_path = revision_root / "plan.json"
    patchset_path = revision_root / "patchset.json"
    approval_path = revision_root / "approvals" / "retro.json"

    if not plan_path.exists() or not patchset_path.exists():
        raise RuntimeError(f"Missing plan or patchset for revision: {revision_id}")
    if not approval_path.exists():
        raise RuntimeError("Missing approval artifact approvals/retro.json")

    approval = _load_json(approval_path, default={})
    if str(approval.get("plan_sha256", "")) != _sha256_file(plan_path):
        raise RuntimeError("Approval plan hash mismatch. Re-approve revision.")

    state_before = load_state(repo)
    current_hashes = workflow_hashes(repo)
    expected_assets_hash = str(state_before.get("overlay_assets_hash") or state_before.get("overlay_hash", ""))
    expected_config_hash = str(state_before.get("workflow_config_hash", ""))
    if expected_assets_hash and expected_assets_hash != current_hashes["overlay_assets_hash"]:
        raise RuntimeError("overlay_assets_hash_drift")
    if expected_config_hash and expected_config_hash != current_hashes["workflow_config_hash"]:
        raise RuntimeError("workflow_config_hash_drift")

    pending = _blocking_actions_pending(revision_root / "actions")
    if pending:
        raise RuntimeError("Blocking action tickets are not completed/waived.")

    patchset = _load_json(patchset_path, default={})
    modules_by_id = {str(m.get("id")): m for m in modules if isinstance(m, dict)}

    operations: List[Dict[str, Any]] = []
    target_paths: List[str] = []
    backup_manifest: List[Dict[str, Any]] = []
    applied_ops: List[Dict[str, Any]] = []
    post_warnings: List[str] = []
    apply_report_path = revision_root / "apply_report.json"

    try:
        operations, target_paths = _preflight_patchset(repo, modules_by_id, patchset)
        if validate_fn is not None:
            ok, errors, _warnings = validate_fn()
            if not ok:
                raise RuntimeError("Pre-apply validate --all --strict failed: " + "; ".join(errors))

        backup_manifest = _build_backup_manifest(repo, revision_root, target_paths)
        applied_ops = _apply_patchset_operations(repo, modules_by_id, operations)

        state_after = dict(state_before)
        hashes_after = workflow_hashes(repo)
        state_after["last_applied_revision"] = revision_id
        state_after["overlay_assets_hash"] = hashes_after["overlay_assets_hash"]
        state_after["workflow_config_hash"] = hashes_after["workflow_config_hash"]
        state_after["overlay_hash"] = hashes_after["overlay_assets_hash"]
        state_after["last_validated_at"] = utc_now_iso()
        _atomic_write_json(p["state"], state_after)

        if validate_fn is not None:
            post_ok, post_errors, post_warnings = validate_fn()
            if not post_ok:
                raise RuntimeError("Post-apply validate --all --strict failed: " + "; ".join(post_errors))

        apply_report = {
            "schema_version": SCHEMA_VERSION,
            "revision_id": revision_id,
            "applied_at": utc_now_iso(),
            "operations": applied_ops,
            "backup_manifest": backup_manifest,
            "post_validate_warnings": post_warnings,
            "success": True,
        }
        _atomic_write_json(apply_report_path, apply_report)

        _append_jsonl(
            p["history"],
            {
                "ts": utc_now_iso(),
                "event": "apply",
                "revision_id": revision_id,
                "success": True,
                "operations": len(applied_ops),
            },
        )
        return {"apply_report": str(apply_report_path), "operations": len(applied_ops)}
    except Exception as exc:  # noqa: BLE001
        restore_errors: List[str] = []
        if backup_manifest:
            try:
                _restore_from_backup_manifest(repo, revision_root, backup_manifest)
            except Exception as restore_exc:  # noqa: BLE001
                restore_errors.append(str(restore_exc))
        _atomic_write_json(p["state"], state_before)
        error_text = str(exc)
        if restore_errors:
            error_text = error_text + " | restore_failed: " + "; ".join(restore_errors)
        fail_report = {
            "schema_version": SCHEMA_VERSION,
            "revision_id": revision_id,
            "applied_at": utc_now_iso(),
            "operations": applied_ops,
            "backup_manifest": backup_manifest,
            "post_validate_warnings": post_warnings,
            "success": False,
            "error": error_text,
        }
        _atomic_write_json(apply_report_path, fail_report)
        _append_jsonl(
            p["history"],
            {
                "ts": utc_now_iso(),
                "event": "apply",
                "revision_id": revision_id,
                "success": False,
                "operations": len(applied_ops),
                "error": error_text,
            },
        )
        raise RuntimeError(error_text)


def rollback_revision(
    repo: Path,
    revision_id: str,
    validate_fn: Optional[Callable[[], Tuple[bool, List[str], List[str]]]] = None,
) -> Dict[str, Any]:
    ensure_scaffold(repo)
    p = _paths(repo)
    revision_root = p["revisions_root"] / revision_id
    backup_manifest_path = revision_root / "backup_manifest.json"
    if not backup_manifest_path.exists():
        raise RuntimeError(f"No backup manifest for revision: {revision_id}")

    backup_manifest_obj = _load_json(backup_manifest_path, default={})
    files = backup_manifest_obj.get("files", []) if isinstance(backup_manifest_obj, dict) else []
    if not isinstance(files, list):
        raise RuntimeError("Invalid backup manifest.")

    state_before = load_state(repo)
    _restore_from_backup_manifest(repo, revision_root, files)

    state_after = dict(state_before)
    hashes_after = workflow_hashes(repo)
    state_after["overlay_assets_hash"] = hashes_after["overlay_assets_hash"]
    state_after["workflow_config_hash"] = hashes_after["workflow_config_hash"]
    state_after["overlay_hash"] = hashes_after["overlay_assets_hash"]
    state_after["last_validated_at"] = utc_now_iso()
    _atomic_write_json(p["state"], state_after)

    post_ok = True
    post_errors: List[str] = []
    if validate_fn is not None:
        post_ok, post_errors, _warnings = validate_fn()
    if not post_ok:
        _atomic_write_json(p["state"], state_before)
        raise RuntimeError("Post-rollback validate --all --strict failed: " + "; ".join(post_errors))

    _append_jsonl(
        p["history"],
        {
            "ts": utc_now_iso(),
            "event": "rollback",
            "revision_id": revision_id,
            "success": True,
            "restored_files": len(files),
        },
    )
    return {"restored_files": len(files)}


def validate_contracts(repo: Path, module_ids: List[str]) -> Tuple[List[str], List[str], List[str]]:
    errors: List[str] = []
    warnings: List[str] = []
    infos: List[str] = []
    p = _paths(repo)

    state = _load_json(p["state"], default=None)
    if state is None:
        # Backward-compatible: retro evolution may be uninitialized before first retro-plan.
        return errors, warnings, infos

    required_state = [
        "schema_version",
        "retro_only_enforced",
        "last_applied_revision",
        "last_validated_at",
    ]
    if not isinstance(state, dict):
        errors.append("workflow state must be an object")
        return errors, warnings, infos
    for key in required_state:
        if key not in state:
            errors.append(f"workflow state missing key: {key}")

    expected_assets_hash = str(state.get("overlay_assets_hash") or state.get("overlay_hash", ""))
    expected_config_hash = str(state.get("workflow_config_hash", ""))
    if not expected_assets_hash:
        errors.append("workflow state missing assets hash (`overlay_assets_hash` or legacy `overlay_hash`)")
    if "workflow_config_hash" not in state:
        infos.append(
            "workflow state missing key: workflow_config_hash (legacy state; will be populated after next retro-apply/rollback)"
        )
    hashes = workflow_hashes(repo)
    if expected_assets_hash and expected_assets_hash != hashes["overlay_assets_hash"]:
        errors.append("workflow overlay assets hash drift detected")
    if expected_config_hash and expected_config_hash != hashes["workflow_config_hash"]:
        errors.append("workflow overlay config hash drift detected")

    # Config validation
    cfg_schemas = {
        "phase_profiles": "phase_profiles.schema.json",
        "review_profiles": "review_profiles.schema.json",
        "capability_catalog": "capability_catalog.schema.json",
        "trust_policy": "trust_policy.schema.json",
    }
    for cfg_key in ["phase_profiles", "review_profiles", "capability_catalog", "trust_policy"]:
        path = p[cfg_key]
        if not path.exists():
            errors.append(f"missing workflow config: {path}")
            continue
        obj = _load_json(path, default=None)
        if not isinstance(obj, dict):
            errors.append(f"workflow config is not object: {path}")
            continue
        if obj.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"workflow config schema_version must be {SCHEMA_VERSION}: {path}")
        schema = _load_schema(repo, cfg_schemas[cfg_key])
        if schema is not None:
            for err in _validate_with_jsonschema(obj, schema):
                errors.append(f"{path}: {err}")

    # Revisions validation
    revision_schema = _load_schema(repo, "retro_revision.schema.json")
    action_schema = _load_schema(repo, "retro_action_ticket.schema.json")
    if p["revisions_root"].exists():
        for rev in sorted(p["revisions_root"].glob("REV-*")):
            if not rev.is_dir():
                continue
            plan = _load_json(rev / "plan.json", default=None)
            patch = _load_json(rev / "patchset.json", default=None)
            if plan is None or patch is None:
                errors.append(f"revision missing plan/patchset: {rev.name}")
                continue
            if not isinstance(plan, dict):
                errors.append(f"revision plan is not object: {rev.name}")
            elif revision_schema is not None:
                for err in _validate_with_jsonschema(plan, revision_schema):
                    errors.append(f"{rev.name}/plan.json: {err}")
            if not isinstance(patch, dict):
                errors.append(f"revision patchset is not object: {rev.name}")
                continue
            if isinstance(plan, dict):
                if str(plan.get("revision_id", "")) and str(plan.get("revision_id")) != rev.name:
                    errors.append(f"revision id mismatch in plan: {rev.name}")
            ops = patch.get("operations", [])
            if not isinstance(ops, list):
                errors.append(f"revision operations is not list: {rev.name}")
                continue
            for idx, op in enumerate(ops):
                if not isinstance(op, dict):
                    errors.append(f"{rev.name} op[{idx}] not object")
                    continue
                kind = str(op.get("op", ""))
                if kind not in PATCH_OPS:
                    errors.append(f"{rev.name} op[{idx}] invalid op={kind}")
                    continue
                if kind == "patch_module_toolchain":
                    module_id = str(op.get("module_id", ""))
                    if module_id not in module_ids:
                        errors.append(f"{rev.name} op[{idx}] unknown module_id={module_id}")

            actions_dir = rev / "actions"
            if actions_dir.exists():
                for action_file in sorted(actions_dir.glob("*.json")):
                    action = _load_json(action_file, default=None)
                    if not isinstance(action, dict):
                        errors.append(f"action ticket not object: {action_file}")
                        continue
                    if action_schema is not None:
                        for err in _validate_with_jsonschema(action, action_schema):
                            errors.append(f"{action_file}: {err}")
                    status = str(action.get("status", ""))
                    atype = str(action.get("type", ""))
                    if status not in ACTION_STATUSES:
                        errors.append(f"action ticket invalid status={status}: {action_file}")
                    if atype not in ACTION_TYPES:
                        errors.append(f"action ticket invalid type={atype}: {action_file}")

    return errors, warnings, infos
