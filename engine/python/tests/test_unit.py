"""Unit tests for core utilities."""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from csk_next.domain.models import ensure_task_transition
from csk_next.domain.schemas import SchemaValidationError, validate_schema
from csk_next.profiles.manager import merge_profile
from csk_next.runtime.paths import resolve_layout
from csk_next.runtime.tasks_engine import mark_task_blocked, mark_task_status
from csk_next.skills.generator import generate_skills


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH = str(REPO_ROOT / "engine" / "python")


def run_cli(
    root: Path,
    *args: str,
    expect_code: int = 0,
    state_root: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHONPATH
    if env_overrides:
        env.update(env_overrides)
    command = [sys.executable, "-m", "csk_next.cli.main", "--root", str(root)]
    if state_root is not None:
        command.extend(["--state-root", str(state_root)])
    command.extend(args)
    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != expect_code:
        raise AssertionError(proc.stdout + proc.stderr)
    return json.loads(proc.stdout)


def module_state_root(root: Path, module_path: str) -> Path:
    return root / ".csk" / "modules" / Path(module_path)


def user_data(payload: dict) -> dict:
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


def tree_digest(root: Path) -> str:
    rows: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        rows.append(f"{rel}:{sha256(path.read_bytes()).hexdigest()}")
    return sha256("\n".join(rows).encode("utf-8")).hexdigest()


class UnitTests(unittest.TestCase):
    def test_schema_required_keys(self) -> None:
        with self.assertRaises(SchemaValidationError):
            validate_schema("registry", {"schema_version": "1"})

    def test_freeze_drift_blocks_plan_approval(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)
            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)

            plan = module_state_root(root, "mod/app") / "tasks" / task_id / "plan.md"
            plan.write_text(plan.read_text(encoding="utf-8") + "\nDrift\n", encoding="utf-8")

            payload = run_cli(
                root,
                "task",
                "approve-plan",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
                expect_code=2,
            )
            self.assertEqual(payload["status"], "error")
            self.assertIn("freeze drift", payload["error"])

    def test_profile_merge(self) -> None:
        base = {
            "name": "default",
            "required_gates": ["scope", "verify", "review"],
            "e2e": {"required": False, "commands": []},
            "recommended": {"linters": ["ruff"], "test_frameworks": [], "skills": [], "mcp": []},
        }
        override = {
            "name": "python",
            "required_gates": ["scope", "verify", "review", "e2e"],
            "e2e": {"required": True, "commands": ["pytest"]},
            "recommended": {"linters": ["ruff", "mypy"], "test_frameworks": ["pytest"], "skills": [], "mcp": []},
        }
        merged = merge_profile(base, override)
        self.assertEqual(merged["name"], "python")
        self.assertTrue(merged["e2e"]["required"])
        self.assertIn("e2e", merged["required_gates"])

    def test_module_init_scaffold_opt_in(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")

            self.assertFalse((root / "modules" / "app" / "AGENTS.md").exists())
            self.assertFalse((root / "modules" / "app" / "PUBLIC_API.md").exists())

            run_cli(root, "module", "init", "--module-id", "app", "--write-scaffold")
            self.assertTrue((root / "modules" / "app" / "AGENTS.md").exists())
            self.assertTrue((root / "modules" / "app" / "PUBLIC_API.md").exists())

    def test_module_status_for_unregistered_module_returns_actionable_next(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")

            payload = run_cli(root, "module", "status", "--module-id", "ghost")
            self.assertEqual(payload["status"], "ok")
            data = user_data(payload)
            module = data["module"]
            self.assertFalse(module["registered"])
            self.assertFalse(module["initialized"])
            self.assertIsNone(module["path"])
            self.assertIsNone(module["kernel_version"])
            self.assertEqual(module["phase"], "UNREGISTERED")
            self.assertIn("csk module add", payload["next"]["recommended"])
            self.assertIn("--module-id ghost", payload["next"]["recommended"])

    def test_module_status_for_registered_module_requires_explicit_init(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")

            before = run_cli(root, "module", "status", "--module-id", "app")
            before_module = user_data(before)["module"]
            self.assertTrue(before_module["registered"])
            self.assertFalse(before_module["initialized"])
            self.assertIsNone(before_module["kernel_version"])
            self.assertEqual(before["next"]["recommended"], "csk module init --module-id app --write-scaffold")

            run_cli(root, "module", "init", "--module-id", "app", "--write-scaffold")
            after = run_cli(root, "module", "status", "--module-id", "app")
            after_module = user_data(after)["module"]
            self.assertTrue(after_module["registered"])
            self.assertTrue(after_module["initialized"])
            self.assertEqual(after_module["kernel_version"], "1.0.0")

    def test_module_init_is_idempotent_and_emits_initialized_event(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")

            first = run_cli(root, "module", "init", "--module-id", "app", "--write-scaffold")
            module_root = root / "modules" / "app"
            digest_first = tree_digest(module_root)

            second = run_cli(root, "module", "init", "--module-id", "app", "--write-scaffold")
            digest_second = tree_digest(module_root)
            self.assertEqual(digest_first, digest_second)

            self.assertFalse(first["already_initialized"])
            self.assertTrue(first["kernel_created"])
            self.assertTrue(first["scaffold_written"])
            self.assertEqual(sorted(first["scaffold_created"]), ["AGENTS.md", "PUBLIC_API.md"])

            self.assertTrue(second["already_initialized"])
            self.assertFalse(second["kernel_created"])
            self.assertTrue(second["scaffold_written"])
            self.assertEqual(second["scaffold_created"], [])

            eventlog = root / ".csk" / "app" / "eventlog.sqlite"
            with sqlite3.connect(eventlog) as connection:
                count = connection.execute(
                    "SELECT COUNT(*) FROM events WHERE type = ? AND module_id = ?",
                    ("module.initialized", "app"),
                ).fetchone()[0]
            self.assertEqual(int(count), 2)

    def test_registry_missing_registered_is_migrated(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            registry_path = root / ".csk" / "app" / "registry.json"
            registry_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "modules": [
                            {
                                "module_id": "root",
                                "path": ".",
                                "initialized": False,
                                "created_at": "2026-02-26T00:00:00Z",
                                "updated_at": "2026-02-26T00:00:00Z",
                            }
                        ],
                        "defaults": {
                            "worktree_policy": "per_module",
                            "proof_storage": "worktree_run",
                            "user_check": "profile_optional",
                        },
                        "updated_at": "2026-02-26T00:00:00Z",
                    },
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            run_cli(root, "status", "--json")
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            self.assertTrue(registry["modules"][0]["registered"])

    def test_module_add_accepts_absolute_path_inside_repo(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            absolute = (root / "modules" / "app").resolve()
            added = run_cli(root, "module", "add", "--path", str(absolute), "--module-id", "app")
            self.assertEqual(added["status"], "ok")
            self.assertEqual(added["module"]["path"], "modules/app")

    def test_bootstrap_runs_registry_detect_when_empty(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "packages" / "auth").mkdir(parents=True, exist_ok=True)
            (root / "apps" / "web").mkdir(parents=True, exist_ok=True)
            (root / "services" / "api").mkdir(parents=True, exist_ok=True)

            bootstrap = run_cli(root, "bootstrap")
            self.assertEqual(bootstrap["status"], "ok")
            self.assertEqual(bootstrap["registry_modules"], 3)
            self.assertEqual(bootstrap["registry_detect_created"], 3)

            module_list_payload = run_cli(root, "module", "list")
            self.assertEqual(module_list_payload["status"], "ok")
            roots = {item["root_path"] for item in module_list_payload["modules"]}
            self.assertEqual(roots, {"packages/auth", "apps/web", "services/api"})

            show = run_cli(root, "module", "show", "auth")
            self.assertEqual(show["status"], "ok")
            self.assertEqual(show["module"]["root_path"], "packages/auth")
            self.assertIn("auth", show["module"]["keywords"])

            detect_again = run_cli(root, "registry", "detect")
            self.assertEqual(detect_again["status"], "ok")
            self.assertEqual(detect_again["created_count"], 0)

    def test_bootstrap_writes_codex_first_root_agents_contract(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            agents = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("`csk status --json`", agents)
            self.assertIn("`$csk`", agents)
            self.assertIn("`NEXT`", agents)
            self.assertIn("`csk skills generate`", agents)
            self.assertIn("auto-run `csk bootstrap`/`csk skills generate`", agents)

    def test_registry_detect_fallback_root_module(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            bootstrap = run_cli(root, "bootstrap")
            self.assertEqual(bootstrap["status"], "ok")
            self.assertEqual(bootstrap["registry_modules"], 1)
            self.assertEqual(bootstrap["registry_detect_created"], 1)

            module_list_payload = run_cli(root, "module", "list")
            self.assertEqual(module_list_payload["status"], "ok")
            self.assertEqual(len(module_list_payload["modules"]), 1)
            self.assertEqual(module_list_payload["modules"][0]["module_id"], "root")
            self.assertEqual(module_list_payload["modules"][0]["root_path"], ".")

    def test_status_alias_without_command_and_phase_projection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            status_payload = run_cli(root)
            self.assertEqual(status_payload["status"], "ok")
            self.assertTrue(status_payload["summary"]["bootstrapped"])
            status_data = user_data(status_payload)
            app_row = next(row for row in status_data["modules"] if row["module_id"] == "app")
            self.assertEqual(app_row["phase"], "PLANNING")
            self.assertEqual(app_row["active_task_id"], task_id)
            self.assertEqual(status_payload["next"]["recommended"], "csk run")

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)

            critic_passed_payload = run_cli(root, "status", "--json")
            critic_data = user_data(critic_passed_payload)
            critic_passed_row = next(row for row in critic_data["modules"] if row["module_id"] == "app")
            self.assertEqual(critic_passed_row["phase"], "PLANNING")
            self.assertEqual(critic_passed_row["task_status"], "critic_passed")
            self.assertEqual(critic_passed_payload["next"]["recommended"], "csk run")

            module_critic_payload = run_cli(root, "module", "status", "--module-id", "app")
            module_critic_data = user_data(module_critic_payload)
            self.assertEqual(module_critic_data["module"]["phase"], "PLANNING")
            self.assertEqual(module_critic_payload["next"]["recommended"], "csk run")

            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)

            frozen_payload = run_cli(root, "status", "--json")
            frozen_data = user_data(frozen_payload)
            frozen_row = next(row for row in frozen_data["modules"] if row["module_id"] == "app")
            self.assertEqual(frozen_row["phase"], "PLAN_FROZEN")
            self.assertIn("csk approve", frozen_payload["next"]["recommended"])

            run_cli(root, "task", "approve-plan", "--module-id", "app", "--task-id", task_id, "--approved-by", "tester")
            layout = resolve_layout(root)
            mark_task_status(layout, "modules/app", task_id, "executing")
            mark_task_blocked(layout, "modules/app", task_id, "verify retries exceeded")

            blocked_payload = run_cli(root, "status", "--json")
            blocked_data = user_data(blocked_payload)
            blocked_row = next(row for row in blocked_data["modules"] if row["module_id"] == "app")
            self.assertEqual(blocked_row["phase"], "BLOCKED")
            self.assertIn("retro run", blocked_payload["next"]["recommended"])

            module_blocked_payload = run_cli(root, "module", "status", "--module-id", "app")
            module_blocked_data = user_data(module_blocked_payload)
            self.assertEqual(module_blocked_data["module"]["phase"], "BLOCKED")
            self.assertIn("retro run", module_blocked_payload["next"]["recommended"])

    def test_status_includes_skills_projection(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(root, "status", "--json")
            self.assertEqual(payload["status"], "ok")
            data = user_data(payload)
            self.assertIn("skills", data)
            self.assertEqual(data["skills"]["status"], "ok")
            self.assertEqual(data["skills"]["missing"], [])
            self.assertEqual(data["skills"]["modified"], [])
            self.assertEqual(data["skills"]["stale"], [])

    def test_status_next_prefers_skills_generate_when_skills_are_drifted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            skill_files = sorted((root / ".agents" / "skills").rglob("SKILL.md"))
            self.assertTrue(skill_files)
            first_skill = skill_files[0]
            first_skill.write_text(first_skill.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")

            payload = run_cli(root, "status", "--json")
            self.assertEqual(user_data(payload)["skills"]["status"], "failed")
            self.assertEqual(payload["next"]["recommended"], "csk skills generate")

    def test_module_alias_dashboard_and_cd_hint(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            run_cli(
                root,
                "mission",
                "new",
                "--title",
                "Demo Mission",
                "--summary",
                "Status projection test",
                "--modules",
                "app",
            )

            alias_payload = run_cli(root, "module", "app")
            self.assertEqual(alias_payload["status"], "ok")
            alias_data = user_data(alias_payload)
            self.assertEqual(alias_data["module"]["module_id"], "app")
            self.assertEqual(alias_data["module"]["phase"], "PLANNING")
            self.assertIsNotNone(alias_data["module"]["worktree_path"])
            self.assertIsNotNone(alias_data["cd_hint"])
            self.assertTrue(alias_data["cd_hint"].startswith("cd "))
            self.assertEqual(alias_payload["next"]["recommended"], "csk run")

            status_payload = run_cli(root, "module", "status", "--module-id", "app")
            self.assertEqual(status_payload["status"], "ok")
            status_data = user_data(status_payload)
            self.assertEqual(status_data["module"]["module_id"], "app")
            self.assertEqual(status_data["module"]["phase"], alias_data["module"]["phase"])

    def test_external_state_root_keeps_repo_without_runtime_dirs(self) -> None:
        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as state_dir:
            root = Path(temp_dir)
            state_root = Path(state_dir) / "state"
            run_cli(root, "bootstrap", state_root=state_root)
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app", state_root=state_root)
            run_cli(root, "module", "init", "--module-id", "app", state_root=state_root)

            task = run_cli(root, "task", "new", "--module-id", "app", state_root=state_root)
            self.assertTrue((state_root / ".csk" / "app" / "registry.json").exists())
            self.assertFalse((root / ".csk").exists())
            self.assertTrue(Path(task["task_path"]).exists())
            self.assertTrue(str(task["task_path"]).startswith(str(state_root / ".csk" / "modules")))

    def test_state_root_from_env(self) -> None:
        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as state_dir:
            root = Path(temp_dir)
            state_root = Path(state_dir) / "state-from-env"
            previous = os.environ.get("CSK_STATE_ROOT")
            try:
                os.environ["CSK_STATE_ROOT"] = str(state_root)
                run_cli(root, "bootstrap")
            finally:
                if previous is None:
                    os.environ.pop("CSK_STATE_ROOT", None)
                else:
                    os.environ["CSK_STATE_ROOT"] = previous

            self.assertTrue((state_root / ".csk" / "app" / "registry.json").exists())
            self.assertFalse((root / ".csk").exists())

    def test_migrate_state_copies_legacy_artifacts(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            legacy_file = root / ".csk" / "local" / "skills_override" / "custom" / "SKILL.md"
            legacy_file.parent.mkdir(parents=True, exist_ok=True)
            legacy_file.write_text("legacy override\n", encoding="utf-8")

            state_root = root / "control-state"
            migrated = run_cli(root, "migrate-state", state_root=state_root)
            self.assertEqual(migrated["status"], "ok")
            self.assertTrue(migrated["migrated"])
            self.assertTrue((state_root / ".csk" / "local" / "skills_override" / "custom" / "SKILL.md").exists())
            self.assertTrue(legacy_file.exists())

    def test_doctor_git_boundary_warn_only(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            (root / "README.md").write_text("# repo\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True, capture_output=True, text=True)
            subprocess.run(
                ["git", "-c", "user.name=Tester", "-c", "user.email=tester@example.com", "commit", "-m", "init"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )

            run_cli(root, "bootstrap")
            doctor = run_cli(root, "doctor", "run", "--git-boundary")
            self.assertEqual(doctor["status"], "ok")
            self.assertIsNotNone(doctor["git_boundary"])
            self.assertFalse(doctor["git_boundary"]["passed"])
            self.assertGreaterEqual(len(doctor["warnings"]), 1)

    def test_skill_generation_override(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            engine_src = root / "engine"
            local_src = root / "local"
            out = root / "out"

            (engine_src / "alpha").mkdir(parents=True)
            (local_src / "alpha").mkdir(parents=True)
            (engine_src / "alpha" / "SKILL.md").write_text("engine", encoding="utf-8")
            (local_src / "alpha" / "SKILL.md").write_text("override", encoding="utf-8")

            generate_skills(engine_src, local_src, out)
            generated = (out / "alpha" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("GENERATED: do not edit by hand", generated)
            self.assertIn("override", generated)

    def test_skills_generate_is_deterministic(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "skills", "generate")
            digest_first = tree_digest(root / ".agents" / "skills")
            run_cli(root, "skills", "generate")
            digest_second = tree_digest(root / ".agents" / "skills")
            self.assertEqual(digest_first, digest_second)

    def test_skills_templates_include_next_block(self) -> None:
        skills_src = REPO_ROOT / "engine" / "python" / "csk_next" / "assets" / "engine_pack" / "skills_src"
        files = sorted(skills_src.rglob("SKILL.md"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertIn("NEXT:", text, msg=str(path))

    def test_skills_templates_include_yaml_frontmatter(self) -> None:
        skills_src = REPO_ROOT / "engine" / "python" / "csk_next" / "assets" / "engine_pack" / "skills_src"
        files = sorted(skills_src.rglob("SKILL.md"))
        self.assertTrue(files)
        for path in files:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), msg=str(path))
            end = text.find("\n---\n", len("---\n"))
            self.assertNotEqual(end, -1, msg=str(path))
            frontmatter = text[: end + len("\n---\n")]
            self.assertIn("name:", frontmatter, msg=str(path))
            self.assertIn("description:", frontmatter, msg=str(path))

    def test_phase00_contract_docs_freeze_is_consistent(self) -> None:
        contract = REPO_ROOT / "docs" / "CONTRACT.md"
        adr_0001 = REPO_ROOT / "docs" / "ADR" / "ADR-0001-module-state-location.md"
        adr_0002 = REPO_ROOT / "docs" / "ADR" / "ADR-0002-worktree-policy.md"
        evidence = REPO_ROOT / "docs" / "remediation_2026-02-26" / "phase-00-freeze-spec" / "EVIDENCE_INDEX.md"

        for path in [contract, adr_0001, adr_0002, evidence]:
            self.assertTrue(path.exists(), msg=str(path))

        contract_text = contract.read_text(encoding="utf-8")
        for marker in [
            "Scope and Isolation",
            "Canonical Directory Layout",
            "Canonical Task Lifecycle",
            "JSON Envelope Contract",
            "docs/remediation_2026-02-26/**",
            "summary",
            "status",
            "next",
            "refs",
            "errors",
            "ADR-0001",
            "ADR-0002",
        ]:
            self.assertIn(marker, contract_text)

        evidence_text = evidence.read_text(encoding="utf-8")
        self.assertIn("docs/CONTRACT.md", evidence_text)
        self.assertIn("docs/ADR/ADR-0001-module-state-location.md", evidence_text)
        self.assertIn("docs/ADR/ADR-0002-worktree-policy.md", evidence_text)

    def test_task_transition_map_rejects_illegal_skip(self) -> None:
        with self.assertRaises(ValueError):
            ensure_task_transition("draft", "plan_approved")

    def test_wizard_fsm_persistence_and_materialization(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")

            started = run_cli(root, "wizard", "start")
            self.assertEqual(started["status"], "ok")
            session_id = started["wizard"]["session_id"]
            session_root = root / ".csk" / "app" / "wizards" / session_id
            self.assertTrue((session_root / "session.json").exists())

            run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "Implement API endpoint")
            run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "app:modules/app")
            run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "single")
            run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "B")
            done = run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "yes")

            self.assertEqual(done["wizard"]["session_status"], "completed")
            result = done["wizard"]["result"]
            self.assertEqual(result["kind"], "single_module_task")
            task_path = Path(result["artifacts"]["task_path"])
            self.assertTrue((task_path / "plan.md").exists())
            self.assertTrue((task_path / "slices.json").exists())
            self.assertTrue((task_path / "decisions.jsonl").exists())
            self.assertTrue((session_root / "events.jsonl").exists())
            self.assertTrue((session_root / "result.json").exists())

    def test_wizard_module_mapping_suggestions_require_explicit_confirmation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")

            started = run_cli(root, "wizard", "start")
            session_id = started["wizard"]["session_id"]
            run_cli(root, "wizard", "answer", "--session-id", session_id, "--response", "Implement change in app module")
            view = run_cli(root, "wizard", "status", "--session-id", session_id)

            self.assertEqual(view["wizard"]["step"]["step_id"], "module_mapping")
            suggestions = view["wizard"]["step"]["suggestions"]
            self.assertGreater(len(suggestions), 0)
            self.assertTrue(all(bool(row["requires_explicit_confirm"]) for row in suggestions))
            self.assertIn("module_mapping_recommended", view["wizard"]["context"])
            self.assertNotIn("selected_modules", view["wizard"]["context"])

    def test_run_non_interactive_reports_missing_scripted_answers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(
                root,
                "run",
                "--answers-json",
                json.dumps({"answers": {"intake_request": "Incomplete answers payload"}}, ensure_ascii=False),
                "--non-interactive",
                expect_code=10,
            )
            self.assertEqual(payload["status"], "failed")
            data = user_data(payload)
            self.assertIn("wizard requires additional answers", data["error"])
            self.assertIn("module_mapping", data["missing_steps"])

    def test_run_without_executable_slice_starts_wizard(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(root, "run")
            self.assertEqual(payload["status"], "ok")
            data = user_data(payload)
            self.assertEqual(data["wizard"]["session_status"], "in_progress")
            self.assertEqual(data["wizard"]["step"]["step_id"], "intake_request")

    def test_run_progresses_planning_before_wizard(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            first = run_cli(root, "run")
            self.assertEqual(first["status"], "ok")
            state_after_first = run_cli(root, "task", "status", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(state_after_first["task"]["status"], "critic_passed")

            second = run_cli(root, "run")
            self.assertEqual(second["status"], "ok")
            state_after_second = run_cli(root, "task", "status", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(state_after_second["task"]["status"], "frozen")

            third = run_cli(root, "run")
            self.assertEqual(third["status"], "ok")
            self.assertIn("csk approve --module-id app", third["next"]["recommended"])
            self.assertIn(task_id, third["next"]["recommended"])
            self.assertFalse((root / ".csk" / "app" / "wizards").exists())

    def test_user_facing_commands_use_strict_envelope(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            created = run_cli(root, "new", "Envelope contract smoke", "--modules", "root")
            task_id = user_data(created)["task_id"]

            payloads = [
                run_cli(root, "status", "--json"),
                created,
                run_cli(root, "run"),
                run_cli(root, "replay", "--check"),
                run_cli(
                    root,
                    "retro",
                    "--module-id",
                    "root",
                    "--task-id",
                    task_id,
                    expect_code=2,
                ),
            ]
            expected_keys = {"summary", "status", "next", "refs", "errors", "data"}
            for payload in payloads:
                self.assertEqual(set(payload.keys()), expected_keys)

    def test_scope_required_empty_paths_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            slices_path = module_state_root(root, "mod/app") / "tasks" / task_id / "slices.json"
            slices = json.loads(slices_path.read_text(encoding="utf-8"))
            slices["slices"][0]["allowed_paths"] = []
            slices_path.write_text(json.dumps(slices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)
            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)
            run_cli(
                root,
                "task",
                "approve-plan",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )

            payload = run_cli(
                root,
                "slice",
                "run",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--slice-id",
                "S-0001",
                expect_code=10,
            )
            self.assertEqual(payload["status"], "gate_failed")
            self.assertEqual(payload["gate"], "scope")
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("scope_config_missing", incidents)

    def test_context_build_respects_module_root_allowed_path_dot(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            module_file = root / "mod" / "app" / "goal.txt"
            module_file.parent.mkdir(parents=True, exist_ok=True)
            module_file.write_text("goal token\n", encoding="utf-8")

            payload = run_cli(root, "context", "build", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(payload["status"], "ok")
            relevant_paths = [row["path"] for row in payload["bundle"]["relevant_files"]]
            self.assertIn("goal.txt", relevant_paths)

    def test_verify_required_empty_commands_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            slices_path = module_state_root(root, "mod/app") / "tasks" / task_id / "slices.json"
            slices = json.loads(slices_path.read_text(encoding="utf-8"))
            slices["slices"][0]["verify_commands"] = []
            slices_path.write_text(json.dumps(slices, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)
            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)
            run_cli(
                root,
                "task",
                "approve-plan",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )

            payload = run_cli(
                root,
                "slice",
                "run",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--slice-id",
                "S-0001",
                expect_code=10,
            )
            self.assertEqual(payload["status"], "gate_failed")
            self.assertEqual(payload["gate"], "verify")
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("verify_config_missing", incidents)

    def test_verify_policy_rejection_fails_slice_without_leaving_running_state(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)
            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)
            run_cli(
                root,
                "task",
                "approve-plan",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )

            payload = run_cli(
                root,
                "slice",
                "run",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--slice-id",
                "S-0001",
                "--verify-cmd",
                "curl https://example.com",
                expect_code=10,
            )
            self.assertIn(payload["status"], {"gate_failed", "blocked"})
            self.assertEqual(payload["gate"], "verify")

            task_state = json.loads(
                (module_state_root(root, "mod/app") / "tasks" / task_id / "task.json").read_text(encoding="utf-8")
            )
            self.assertNotEqual(task_state["slices"]["S-0001"]["status"], "running")
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("verify_policy_reject", incidents)

    def test_ready_uses_local_profile_override(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            profile_override = {
                "name": "default",
                "required_gates": ["scope", "verify", "review"],
                "default_commands": {},
                "e2e": {"required": False, "commands": []},
                "user_check_required": True,
                "recommended": {"linters": [], "test_frameworks": [], "skills": [], "mcp": []},
            }
            profile_path = root / ".csk" / "local" / "profiles" / "default.json"
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile_path.write_text(json.dumps(profile_override, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)
            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)
            run_cli(
                root,
                "task",
                "approve-plan",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )
            run_cli(
                root,
                "slice",
                "run",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--slice-id",
                "S-0001",
            )

            ready_fail = run_cli(
                root,
                "gate",
                "validate-ready",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                expect_code=10,
            )
            self.assertEqual(ready_fail["status"], "failed")
            self.assertFalse(ready_fail["ready"]["checks"]["user_check_recorded"]["passed"])

            user_check_path = (
                module_state_root(root, "mod/app") / "tasks" / task_id / "approvals" / "user_check.json"
            )
            user_check_path.parent.mkdir(parents=True, exist_ok=True)
            user_check_path.write_text(
                json.dumps({"approved_by": "tester", "approved_at": "2026-02-21T00:00:00Z"}, ensure_ascii=False, indent=2)
                + "\n",
                encoding="utf-8",
            )

            ready_ok = run_cli(root, "gate", "validate-ready", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(ready_ok["status"], "ok")

    def test_new_uses_local_default_profile_when_profile_flag_is_omitted(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "mod/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            config_path = root / ".csk" / "local" / "config.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "default_profile": "python",
                        "worktree_default": True,
                        "allowlist_commands": [],
                        "denylist_commands": ["rm", "sudo", "curl", "wget"],
                        "user_check_mode": "profile_optional",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            created = run_cli(root, "new", "Use local profile default", "--modules", "app")
            task_id = user_data(created)["task_id"]
            task_state = json.loads(
                (module_state_root(root, "mod/app") / "tasks" / task_id / "task.json").read_text(encoding="utf-8")
            )
            self.assertEqual(task_state["profile"], "python")

    def test_worktree_failure_fallback_incident(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            mission = run_cli(
                root,
                "mission",
                "new",
                "--title",
                "Worktree fallback",
                "--summary",
                "No git repo",
                "--modules",
                "app",
                "--no-task-stubs",
            )
            self.assertEqual(mission["status"], "ok")
            worktrees_path = root / ".csk" / "app" / "missions" / mission["mission_id"] / "worktrees.json"
            worktrees = json.loads(worktrees_path.read_text(encoding="utf-8"))
            self.assertIn("app", worktrees["opt_out_modules"])
            self.assertFalse(worktrees["create_status"]["app"]["created"])
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("worktree_create_failed", incidents)

    def test_gate_verify_requires_command(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]
            payload = run_cli(
                root,
                "gate",
                "verify",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--slice-id",
                "S-0001",
                expect_code=10,
            )
            self.assertEqual(payload["status"], "failed")
            self.assertFalse(payload["proof"]["passed"])

    def test_retro_alias_without_subcommand(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "module", "add", "--path", "modules/app", "--module-id", "app")
            run_cli(root, "module", "init", "--module-id", "app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            payload = run_cli(
                root,
                "retro",
                "--module-id",
                "app",
                "--task-id",
                task["task_id"],
                expect_code=2,
            )
            self.assertEqual(payload["status"], "error")
            errors = payload.get("errors", [])
            self.assertTrue(any("Retro requires task status" in row for row in errors))
            self.assertIn("next", payload)

    def test_approve_error_includes_next_for_user_flow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(
                root,
                "approve",
                "--module-id",
                "root",
                "--task-id",
                "T-0001",
                "--approved-by",
                "tester",
                expect_code=2,
            )
            self.assertEqual(payload["status"], "error")
            self.assertIn("next", payload)
            self.assertIn("recommended", payload["next"])

    def test_replay_exit_code_30_on_invariant_violation(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(
                root,
                "event",
                "append",
                "--type",
                "proof.pack.written",
                "--payload",
                '{"manifest_path":"/definitely/missing/manifest.json"}',
            )
            replay = run_cli(root, "replay", "--check", expect_code=30)
            self.assertEqual(replay["status"], "replay_failed")
            self.assertGreater(len(user_data(replay)["replay"]["violations"]), 0)

    def test_replay_error_includes_next_for_user_flow(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(root, "replay", expect_code=2)
            self.assertEqual(payload["status"], "error")
            self.assertIn("next", payload)
            self.assertEqual(payload["next"]["recommended"], "csk replay --check")

    def test_completion_prints_raw_script(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env = dict(os.environ)
            env["PYTHONPATH"] = PYTHONPATH
            proc = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "csk_next.cli.main",
                    "--root",
                    str(root),
                    "completion",
                    "bash",
                ],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(proc.returncode, 0)
            self.assertIn("complete -F _csk_complete csk", proc.stdout)
            self.assertNotIn('"status": "ok"', proc.stdout)

    def test_short_csk_entrypoint_script_is_present(self) -> None:
        script = REPO_ROOT / "csk"
        wrapper = REPO_ROOT / "tools" / "csk"
        self.assertTrue(script.exists())
        self.assertTrue(wrapper.exists())
        entrypoint = script.read_text(encoding="utf-8")
        self.assertIn('STATE_ROOT="${CSK_STATE_ROOT:-${REPO_ROOT}}"', entrypoint)
        self.assertIn("python -m csk_next.cli.main", entrypoint)

    def test_generated_skills_include_csk_status(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            generated = root / ".agents" / "skills" / "csk-status" / "SKILL.md"
            self.assertTrue(generated.exists())
            text = generated.read_text(encoding="utf-8")
            self.assertIn("$csk-status", text)
            self.assertIn("NEXT:", text)

    def test_generated_skills_keep_frontmatter_before_generated_marker(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            generated = root / ".agents" / "skills" / "csk" / "SKILL.md"
            text = generated.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            end = text.find("\n---\n", len("---\n"))
            self.assertNotEqual(end, -1)
            frontmatter = text[: end + len("\n---\n")]
            self.assertNotIn("GENERATED: do not edit by hand", frontmatter)
            tail = text[end + len("\n---\n") :].lstrip("\n")
            self.assertTrue(tail.startswith("<!-- GENERATED: do not edit by hand -->"))

    def test_generated_csk_router_has_runnable_approve_and_retro_next_commands(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            generated = root / ".agents" / "skills" / "csk" / "SKILL.md"
            text = generated.read_text(encoding="utf-8")
            self.assertIn(
                "csk approve --module-id <module_id_from_status> --task-id <active_task_id_from_status> --approved-by <human>",
                text,
            )
            self.assertIn(
                "csk retro run --module-id <module_id_from_status> --task-id <active_task_id_from_status>",
                text,
            )
            self.assertNotIn("-> suggest `csk approve`.", text)
            self.assertNotIn("-> suggest `csk retro`.", text)

    def test_validate_skills_detects_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            skill_files = sorted((root / ".agents" / "skills").rglob("SKILL.md"))
            self.assertTrue(skill_files)
            generated_skill = skill_files[0]
            generated_skill.write_text(generated_skill.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")

            payload = run_cli(root, "validate", "--skills", expect_code=10)
            self.assertEqual(payload["status"], "failed")
            self.assertTrue(payload["skills"]["modified"])

    def test_validate_skills_detects_non_markdown_drift(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            override_dir = root / ".csk" / "local" / "skills_override" / "custom"
            override_dir.mkdir(parents=True, exist_ok=True)
            (override_dir / "SKILL.md").write_text("# custom skill\n", encoding="utf-8")
            (override_dir / "template.txt").write_text("version-1\n", encoding="utf-8")

            run_cli(root, "skills", "generate")
            generated = root / ".agents" / "skills" / "custom" / "template.txt"
            self.assertTrue(generated.exists())
            generated.write_text("drifted\n", encoding="utf-8")

            payload = run_cli(root, "validate", "--skills", expect_code=10)
            self.assertEqual(payload["status"], "failed")
            self.assertIn("custom/template.txt", payload["skills"]["modified"])

    def test_event_log_bootstrap_started_completed_and_idempotent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            run_cli(root, "bootstrap")

            tail = run_cli(root, "event", "tail", "--n", "20")
            self.assertEqual(tail["status"], "ok")
            bootstrap_events = [
                row for row in tail["events"] if row.get("payload", {}).get("command") == "bootstrap"
            ]
            self.assertEqual(len(bootstrap_events), 4)
            self.assertEqual(
                sorted(row["type"] for row in bootstrap_events),
                ["command.completed", "command.completed", "command.started", "command.started"],
            )

    def test_event_append_and_tail_filters(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_cli(root, "bootstrap")
            payload = run_cli(
                root,
                "event",
                "append",
                "--type",
                "plan.drafted",
                "--actor",
                "assistant:coder",
                "--module-id",
                "app",
                "--task-id",
                "T-0001",
                "--payload",
                '{"reason":"seed"}',
                "--artifact-ref",
                "tasks/T-0001/plan.md",
            )
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["event"]["type"], "plan.drafted")

            tail = run_cli(root, "event", "tail", "--n", "5", "--type", "plan.drafted")
            self.assertEqual(tail["status"], "ok")
            self.assertEqual(len(tail["events"]), 1)
            event = tail["events"][0]
            self.assertEqual(event["type"], "plan.drafted")
            self.assertEqual(event["actor"], "assistant:coder")
            self.assertEqual(event["module_id"], "app")
            self.assertEqual(event["task_id"], "T-0001")
            self.assertEqual(event["payload"]["reason"], "seed")
            self.assertEqual(event["artifact_refs"], ["tasks/T-0001/plan.md"])

    def test_event_log_does_not_crash_without_git_in_path(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            env = {"PATH": "/tmp"}
            bootstrap = run_cli(root, "bootstrap", env_overrides=env)
            self.assertEqual(bootstrap["status"], "ok")

            tail = run_cli(root, "event", "tail", "--n", "20", env_overrides=env)
            self.assertEqual(tail["status"], "ok")
            bootstrap_started = [
                row
                for row in tail["events"]
                if row["type"] == "command.started" and row.get("payload", {}).get("command") == "bootstrap"
            ]
            self.assertEqual(len(bootstrap_started), 1)
            self.assertIsNone(bootstrap_started[0]["repo_git_head"])


if __name__ == "__main__":
    unittest.main()
