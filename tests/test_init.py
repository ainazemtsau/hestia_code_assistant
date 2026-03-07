from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf


class InitTests(unittest.TestCase):
    def test_init_is_idempotent(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        first = run_pf(root, "init")
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertTrue((root / ".pf" / "state.db").exists())
        self.assertTrue((root / "AGENTS.md").exists())

        second = run_pf(root, "init")
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertTrue((root / ".pf" / "state.db").exists())


if __name__ == "__main__":
    unittest.main()
