from __future__ import annotations

import json
import unittest
from pathlib import Path

from tests.common import make_repo, run_pf_json


class ContextBuilderTests(unittest.TestCase):
    def test_context_build_respects_scope_and_budget(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        (root / "app").mkdir(parents=True, exist_ok=True)
        (root / "app" / "health.py").write_text("def health():\n    return 'ok'\n", encoding="utf-8")
        (root / "other").mkdir(parents=True, exist_ok=True)
        (root / "other" / "secret.py").write_text("def health():\n    return 'bad'\n", encoding="utf-8")

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        run_pf_json(root, "focus", "module", "app")
        run_pf_json(root, "plan", "approve", "--module-id", "app", "--note", "ok")

        proc, payload = run_pf_json(
            root,
            "context",
            "build",
            "--intent",
            "execute",
            "--module",
            "app",
            "--budget",
            "2500",
            "--query",
            "health",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

        bundle_rel = payload["data"]["bundle_json"]
        bundle = json.loads((root / bundle_rel).read_text(encoding="utf-8"))

        selected_bytes = len(json.dumps(bundle["selected"], ensure_ascii=False, sort_keys=True).encode("utf-8"))
        self.assertLessEqual(selected_bytes, 2500)

        for snippet in bundle["selected"]["code_snippets"]:
            self.assertTrue(snippet["path"].startswith("app/"), snippet["path"])

    def test_context_budget_too_small_returns_validation_error(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        (root / "app").mkdir(parents=True, exist_ok=True)
        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        run_pf_json(root, "focus", "module", "app")

        proc, payload = run_pf_json(
            root,
            "context",
            "build",
            "--intent",
            "execute",
            "--module",
            "app",
            "--budget",
            "10",
        )
        self.assertEqual(proc.returncode, 10, proc.stdout + proc.stderr)
        self.assertFalse(payload["ok"])
        self.assertIn("details", payload["error"])
        self.assertIn("min_required_budget", payload["error"]["details"])

    def test_context_respects_slice_allowed_paths(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        (root / "app" / "allowed").mkdir(parents=True, exist_ok=True)
        (root / "app" / "blocked").mkdir(parents=True, exist_ok=True)
        (root / "app" / "allowed" / "ok.py").write_text("def token_hit():\n    return 1\n", encoding="utf-8")
        (root / "app" / "blocked" / "bad.py").write_text("def token_hit():\n    return 2\n", encoding="utf-8")

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        _, task_payload = run_pf_json(root, "task", "create", "--module-id", "app", "--title", "Scoped task")
        task_id = task_payload["data"]["task"]["task_id"]
        run_pf_json(
            root,
            "slice",
            "create",
            "--task-id",
            task_id,
            "--title",
            "Only allowed path",
            "--allowed-paths",
            "app/allowed",
        )
        run_pf_json(root, "focus", "module", "app")

        proc, payload = run_pf_json(
            root,
            "context",
            "build",
            "--intent",
            "execute",
            "--module",
            "app",
            "--task",
            task_id,
            "--budget",
            "6000",
            "--query",
            "token_hit",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        bundle = payload["data"]["bundle"]
        for snippet in bundle["selected"]["code_snippets"]:
            self.assertTrue(snippet["path"].startswith("app/allowed/"), snippet["path"])

    def test_context_ignores_allowed_paths_outside_repo_with_shared_prefix(self) -> None:
        tmp = make_repo()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)

        sibling = root.parent / f"{root.name}_outside"
        sibling.mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: sibling.rmdir() if sibling.exists() and not any(sibling.iterdir()) else None)

        (root / "app").mkdir(parents=True, exist_ok=True)
        (root / "app" / "token.py").write_text("def shared_token():\n    return 1\n", encoding="utf-8")

        run_pf_json(root, "init")
        run_pf_json(root, "module", "upsert", "--module-id", "app", "--root-path", "app", "--display-name", "App")
        run_pf_json(root, "module", "init", "--module-id", "app", "--write-scaffold")
        _, task_payload = run_pf_json(root, "task", "create", "--module-id", "app", "--title", "Prefix path task")
        task_id = task_payload["data"]["task"]["task_id"]
        run_pf_json(
            root,
            "slice",
            "create",
            "--task-id",
            task_id,
            "--title",
            "Try outside path",
            "--allowed-paths",
            str(sibling),
        )

        proc, payload = run_pf_json(
            root,
            "context",
            "build",
            "--intent",
            "execute",
            "--module",
            "app",
            "--task",
            task_id,
            "--budget",
            "6000",
            "--query",
            "shared_token",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        bundle = payload["data"]["bundle"]
        snippets = bundle["selected"]["code_snippets"]
        self.assertGreater(len(snippets), 0)
        for snippet in snippets:
            self.assertTrue(snippet["path"].startswith("app/"), snippet["path"])


if __name__ == "__main__":
    unittest.main()
