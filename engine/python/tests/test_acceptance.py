"""Integration and acceptance tests for CSK-Next."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHONPATH = str(REPO_ROOT / "engine" / "python")


def run_cli(
    root: Path,
    *args: str,
    expect_code: int | None = 0,
    state_root: Path | None = None,
) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHONPATH
    command = [sys.executable, "-m", "csk_next.cli.main", "--root", str(root)]
    if state_root is not None:
        command.extend(["--state-root", str(state_root)])
    command.extend(args)
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    if expect_code is not None and proc.returncode != expect_code:
        raise AssertionError(proc.stdout + proc.stderr)
    return json.loads(proc.stdout)


def run_phase01_acceptance_a_harness(root: Path) -> dict:
    module_path = Path(__file__).with_name("test_acceptance_a_greenfield.py")
    spec = importlib.util.spec_from_file_location("phase01_acceptance_a_harness", module_path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load strict harness from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    scenario = getattr(module, "run_acceptance_a_greenfield_scenario", None)
    if scenario is None:
        raise AssertionError("run_acceptance_a_greenfield_scenario not found")
    result = scenario(root)
    if not isinstance(result, dict):
        raise AssertionError("Strict harness returned non-dict result")
    return result


def module_state_root(root: Path, module_path: str) -> Path:
    return root / ".csk" / "modules" / Path(module_path)


def user_data(payload: dict) -> dict:
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return payload


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
    def test_run_with_external_state_root(self) -> None:
        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as state_dir:
            root = Path(temp_dir)
            state_root = Path(state_dir) / "state"
            self.assertEqual(run_cli(root, "bootstrap", state_root=state_root)["status"], "ok")

            payload = run_cli(
                root,
                "run",
                "--request",
                "Implement scoped change",
                "--modules",
                "app:modules/app",
                "--shape",
                "single",
                "--plan-option",
                "B",
                "--yes",
                "--non-interactive",
                state_root=state_root,
            )
            self.assertEqual(payload["status"], "ok")
            self.assertTrue((state_root / ".csk" / "app" / "registry.json").exists())
            self.assertFalse((root / ".csk").exists())

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
            wizard = user_data(payload)["wizard"]
            self.assertEqual(wizard["session_status"], "completed")
            self.assertEqual(wizard["result"]["kind"], "single_module_task")
            artifacts = wizard["result"]["artifacts"]
            self.assertTrue(Path(artifacts["task_path"]).exists())
            self.assertTrue((module_state_root(root, "modules/app") / "module" / "kernel.json").exists())

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
            wizard = user_data(payload)["wizard"]
            self.assertEqual(wizard["session_status"], "completed")
            result = wizard["result"]
            self.assertEqual(result["kind"], "multi_module_mission")
            self.assertEqual(len(result["artifacts"]["tasks_created"]), 2)
            self.assertTrue((module_state_root(root, "modules/owner") / "module" / "kernel.json").exists())
            self.assertTrue((module_state_root(root, "modules/consumer") / "module" / "kernel.json").exists())

    def test_acceptance_a_greenfield(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = run_phase01_acceptance_a_harness(root)
            self.assertEqual(result["status"], "ok")

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
                expect_code=2,
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
                expect_code=10,
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
                expect_code=2,
            )
            self.assertEqual(retro["status"], "error")
            self.assertTrue(any("ready_approved or blocked" in row for row in retro.get("errors", [])))
            self.assertFalse((module_state_root(root, "modules/app") / "tasks" / task_id / "retro.md").exists())

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
                expect_code=10,
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
                expect_code=10,
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
                expect_code=10,
            )
            self.assertEqual(third["status"], "blocked")

            doctor = run_cli(root, "doctor", "run", "--command", "definitely_missing_cmd", expect_code=10)
            self.assertEqual(doctor["status"], "failed")

            incidents = (root / ".csk" / "app" / "logs" / "incidents.jsonl").read_text(encoding="utf-8")
            self.assertIn("verify_fail", incidents)
            self.assertIn("command_not_found", incidents)

    def test_public_cli_flow_with_aliases_and_replay(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            setup_module(root, "app", "modules/app")

            created = run_cli(root, "new", "Implement API hardening", "--modules", "app")
            self.assertEqual(created["status"], "ok")
            created_data = user_data(created)
            self.assertEqual(created_data["kind"], "single_module_task")
            task_id = created_data["task_id"]

            self.assertEqual(
                run_cli(root, "plan", "critic", "--module-id", "app", "--task-id", task_id)["status"],
                "ok",
            )
            self.assertEqual(
                run_cli(root, "plan", "freeze", "--module-id", "app", "--task-id", task_id)["status"],
                "ok",
            )

            plan_approval = run_cli(
                root,
                "approve",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )
            self.assertEqual(plan_approval["status"], "ok")
            self.assertEqual(user_data(plan_approval)["kind"], "plan")

            run_first = run_cli(root, "run")
            self.assertEqual(run_first["status"], "done")

            run_second = run_cli(root, "run")
            self.assertEqual(run_second["status"], "ok")

            ready_approval = run_cli(
                root,
                "approve",
                "--module-id",
                "app",
                "--task-id",
                task_id,
                "--approved-by",
                "tester",
            )
            self.assertEqual(ready_approval["status"], "ok")
            self.assertEqual(user_data(ready_approval)["kind"], "ready")

            retro = run_cli(
                root,
                "retro",
                "--module-id",
                "app",
                "--task-id",
                task_id,
            )
            self.assertEqual(retro["status"], "ok")
            self.assertTrue(Path(user_data(retro)["patch_file"]).exists())

            context = run_cli(root, "context", "build", "--module-id", "app", "--task-id", task_id)
            self.assertEqual(context["status"], "ok")
            self.assertTrue(Path(context["bundle_path"]).exists())

            pkm = run_cli(root, "pkm", "build", "--module-id", "app")
            self.assertEqual(pkm["status"], "ok")
            self.assertGreaterEqual(pkm["items_written"], 1)

            replay = run_cli(root, "replay", "--check")
            self.assertEqual(replay["status"], "ok")
            self.assertEqual(user_data(replay)["replay"]["status"], "ok")

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

    def test_acceptance_f_skills_drift_recovery(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.assertEqual(run_cli(root, "bootstrap")["status"], "ok")
            self.assertEqual(run_cli(root, "validate", "--all", "--strict", "--skills")["status"], "ok")

            skill_files = sorted((root / ".agents" / "skills").rglob("SKILL.md"))
            self.assertTrue(skill_files)
            skill = skill_files[0]
            skill.write_text(skill.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")

            status = run_cli(root, "status", "--json")
            self.assertEqual(user_data(status)["skills"]["status"], "failed")
            self.assertEqual(status["next"]["recommended"], "csk skills generate")

            failed = run_cli(root, "validate", "--all", "--strict", "--skills", expect_code=10)
            self.assertEqual(failed["status"], "failed")

            self.assertEqual(run_cli(root, "skills", "generate")["status"], "ok")
            self.assertEqual(run_cli(root, "validate", "--all", "--strict", "--skills")["status"], "ok")

    def test_acceptance_g_clean_state_gate_pack(self) -> None:
        with TemporaryDirectory() as temp_dir, TemporaryDirectory() as state_dir:
            root = Path(temp_dir)
            state_root = Path(state_dir) / "state"
            self.assertEqual(run_cli(root, "bootstrap", state_root=state_root)["status"], "ok")
            self.assertEqual(
                run_cli(root, "validate", "--all", "--strict", "--skills", state_root=state_root)["status"],
                "ok",
            )
            self.assertEqual(run_cli(root, "replay", "--check", state_root=state_root)["status"], "ok")
            self.assertEqual(run_cli(root, "doctor", "run", "--git-boundary", state_root=state_root)["status"], "ok")


if __name__ == "__main__":
    unittest.main()
