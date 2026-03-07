from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from tests.common import make_repo, run_pf


class DbSchemaTests(unittest.TestCase):
    def test_schema_has_required_tables(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        proc = run_pf(root, "init")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        conn = sqlite3.connect(root / ".pf" / "state.db")
        conn.row_factory = sqlite3.Row
        tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        conn.close()

        for name in [
            "events",
            "modules",
            "artifacts",
            "focus",
            "pkm_items",
            "docs_index",
            "runtime_counters",
            "doctor_baseline",
        ]:
            self.assertIn(name, tables)

        conn = sqlite3.connect(root / ".pf" / "state.db")
        conn.row_factory = sqlite3.Row
        cols = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(docs_index)").fetchall()
        }
        conn.close()
        self.assertIn("baseline_fingerprint_json", cols)
        self.assertIn("observed_fingerprint_json", cols)


if __name__ == "__main__":
    unittest.main()
