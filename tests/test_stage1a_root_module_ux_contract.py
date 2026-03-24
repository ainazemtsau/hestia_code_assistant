from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ENTRY = REPO_ROOT / "runtime" / "entry"
RUNTIME_ROOT_MODULE = REPO_ROOT / "runtime" / "root-module"
PLANS_DIR = REPO_ROOT / "docs" / "plans"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Stage1ARootModuleUxContractTests(unittest.TestCase):
    def test_root_entry_model_exists_and_defines_action_first_root_contract(self) -> None:
        path = RUNTIME_ENTRY / "ROOT_ENTRY_MODEL.md"
        self.assertTrue(path.exists(), f"Missing root entry model: {path}")

        text = read_text(path)
        required_snippets = [
            "$csk",
            "root control plane",
            "Now",
            "Blocked / Waiting",
            "Modules",
            "Root Work",
            "Next Commands",
            "$csk-reconcile-state",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_module_entry_model_exists_and_defines_local_first_view(self) -> None:
        path = RUNTIME_ENTRY / "MODULE_ENTRY_MODEL.md"
        self.assertTrue(path.exists(), f"Missing module entry model: {path}")

        text = read_text(path)
        required_snippets = [
            "local-first",
            "module view",
            "path back to root",
            "current module",
            "current leaf",
            "next recommended step",
            "$csk-reconcile-state",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_routing_rules_exist_and_cover_descent_return_and_reconcile(self) -> None:
        path = RUNTIME_ENTRY / "ROUTING_RULES.md"
        self.assertTrue(path.exists(), f"Missing routing rules: {path}")

        text = read_text(path)
        required_snippets = [
            "root -> internal module",
            "internal module -> leaf",
            "module -> root",
            "state_health",
            "fresh",
            "reconciled",
            "stale",
            "contradictory",
            "do not allow implementation",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_next_command_model_exists_and_defines_dashboard_outputs(self) -> None:
        path = RUNTIME_ROOT_MODULE / "NEXT_COMMAND_MODEL.md"
        self.assertTrue(path.exists(), f"Missing next command model: {path}")

        text = read_text(path)
        required_snippets = [
            "dashboard.yaml",
            "next recommended skill",
            "next recommended directory",
            "next recommended prompt",
            "single next recommended step",
            "state health",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_stage_1a_report_exists_and_records_stop_at_stage_end(self) -> None:
        path = PLANS_DIR / "2026-03-24-stage-1a-root-module-ux-contract-report.md"
        self.assertTrue(path.exists(), f"Missing Stage 1A report: {path}")

        text = read_text(path)
        required_snippets = [
            "Stage result",
            "passed",
            "Outputs produced",
            "Gates passed",
            "Exact next recommended action",
            "Next stage eligible",
            "stop at the end of the stage",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
