from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class ReviewFixRegressionTests(unittest.TestCase):
    def test_module_upsert_rejects_path_traversal_module_id(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        bad_module_id = "../../pf_escape_demo"
        proc, payload = run_pf_json(
            root,
            "module",
            "upsert",
            "--module-id",
            bad_module_id,
            "--root-path",
            "app",
            "--display-name",
            "App",
        )
        self.assertEqual(proc.returncode, 10, proc.stdout + proc.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], 10)
        self.assertEqual(payload["error"]["details"]["module_id"], bad_module_id)

    def test_artifact_reuse_returns_persisted_metadata(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        artifact_file = root / "artifact.txt"
        artifact_file.write_text("hello\n", encoding="utf-8")

        proc1, payload1 = run_pf_json(
            root,
            "artifact",
            "put",
            "--kind",
            "plan",
            "--path",
            "artifact.txt",
        )
        self.assertEqual(proc1.returncode, 0, proc1.stdout + proc1.stderr)
        art1 = payload1["data"]["artifact"]
        self.assertFalse(art1["reused"])

        proc2, payload2 = run_pf_json(
            root,
            "artifact",
            "put",
            "--kind",
            "plan",
            "--path",
            "artifact.txt",
        )
        self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
        art2 = payload2["data"]["artifact"]

        self.assertTrue(art2["reused"])
        self.assertEqual(art2["artifact_id"], art1["artifact_id"])
        self.assertEqual(art2["kind"], art1["kind"])
        self.assertEqual(art2["path"], art1["path"])
        self.assertEqual(art2["sha256"], art1["sha256"])
        self.assertEqual(art2["bytes"], art1["bytes"])
        self.assertEqual(art2["created_ts"], art1["created_ts"])

    def test_artifact_reuse_rejects_kind_mismatch(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        artifact_file = root / "artifact.txt"
        artifact_file.write_text("hello\n", encoding="utf-8")
        run_pf_json(root, "artifact", "put", "--kind", "plan", "--path", "artifact.txt")

        proc, payload = run_pf_json(
            root,
            "artifact",
            "put",
            "--kind",
            "bundle",
            "--path",
            "artifact.txt",
        )
        self.assertEqual(proc.returncode, 10, proc.stdout + proc.stderr)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], 10)
        self.assertEqual(payload["error"]["details"]["existing_kind"], "plan")
        self.assertEqual(payload["error"]["details"]["requested_kind"], "bundle")

    def test_status_uses_event_order_when_mission_created_timestamps_tie(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        _, payload1 = run_pf_json(root, "mission", "create", "--title", "Mission one")
        _, payload2 = run_pf_json(root, "mission", "create", "--title", "Mission two")
        mission1 = payload1["data"]["mission"]["mission_id"]
        mission2 = payload2["data"]["mission"]["mission_id"]

        conn = sqlite3.connect(root / ".pf" / "state.db")
        conn.execute("UPDATE events SET ts='2026-01-01T00:00:00Z' WHERE type='mission.created'")
        conn.commit()
        conn.close()

        proc, status = run_pf_json(root, "status")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        active = status["data"]["state"]["active_mission"]
        self.assertIsNotNone(active)
        self.assertNotEqual(active["mission_id"], mission1)
        self.assertEqual(active["mission_id"], mission2)

    def test_doctor_returns_structured_result_on_db_access_failure(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        db_path = root / ".pf" / "state.db"
        db_path.unlink()
        db_path.mkdir(parents=True, exist_ok=True)

        proc, payload = run_pf_json(root, "doctor")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertTrue(payload["ok"])
        self.assertIn("data", payload)
        self.assertNotIn("error", payload)

        doctor = payload["data"]
        self.assertFalse(doctor["ok"])
        checks = {check["name"]: check for check in doctor["checks"]}
        self.assertIn("initialized", checks)
        self.assertIn("db_access", checks)
        self.assertTrue(checks["initialized"]["ok"])
        self.assertFalse(checks["db_access"]["ok"])
        self.assertTrue(
            any("guardrail baseline comparison skipped" in warning for warning in doctor["warnings"])
        )


if __name__ == "__main__":
    unittest.main()
