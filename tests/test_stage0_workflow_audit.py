import json
import unittest
from pathlib import Path


ALLOWED_VERDICTS = {"keep", "fix", "replace", "remove", "defer"}
ALLOWED_STAGES = {
    "Stage 0",
    "Stage 0.5",
    "Stage 1",
    "Stage 2",
    "Stage 3",
    "Stage 4",
    "Stage 5",
    "Stage 6",
    "Stage 7",
    "Stage 8",
    "Stage 9",
}
REQUIRED_JOURNEY_STEPS = [
    "install",
    "init_adopt",
    "planning",
    "pre_execution_review",
    "execution",
    "final_review_ready_reporting",
    "retro_learning",
    "update",
]
REQUIRED_PUBLIC_SURFACES = {
    "$csk",
    "$csk-module",
    "root AGENTS.md bootstrap behavior",
    "client bootstrap managed block",
    ".csk-base/ENTRYPOINT.md",
    "installed csk-init",
    "installed csk-adopt",
    "installed csk-project-update",
    "install helper CLI",
    "update helper CLI",
    "tools/csk/csk.py",
    "shadow/phase1-clean installed skills",
    "shadow/canonical top-level ownership model",
}


class Stage0WorkflowAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.audit_path = Path("docs/plans/2026-03-13-stage-0-global-workflow-audit.md")
        self.inventory_path = Path("docs/plans/2026-03-13-stage-0-workflow-inventory.json")
        self.roadmap_path = Path("docs/plans/2026-03-13-workflow-redesign-master-roadmap.md")

    def test_stage0_audit_and_inventory_exist(self) -> None:
        self.assertTrue(self.audit_path.exists())
        self.assertTrue(self.inventory_path.exists())

    def test_inventory_has_required_schema_and_layers(self) -> None:
        inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        self.assertEqual(inventory["schema_version"], 1)
        self.assertEqual(inventory["layers"], ["live", "phase1-clean", "canonical"])
        self.assertIn("generated_on", inventory)
        self.assertIn("journey_steps", inventory)
        self.assertIn("public_surfaces", inventory)
        self.assertIn("dead_ends", inventory)
        self.assertIn("broken_contracts", inventory)
        self.assertIn("summary", inventory)

    def test_inventory_covers_all_required_journey_steps(self) -> None:
        inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        steps = {entry["id"]: entry for entry in inventory["journey_steps"]}
        self.assertEqual(set(steps.keys()), set(REQUIRED_JOURNEY_STEPS))
        for step_id in REQUIRED_JOURNEY_STEPS:
            self.assertGreaterEqual(len(steps[step_id]["preliminary_verdicts"]), 1)
            for verdict in steps[step_id]["preliminary_verdicts"]:
                self.assertIn(verdict["verdict"], ALLOWED_VERDICTS)
                self.assertIn(verdict["owner_stage"], ALLOWED_STAGES)

    def test_inventory_lists_required_public_surfaces(self) -> None:
        inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        surfaces = {entry["name"] for entry in inventory["public_surfaces"]}
        self.assertTrue(REQUIRED_PUBLIC_SURFACES.issubset(surfaces))
        for entry in inventory["public_surfaces"]:
            self.assertIn(entry["verdict"], ALLOWED_VERDICTS)
            self.assertIn(entry["owner_stage"], ALLOWED_STAGES)

    def test_dead_ends_and_broken_contracts_are_owned(self) -> None:
        inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(inventory["dead_ends"]), 1)
        self.assertGreaterEqual(len(inventory["broken_contracts"]), 1)
        for entry in inventory["dead_ends"]:
            self.assertIn(entry["owner_stage"], ALLOWED_STAGES)
        for entry in inventory["broken_contracts"]:
            self.assertIn(entry["owner_stage"], ALLOWED_STAGES)

    def test_summary_contains_required_counts(self) -> None:
        inventory = json.loads(self.inventory_path.read_text(encoding="utf-8"))
        summary = inventory["summary"]
        self.assertIn("counts_by_verdict", summary)
        self.assertIn("counts_by_owner_stage", summary)
        self.assertIn("counts_by_layer", summary)
        self.assertIn("dead_end_count", summary)
        self.assertIn("broken_contract_count", summary)

    def test_markdown_audit_covers_journey_and_required_lists(self) -> None:
        text = self.audit_path.read_text(encoding="utf-8")
        for title in (
            "## Install",
            "## Init / Adopt",
            "## Planning",
            "## Pre-Execution Review",
            "## Execution",
            "## Final Review / READY / Reporting",
            "## Retro / Learning",
            "## Update",
            "## Consolidated Public Surface Table",
            "## Consolidated Dead-End List",
            "## Consolidated Broken-Contract List",
            "## Owner-Stage Mapping",
            "## Recommended Next Focus for Stage 0.5",
        ):
            self.assertIn(title, text)
        self.assertIn("Stage 7", text)
        self.assertIn("dead-end", text.lower())

    def test_master_roadmap_reflects_stage0_completion(self) -> None:
        text = self.roadmap_path.read_text(encoding="utf-8")
        self.assertIn("- `Stage 0`: closed", text)
        self.assertRegex(text, r"- `Stage 0\.5`: (backlog|auditing|closed)")
        self.assertIn("Stage 0 audit results", text)


if __name__ == "__main__":
    unittest.main()
