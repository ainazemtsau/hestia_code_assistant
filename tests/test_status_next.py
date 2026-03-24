from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class StatusNextTests(unittest.TestCase):
    def test_uninitialized_next_is_init(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        # Remove .git to simulate outside repo and then restore for this test.
        proc, payload = run_pf_json(root, "status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["next"]["cmd"], "pf init")

    def test_initialized_idle_next_is_intake(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        proc, payload = run_pf_json(root, "status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["next"]["cmd"], "$pf-intake")
        self.assertIn("cmd", payload["next"])

    def test_focus_module_without_plan_approval_next_planner(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        run_pf_json(root, "focus", "module", "app")

        proc, payload = run_pf_json(root, "status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["next"]["cmd"], "$pf-planner")

    def test_new_task_after_old_approval_still_requires_planner(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        run_pf_json(root, "focus", "module", "app")

        _, first_task = run_pf_json(root, "task", "create", "--module-id", "app", "--title", "Task one")
        t1 = first_task["data"]["task"]["task_id"]
        run_pf_json(root, "plan", "mark-saved", "--module-id", "app", "--task-id", t1)
        run_pf_json(root, "plan", "approve", "--module-id", "app", "--task-id", t1, "--note", "ok")

        run_pf_json(root, "task", "create", "--module-id", "app", "--title", "Task two")
        proc, payload = run_pf_json(root, "status")

        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(payload["next"]["cmd"], "$pf-planner")
        self.assertEqual(payload["data"]["state"]["focus_task_state"], "NEW")


if __name__ == "__main__":
    unittest.main()
