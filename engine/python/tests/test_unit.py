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
from csk_next.skills.generator import generate_skills


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH = str(REPO_ROOT / "engine" / "python")


def run_cli(root: Path, *args: str, expect_code: int = 0) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHONPATH
    proc = subprocess.run(
        [sys.executable, "-m", "csk_next.cli.main", "--root", str(root), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != expect_code:
        raise AssertionError(proc.stdout + proc.stderr)
    return json.loads(proc.stdout)


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

            plan = root / "mod" / "app" / ".csk" / "tasks" / task_id / "plan.md"
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

            slices_path = root / "mod" / "app" / ".csk" / "tasks" / task_id / "slices.json"
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

            slices_path = root / "mod" / "app" / ".csk" / "tasks" / task_id / "slices.json"
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

            user_check_path = root / "mod" / "app" / ".csk" / "tasks" / task_id / "approvals" / "user_check.json"
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


if __name__ == "__main__":
    unittest.main()
