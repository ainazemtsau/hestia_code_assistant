"""Integration and acceptance tests for CSK-Next."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH = str(REPO_ROOT / "engine" / "python")


def run_cli(root: Path, *args: str, expect_code: int | None = 0) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHONPATH
    proc = subprocess.run(
        [sys.executable, "-m", "csk_next.cli.main", "--root", str(root), *args],
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if expect_code is not None and proc.returncode != expect_code:
        raise AssertionError(proc.stdout + proc.stderr)
    return json.loads(proc.stdout)


def setup_module(root: Path, module_id: str, module_path: str) -> None:
    add_payload = run_cli(root, "module", "add", "--path", module_path, "--module-id", module_id)
    if add_payload["status"] != "ok":
        raise AssertionError(add_payload)
    init_payload = run_cli(root, "module", "init", "--module-id", module_id)
    if init_payload["status"] != "ok":
        raise AssertionError(init_payload)


def init_git_repo(root: Path) -> None:
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


def approve_plan(root: Path, module_id: str, task_id: str) -> None:
    critic = run_cli(root, "task", "critic", "--module-id", module_id, "--task-id", task_id)
    if critic["status"] != "ok":
        raise AssertionError(critic)
    freeze = run_cli(root, "task", "freeze", "--module-id", module_id, "--task-id", task_id)
    if freeze["status"] != "ok":
        raise AssertionError(freeze)
    approve = run_cli(
        root,
        "task",
        "approve-plan",
        "--module-id",
        module_id,
        "--task-id",
        task_id,
        "--approved-by",
        "tester",
    )
    if approve["status"] != "ok":
        raise AssertionError(approve)


def run_slice_to_done(root: Path, module_id: str, task_id: str, verify_cmd: str | None = None) -> None:
    args = [
        "slice",
        "run",
        "--module-id",
        module_id,
        "--task-id",
        task_id,
        "--slice-id",
        "S-0001",
        "--implement",
        "python -c \"print('ok')\"",
    ]
    if verify_cmd is not None:
        args.extend(["--verify-cmd", verify_cmd])
    payload = run_cli(root, *args)
    if payload["status"] != "done":
        raise AssertionError(payload)


def ready_and_retro(root: Path, module_id: str, task_id: str) -> None:
    ready = run_cli(root, "gate", "validate-ready", "--module-id", module_id, "--task-id", task_id)
    if ready["status"] != "ok":
        raise AssertionError(ready)
    approve = run_cli(
        root,
        "gate",
        "approve-ready",
        "--module-id",
        module_id,
        "--task-id",
        task_id,
        "--approved-by",
        "tester",
    )
    if approve["status"] != "ok":
        raise AssertionError(approve)
    retro = run_cli(root, "retro", "run", "--module-id", module_id, "--task-id", task_id)
    if retro["status"] != "ok":
        raise AssertionError(retro)


class AcceptanceTests(unittest.TestCase):
    def test_run_single_module_planning_entrypoint(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")

            payload = run_cli(
                root,
                "run",
                "--request",
                "Implement small API change",
                "--modules",
                "app:modules/app",
                "--shape",
                "single",
                "--plan-option",
                "B",
                "--yes",
                "--non-interactive",
            )
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["wizard"]["session_status"], "completed")
            self.assertEqual(payload["wizard"]["result"]["kind"], "single_module_task")
            artifacts = payload["wizard"]["result"]["artifacts"]
            self.assertTrue(Path(artifacts["task_path"]).exists())
            self.assertTrue((root / "modules" / "app" / ".csk" / "module" / "kernel.json").exists())

    def test_run_multi_module_routing_and_lazy_init(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")

            payload = run_cli(
                root,
                "run",
                "--request",
                "Change owner API and adapt consumer",
                "--modules",
                "owner:modules/owner,consumer:modules/consumer",
                "--shape",
                "multi",
                "--plan-option",
                "B",
                "--yes",
                "--non-interactive",
            )
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["wizard"]["session_status"], "completed")
            result = payload["wizard"]["result"]
            self.assertEqual(result["kind"], "multi_module_mission")
            self.assertEqual(len(result["artifacts"]["tasks_created"]), 2)
            self.assertTrue((root / "modules" / "owner" / ".csk" / "module" / "kernel.json").exists())
            self.assertTrue((root / "modules" / "consumer" / ".csk" / "module" / "kernel.json").exists())

    def test_acceptance_a_greenfield(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")

            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]

            approve_plan(root, "app", task_id)
            run_slice_to_done(root, "app", task_id)
            ready_and_retro(root, "app", task_id)

            strict = run_cli(root, "validate", "--all", "--strict")
            self.assertEqual(strict["status"], "ok")

    def test_acceptance_b_brownfield_multi_module(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "services").mkdir(parents=True, exist_ok=True)
            (root / "packages").mkdir(parents=True, exist_ok=True)

            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "svc", "services/svc")
            setup_module(root, "pkg", "packages/pkg")

            mission = run_cli(
                root,
                "mission",
                "new",
                "--title",
                "Brownfield",
                "--summary",
                "Pilot modules",
                "--modules",
                "svc",
                "pkg",
            )
            self.assertEqual(mission["status"], "ok")
            self.assertEqual(len(mission["tasks_created"]), 2)

            status = run_cli(root, "mission", "status", "--mission-id", mission["mission_id"])
            self.assertEqual(status["status"], "ok")
            self.assertEqual(len(status["routing"]["module_routes"]), 2)

    def test_mission_rejects_unknown_modules(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            payload = run_cli(
                root,
                "mission",
                "new",
                "--title",
                "Invalid mission",
                "--summary",
                "Unknown module id",
                "--modules",
                "ghost",
                "--no-task-stubs",
                expect_code=1,
            )
            self.assertEqual(payload["status"], "error")
            self.assertIn("Module not found", payload["error"])

    def test_worktree_create_success_in_git_repo(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            init_git_repo(root)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")
            mission = run_cli(
                root,
                "mission",
                "new",
                "--title",
                "Git worktree mission",
                "--summary",
                "Create real worktree",
                "--modules",
                "app",
                "--no-task-stubs",
            )
            self.assertEqual(mission["status"], "ok")
            worktrees = json.loads(
                (root / ".csk" / "app" / "missions" / mission["mission_id"] / "worktrees.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(worktrees["create_status"]["app"]["created"])
            self.assertTrue(Path(worktrees["module_worktrees"]["app"]).exists())

    def test_acceptance_c_cross_module_api_change(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "owner", "modules/owner")
            setup_module(root, "consumer", "modules/consumer")

            mission = run_cli(
                root,
                "mission",
                "new",
                "--title",
                "API change",
                "--summary",
                "Owner + consumer",
                "--modules",
                "owner",
                "consumer",
            )
            tasks = mission["tasks_created"]
            self.assertEqual(len(tasks), 2)

            for module_id, task_id in zip(["owner", "consumer"], tasks, strict=True):
                approve_plan(root, module_id, task_id)
                run_slice_to_done(root, module_id, task_id)
                ready_and_retro(root, module_id, task_id)

            strict = run_cli(root, "validate", "--all", "--strict")
            self.assertEqual(strict["status"], "ok")

    def test_ready_validation_fails_on_missing_proofs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]
            approve_plan(root, "app", task_id)
            ready = run_cli(
                root,
                "gate",
                "validate-ready",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                expect_code=1,
            )
            self.assertEqual(ready["status"], "failed")
            self.assertFalse(ready["ready"]["checks"]["verify_coverage_ok"]["passed"])

    def test_retro_denied_before_ready_approval(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")
            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]
            approve_plan(root, "app", task_id)
            run_slice_to_done(root, "app", task_id)
            ready = run_cli(root, "gate", "validate-ready", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(ready["status"], "ok")
            retro = run_cli(
                root,
                "retro",
                "run",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                expect_code=1,
            )
            self.assertEqual(retro["status"], "error")
            self.assertIn("ready_approved or blocked", retro["error"])
            self.assertFalse((root / "modules" / "app" / ".csk" / "tasks" / task_id / "retro.md").exists())

    def test_acceptance_d_failures_and_doctor(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")

            task = run_cli(root, "task", "new", "--module-id", "app")
            task_id = task["task_id"]
            approve_plan(root, "app", task_id)

            fail_cmd = "python -c \"import sys; sys.exit(1)\""
            first = run_cli(
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
                fail_cmd,
                expect_code=1,
            )
            self.assertEqual(first["status"], "gate_failed")

            second = run_cli(
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
                fail_cmd,
                expect_code=1,
            )
            self.assertIn(second["status"], {"gate_failed", "blocked"})

            third = run_cli(
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
            self.assertEqual(third["status"], "blocked")

            doctor = run_cli(root, "doctor", "run", "--command", "definitely_missing_cmd", expect_code=1)
            self.assertEqual(doctor["status"], "failed")

            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("verify_fail", incidents)
            self.assertIn("command_not_found", incidents)

    def test_acceptance_e_update_and_overlay_preserved(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")

            override_dir = root / ".csk" / "local" / "skills_override" / "csk"
            override_dir.mkdir(parents=True, exist_ok=True)
            override_file = override_dir / "SKILL.md"
            override_file.write_text("# $csk override\n", encoding="utf-8")

            before = override_file.read_text(encoding="utf-8")
            update = run_cli(root, "update", "engine")
            self.assertEqual(update["status"], "ok")

            after = override_file.read_text(encoding="utf-8")
            self.assertEqual(before, after)

            generated = root / ".agents" / "skills" / "csk" / "SKILL.md"
            self.assertTrue(generated.exists())
            self.assertIn("override", generated.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
