from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class ReportTests(unittest.TestCase):
    def test_manager_report_has_next(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        proc, payload = run_pf_json(root, "report", "manager")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = payload["data"]["report"]
        self.assertIn("next", report)
        self.assertIn("cmd", report["next"])


if __name__ == "__main__":
    unittest.main()
