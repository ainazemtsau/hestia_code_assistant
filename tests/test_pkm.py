from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class PkmTests(unittest.TestCase):
    def test_pkm_upsert_and_list(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        fp = '{"algo":"pf-v1","sources":[],"combined":"x"}'
        proc1, payload1 = run_pf_json(
            root,
            "pkm",
            "upsert",
            "--scope-type",
            "module",
            "--scope-id",
            "app",
            "--kind",
            "runbook",
            "--title",
            "Run tests",
            "--body-md",
            "pytest",
            "--fingerprint-json",
            fp,
            "--confidence",
            "0.8",
        )
        self.assertEqual(proc1.returncode, 0, proc1.stdout + proc1.stderr)

        proc2, payload2 = run_pf_json(root, "pkm", "list", "--scope-type", "module", "--scope-id", "app")
        self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
        self.assertEqual(len(payload2["data"]["items"]), 1)


if __name__ == "__main__":
    unittest.main()
