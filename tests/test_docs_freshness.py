from __future__ import annotations

import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class DocsFreshnessTests(unittest.TestCase):
    def test_docs_stale_after_source_change(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        (root / "app").mkdir(parents=True, exist_ok=True)
        src = root / "app" / "api.txt"
        src.write_text("v1\n", encoding="utf-8")

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")

        doc_path = root / ".pf" / "modules" / "app" / "DOCS" / "API.md"
        doc_path.write_text(
            """---
pf_doc:
  scope: module:app
  sources:
    - path: app/api.txt
      mode: file-sha
  freshness:
    policy: strict
    stale_on_any_change: true
---

# API
""",
            encoding="utf-8",
        )

        proc1, payload1 = run_pf_json(root, "docs", "scan", "--scope", "module", "--module-id", "app")
        self.assertEqual(proc1.returncode, 0, proc1.stdout + proc1.stderr)
        self.assertEqual(payload1["data"]["count"], 1)

        proc2, payload2 = run_pf_json(root, "docs", "check", "--scope", "module", "--module-id", "app")
        self.assertEqual(proc2.returncode, 0, proc2.stdout + proc2.stderr)
        self.assertEqual(payload2["data"]["stale_count"], 0)

        src.write_text("v2\n", encoding="utf-8")

        proc3, payload3 = run_pf_json(root, "docs", "check", "--scope", "module", "--module-id", "app")
        self.assertEqual(proc3.returncode, 0, proc3.stdout + proc3.stderr)
        self.assertEqual(payload3["data"]["stale_count"], 1)

        proc4, payload4 = run_pf_json(root, "docs", "scan", "--scope", "module", "--module-id", "app")
        self.assertEqual(proc4.returncode, 0, proc4.stdout + proc4.stderr)
        self.assertEqual(payload4["data"]["count"], 1)

        proc5, payload5 = run_pf_json(root, "docs", "check", "--scope", "module", "--module-id", "app")
        self.assertEqual(proc5.returncode, 0, proc5.stdout + proc5.stderr)
        self.assertEqual(payload5["data"]["stale_count"], 1)


if __name__ == "__main__":
    unittest.main()
