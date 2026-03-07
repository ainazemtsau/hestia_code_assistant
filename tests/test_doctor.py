from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class DoctorTests(unittest.TestCase):
    def test_doctor_uses_baseline_and_flags_only_new_files(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        (root / "tools").mkdir(parents=True, exist_ok=True)
        (root / "tools" / "existing.sh").write_text("echo existing\n", encoding="utf-8")

        run_pf_json(root, "init")
        _, first = run_pf_json(root, "doctor")
        self.assertEqual(first["data"]["warnings"], [])

        (root / "tools" / "new.sh").write_text("echo new\n", encoding="utf-8")
        _, second = run_pf_json(root, "doctor")
        warnings = second["data"]["warnings"]
        self.assertEqual(len(warnings), 1)
        self.assertIn("tools/new.sh", warnings[0])


if __name__ == "__main__":
    unittest.main()
