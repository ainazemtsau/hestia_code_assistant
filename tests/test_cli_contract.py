from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

from tests.common import PF_BIN, make_repo, run_pf_json


class CliContractTests(unittest.TestCase):
    def test_unknown_command_json_mode_returns_json_only(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        proc = subprocess.run(
            [str(PF_BIN), "unknown", "--json"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stderr.strip(), "")

        payload = json.loads(proc.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], 2)

    def test_replay_requires_check_flag(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        run_pf_json(root, "init")
        proc, payload = run_pf_json(root, "replay")
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], 2)


if __name__ == "__main__":
    unittest.main()
