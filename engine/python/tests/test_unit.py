"""Unit tests for core utilities."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
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
                expect_code=1,
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
            app_row = next(row for row in status_payload["modules"] if row["module_id"] == "app")
            self.assertEqual(app_row["phase"], "PLANNING")
            self.assertEqual(app_row["active_task_id"], task_id)
            self.assertIn("task critic", status_payload["next"]["recommended"])

            run_cli(root, "task", "critic", "--module-id", "app", "--task-id", task_id)

            critic_passed_payload = run_cli(root, "status", "--json")
            critic_passed_row = next(row for row in critic_passed_payload["modules"] if row["module_id"] == "app")
            self.assertEqual(critic_passed_row["phase"], "PLANNING")
            self.assertEqual(critic_passed_row["task_status"], "critic_passed")
            self.assertIn("task freeze", critic_passed_payload["next"]["recommended"])

            module_critic_payload = run_cli(root, "module", "status", "--module-id", "app")
            self.assertEqual(module_critic_payload["module"]["phase"], "PLANNING")
            self.assertIn("task freeze", module_critic_payload["next"]["recommended"])

            run_cli(root, "task", "freeze", "--module-id", "app", "--task-id", task_id)

            frozen_payload = run_cli(root, "status", "--json")
            frozen_row = next(row for row in frozen_payload["modules"] if row["module_id"] == "app")
            self.assertEqual(frozen_row["phase"], "PLAN_FROZEN")
            self.assertIn("approve-plan", frozen_payload["next"]["recommended"])

            run_cli(root, "task", "approve-plan", "--module-id", "app", "--task-id", task_id, "--approved-by", "tester")
            layout = resolve_layout(root)
            mark_task_status(layout, "modules/app", task_id, "executing")
            mark_task_blocked(layout, "modules/app", task_id, "verify retries exceeded")

            blocked_payload = run_cli(root, "status", "--json")
            blocked_row = next(row for row in blocked_payload["modules"] if row["module_id"] == "app")
            self.assertEqual(blocked_row["phase"], "BLOCKED")
            self.assertIn("retro run", blocked_payload["next"]["recommended"])

            module_blocked_payload = run_cli(root, "module", "status", "--module-id", "app")
            self.assertEqual(module_blocked_payload["module"]["phase"], "BLOCKED")
            self.assertIn("retro run", module_blocked_payload["next"]["recommended"])

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
            self.assertEqual(alias_payload["module"]["module_id"], "app")
            self.assertEqual(alias_payload["module"]["phase"], "PLANNING")
            self.assertIsNotNone(alias_payload["module"]["worktree_path"])
            self.assertIsNotNone(alias_payload["cd_hint"])
            self.assertTrue(alias_payload["cd_hint"].startswith("cd "))
            self.assertIn("task critic", alias_payload["next"]["recommended"])

            status_payload = run_cli(root, "module", "status", "--module-id", "app")
            self.assertEqual(status_payload["status"], "ok")
            self.assertEqual(status_payload["module"]["module_id"], "app")
            self.assertEqual(status_payload["module"]["phase"], alias_payload["module"]["phase"])

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
            self.assertEqual((out / "alpha" / "SKILL.md").read_text(encoding="utf-8"), "override")

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
                expect_code=1,
            )
            self.assertEqual(payload["status"], "gate_failed")
            self.assertEqual(payload["gate"], "scope")
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("scope_config_missing", incidents)

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
                expect_code=1,
            )
            self.assertEqual(payload["status"], "gate_failed")
            self.assertEqual(payload["gate"], "verify")
            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("verify_config_missing", incidents)

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
                expect_code=1,
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
                expect_code=1,
            )
            self.assertEqual(payload["status"], "failed")
            self.assertFalse(payload["proof"]["passed"])

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
