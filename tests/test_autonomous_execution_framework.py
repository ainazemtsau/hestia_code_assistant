from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANS_DIR = REPO_ROOT / "docs" / "plans"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class AutonomousExecutionFrameworkTests(unittest.TestCase):
    def test_autonomous_execution_protocol_exists_and_defines_core_rules(self) -> None:
        path = PLANS_DIR / "AUTONOMOUS_EXECUTION_PROTOCOL.md"
        self.assertTrue(path.exists(), f"Missing protocol doc: {path}")

        text = read_text(path)
        required_snippets = [
            "One active stage at a time",
            "stop at the end of the stage",
            "hard blockers",
            "No auto-commit",
            "No auto-push",
            "documentation obligations before stopping",
            "Stage 1A - Root / Module UX Contract",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_stage_packet_template_exists_and_contains_required_fields(self) -> None:
        path = PLANS_DIR / "STAGE_PACKET_TEMPLATE.md"
        self.assertTrue(path.exists(), f"Missing stage packet template: {path}")

        text = read_text(path)
        required_fields = [
            "Stage goal",
            "Exact inputs",
            "Exact outputs",
            "Substage order",
            "Required gates",
            "Acceptance criteria",
            "Hard blockers",
            "Allowed autonomous decisions",
            "Forbidden decisions",
            "Stop conditions",
            "Next-stage prerequisites",
        ]

        for field in required_fields:
            self.assertIn(field, text)

    def test_stage_report_template_exists_and_contains_required_fields(self) -> None:
        path = PLANS_DIR / "STAGE_REPORT_TEMPLATE.md"
        self.assertTrue(path.exists(), f"Missing stage report template: {path}")

        text = read_text(path)
        required_fields = [
            "Stage result",
            "Outputs produced",
            "Gates passed",
            "Unresolved items",
            "Blockers encountered",
            "Assumptions used",
            "Exact next recommended action",
            "Next stage eligible",
        ]

        for field in required_fields:
            self.assertIn(field, text)

    def test_stage_1a_packet_exists_and_binds_to_runtime_outputs(self) -> None:
        path = PLANS_DIR / "2026-03-24-stage-1a-root-module-ux-contract-packet.md"
        self.assertTrue(path.exists(), f"Missing Stage 1A packet: {path}")

        text = read_text(path)
        required_snippets = [
            "Stage 1A - Root / Module UX Contract",
            "docs/csk_vnext_final_spec_ru.md",
            "docs/plans/2026-03-13-stage-1-entry-routing-root-module-program-model.md",
            "runtime/entry/ROOT_ENTRY_MODEL.md",
            "runtime/entry/MODULE_ENTRY_MODEL.md",
            "runtime/entry/ROUTING_RULES.md",
            "runtime/root-module/NEXT_COMMAND_MODEL.md",
            "stop at the end of the stage",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)

    def test_master_roadmap_references_framework_and_stage_1a(self) -> None:
        path = PLANS_DIR / "2026-03-13-workflow-redesign-master-roadmap.md"
        text = read_text(path)

        required_snippets = [
            "AUTONOMOUS_EXECUTION_PROTOCOL.md",
            "STAGE_PACKET_TEMPLATE.md",
            "STAGE_REPORT_TEMPLATE.md",
            "Stage 1A - Root / Module UX Contract",
        ]

        for snippet in required_snippets:
            self.assertIn(snippet, text)


if __name__ == "__main__":
    unittest.main()
