"""Strict phase-01 acceptance A tests for deterministic greenfield E2E."""

from __future__ import annotations

import json
import os
import sqlite3
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
    expect_code: int = 0,
) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = PYTHONPATH
    command = [sys.executable, "-m", "csk_next.cli.main", "--root", str(root), "--state-root", str(root)]
    command.extend(args)
    proc = subprocess.run(
        command,
        text=True,
        capture_output=True,
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


def task_root(root: Path, task_id: str, module_path: str = ".") -> Path:
    return module_state_root(root, module_path) / "tasks" / task_id


def task_run_root(root: Path, task_id: str, module_path: str = ".") -> Path:
    return module_state_root(root, module_path) / "run" / "tasks" / task_id


def configure_two_slice_fixture(root: Path, task_id: str) -> None:
    root_path = task_root(root, task_id)
    slices_path = root_path / "slices.json"
    task_state_path = root_path / "task.json"

    slices_doc = json.loads(slices_path.read_text(encoding="utf-8"))
    if len(slices_doc.get("slices", [])) != 2:
        raise AssertionError("task fixture must be initialized with exactly two slices")
    base_slice_one = dict(slices_doc["slices"][0])
    base_slice_two = dict(slices_doc["slices"][1])
    max_attempts = int(base_slice_one.get("max_attempts", 2))

    slice_one = dict(base_slice_one)
    slice_one.update(
        {
            "slice_id": "S-0001",
            "title": "Slice S-0001",
            "deps": [],
            "allowed_paths": ["phase01_slice1.txt"],
            "verify_commands": ['python -c "print(\'verify s1 ok\')"'],
            "traceability": ["phase-01.acceptance-a"],
        }
    )

    slice_two = dict(base_slice_two)
    slice_two.update(
        {
            "slice_id": "S-0002",
            "title": "Slice S-0002",
            "deps": ["S-0001"],
            "allowed_paths": ["phase01_slice2.txt"],
            "verify_commands": ['python -c "print(\'verify s2 ok\')"'],
            "traceability": ["phase-01.acceptance-a"],
        }
    )

    slices_doc["slices"] = [slice_one, slice_two]
    slices_path.write_text(json.dumps(slices_doc, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    task_state = json.loads(task_state_path.read_text(encoding="utf-8"))
    task_state["slices"] = {
        "S-0001": {"status": "pending", "attempts": 0, "max_attempts": max_attempts},
        "S-0002": {"status": "pending", "attempts": 0, "max_attempts": max_attempts},
    }
    task_state_path.write_text(json.dumps(task_state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def event_types_for_task(root: Path, task_id: str) -> list[str]:
    eventlog = root / ".csk" / "app" / "eventlog.sqlite"
    if not eventlog.exists():
        raise AssertionError(f"Event log not found: {eventlog}")
    with sqlite3.connect(eventlog) as connection:
        rows = connection.execute(
            "SELECT type FROM events WHERE task_id = ? ORDER BY ts ASC, rowid ASC",
            (task_id,),
        ).fetchall()
    return [str(row[0]) for row in rows]


def run_acceptance_a_greenfield_scenario(root: Path) -> dict:
    bootstrap = run_cli(root, "bootstrap")
    if bootstrap["status"] != "ok":
        raise AssertionError(bootstrap)

    add = run_cli(root, "module", "add", "--path", ".", "--module-id", "root")
    if add["status"] != "ok":
        raise AssertionError(add)

    init = run_cli(root, "module", "init", "--module-id", "root", "--write-scaffold")
    if init["status"] != "ok":
        raise AssertionError(init)

    created = run_cli(root, "task", "new", "--module-id", "root", "--slice-count", "2")
    if created["status"] != "ok":
        raise AssertionError(created)
    task_id = str(created["task_id"])
    configure_two_slice_fixture(root, task_id)

    critic = run_cli(root, "task", "critic", "--module-id", "root", "--task-id", task_id)
    if critic["status"] != "ok":
        raise AssertionError(critic)

    freeze = run_cli(root, "task", "freeze", "--module-id", "root", "--task-id", task_id)
    if freeze["status"] != "ok":
        raise AssertionError(freeze)

    approve_plan = run_cli(
        root,
        "task",
        "approve-plan",
        "--module-id",
        "root",
        "--task-id",
        task_id,
        "--approved-by",
        "tester",
    )
    if approve_plan["status"] != "ok":
        raise AssertionError(approve_plan)

    implement_s1 = (
        "python -c \"from pathlib import Path; "
        "Path('phase01_slice1.txt').write_text('slice1\\n', encoding='utf-8')\""
    )
    slice_one = run_cli(
        root,
        "slice",
        "run",
        "--module-id",
        "root",
        "--task-id",
        task_id,
        "--slice-id",
        "S-0001",
        "--implement",
        implement_s1,
    )
    if slice_one["status"] != "done":
        raise AssertionError(slice_one)

    implement_s2 = (
        "python -c \"from pathlib import Path; "
        "Path('phase01_slice2.txt').write_text('slice2\\n', encoding='utf-8')\""
    )
    slice_two = run_cli(
        root,
        "slice",
        "run",
        "--module-id",
        "root",
        "--task-id",
        task_id,
        "--slice-id",
        "S-0002",
        "--implement",
        implement_s2,
    )
    if slice_two["status"] != "done":
        raise AssertionError(slice_two)

    ready = run_cli(root, "gate", "validate-ready", "--module-id", "root", "--task-id", task_id)
    if ready["status"] != "ok":
        raise AssertionError(ready)

    approve_ready = run_cli(
        root,
        "gate",
        "approve-ready",
        "--module-id",
        "root",
        "--task-id",
        task_id,
        "--approved-by",
        "tester",
    )
    if approve_ready["status"] != "ok":
        raise AssertionError(approve_ready)

    retro = run_cli(root, "retro", "run", "--module-id", "root", "--task-id", task_id)
    if retro["status"] != "ok":
        raise AssertionError(retro)

    replay = run_cli(root, "replay", "--check")
    if replay["status"] != "ok":
        raise AssertionError(replay)

    return {
        "status": "ok",
        "task_id": task_id,
        "task_root": task_root(root, task_id),
        "task_run_root": task_run_root(root, task_id),
        "retro": user_data(retro),
        "replay": user_data(replay),
        "event_types": event_types_for_task(root, task_id),
    }


class AcceptanceAGreenfieldTests(unittest.TestCase):
    def test_acceptance_a_greenfield_strict_positive(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = run_acceptance_a_greenfield_scenario(root)
            task_id = str(result["task_id"])
            task_root_path = Path(result["task_root"])
            run_root_path = Path(result["task_run_root"])

            required_task_artifacts = [
                task_root_path / "task.json",
                task_root_path / "plan.md",
                task_root_path / "slices.json",
                task_root_path / "critic.json",
                task_root_path / "freeze.json",
                task_root_path / "approvals" / "plan.json",
                task_root_path / "approvals" / "ready.json",
                task_root_path / "retro.md",
            ]
            required_run_artifacts = [
                run_root_path / "proofs" / "S-0001" / "scope.json",
                run_root_path / "proofs" / "S-0001" / "verify.json",
                run_root_path / "proofs" / "S-0001" / "review.json",
                run_root_path / "proofs" / "S-0001" / "manifest.json",
                run_root_path / "proofs" / "S-0002" / "scope.json",
                run_root_path / "proofs" / "S-0002" / "verify.json",
                run_root_path / "proofs" / "S-0002" / "review.json",
                run_root_path / "proofs" / "S-0002" / "manifest.json",
                run_root_path / "proofs" / "ready.json",
                run_root_path / "proofs" / "READY" / "handoff.md",
            ]
            for artifact in [*required_task_artifacts, *required_run_artifacts]:
                self.assertTrue(artifact.exists(), str(artifact))

            patch_file = Path(result["retro"]["patch_file"])
            self.assertTrue(patch_file.exists(), str(patch_file))
            self.assertIn("/.csk/local/patches/", str(patch_file).replace("\\", "/"))
            self.assertTrue((root / ".csk" / "app" / "eventlog.sqlite").exists())

            event_types = list(result["event_types"])
            self.assertEqual(event_types.count("task.created"), 1)
            self.assertEqual(event_types.count("slice.created"), 2)
            self.assertEqual(event_types.count("task.critic_passed"), 1)
            self.assertEqual(event_types.count("task.frozen"), 1)
            self.assertEqual(event_types.count("task.plan_approved"), 1)
            self.assertEqual(event_types.count("proof.pack.written"), 2)
            self.assertEqual(event_types.count("ready.validated"), 1)
            self.assertEqual(event_types.count("ready.approved"), 1)
            self.assertEqual(event_types.count("retro.completed"), 1)
            self.assertNotIn("task.critic_failed", event_types)
            self.assertNotIn("plan.criticized", event_types)
            self.assertNotIn("plan.frozen", event_types)
            self.assertNotIn("plan.approved", event_types)

            strict = run_cli(root, "validate", "--all", "--strict")
            self.assertEqual(strict["status"], "ok")
            self.assertEqual(task_id, "T-0001")

    def test_acceptance_a_missing_required_artifact_fails(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = run_acceptance_a_greenfield_scenario(root)
            retro_file = Path(result["task_root"]) / "retro.md"
            retro_file.unlink()

            validate = run_cli(root, "validate", "--all", "--strict", expect_code=10)
            self.assertEqual(validate["status"], "failed")
            state = validate["state"]
            self.assertEqual(state["status"], "failed")
            self.assertIn("missing retro.md", str(state.get("error", "")))

    def test_acceptance_a_replay_fails_on_missing_manifest(self) -> None:
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            result = run_acceptance_a_greenfield_scenario(root)
            manifest = Path(result["task_run_root"]) / "proofs" / "S-0002" / "manifest.json"
            manifest.unlink()

            replay = run_cli(root, "replay", "--check", expect_code=30)
            self.assertEqual(replay["status"], "replay_failed")
            violations = user_data(replay)["replay"]["violations"]
            self.assertGreater(len(violations), 0)
            self.assertTrue(any(str(manifest) in row for row in violations))


if __name__ == "__main__":
    unittest.main()
