import json
import unittest
from pathlib import Path


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
REQUIRED_BOUNDARY_PATHS = {
    "install/",
    "tools/csk/install_lib.py",
    "tools/csk/install_client_workflow.py",
    "tools/csk/update_client_workflow.py",
    "tests/test_bootstrap_contract.py",
    "tests/test_client_install_flow.py",
    "tests/test_client_install_manifest.py",
    "tests/test_stage0_workflow_audit.py",
    "tests/test_stage05_source_installed_shadow_architecture.py",
    "shadow/phase1-clean/",
    "shadow/canonical/runtime/",
    "shadow/canonical/client-package/",
    "shadow/canonical/delivery/",
    "shadow/canonical/tests/",
    "shadow/canonical/cutover/",
    ".csk-app/digest.md",
    "shadow/README.md",
    "docs/plans/2026-03-13-stage-0-global-workflow-audit.md",
    "docs/plans/2026-03-13-stage-0-workflow-inventory.json",
    "docs/plans/2026-03-13-stage-0-5-source-installed-shadow-architecture.md",
    "docs/plans/2026-03-13-workflow-redesign-master-roadmap.md",
}
REQUIRED_DOC_TERMS = (
    "canonical-active",
    "live-compatibility",
    "legacy-reference",
    "installed-client-surface",
    "## Canonical-Active Paths",
    "## Live-Compatibility Paths",
    "## Legacy-Reference Paths",
    "## Replace-at-Cutover Paths",
    "## Delete-at-Cutover Paths",
)


class Stage05ArchitectureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc_path = Path("docs/plans/2026-03-13-stage-0-5-source-installed-shadow-architecture.md")
        self.boundary_map_path = Path("shadow/canonical/cutover/boundary-map.json")
        self.replace_manifest_path = Path("shadow/canonical/cutover/live-replace-manifest.json")
        self.delete_manifest_path = Path("shadow/canonical/cutover/live-delete-manifest.json")
        self.digest_path = Path(".csk-app/digest.md")
        self.shadow_readme_path = Path("shadow/README.md")
        self.roadmap_path = Path("docs/plans/2026-03-13-workflow-redesign-master-roadmap.md")

    def test_stage05_doc_and_boundary_map_exist(self) -> None:
        self.assertTrue(self.doc_path.exists())
        self.assertTrue(self.boundary_map_path.exists())

    def test_stage05_doc_contains_required_architecture_terms(self) -> None:
        text = self.doc_path.read_text(encoding="utf-8")
        for term in REQUIRED_DOC_TERMS:
            self.assertIn(term, text)
        self.assertIn("all new redesign work lands only in `shadow/canonical/`", text)
        self.assertIn("`shadow/phase1-clean/` is not a design target anymore", text)

    def test_boundary_map_has_required_schema_and_paths(self) -> None:
        boundary_map = json.loads(self.boundary_map_path.read_text(encoding="utf-8"))
        self.assertEqual(boundary_map["version"], 1)
        self.assertIsInstance(boundary_map["entries"], list)
        paths = set()
        for entry in boundary_map["entries"]:
            for key in (
                "path",
                "current_class",
                "future_class",
                "source_of_truth",
                "cutover_action",
                "owner_stage",
                "notes",
            ):
                self.assertIn(key, entry)
            self.assertIn(entry["owner_stage"], ALLOWED_STAGES)
            paths.add(entry["path"])
        self.assertTrue(REQUIRED_BOUNDARY_PATHS.issubset(paths))

    def test_cutover_manifests_are_exact_and_disjoint(self) -> None:
        replace_manifest = json.loads(self.replace_manifest_path.read_text(encoding="utf-8"))
        delete_manifest = json.loads(self.delete_manifest_path.read_text(encoding="utf-8"))
        replace_paths = set(replace_manifest["replace_paths"])
        delete_paths = set(delete_manifest["delete_paths"])
        self.assertFalse(replace_paths & delete_paths)

        boundary_map = json.loads(self.boundary_map_path.read_text(encoding="utf-8"))
        boundary_paths = {entry["path"] for entry in boundary_map["entries"]}
        self.assertTrue(replace_paths.issubset(boundary_paths))
        self.assertTrue(delete_paths.issubset(boundary_paths))
        self.assertIn("shadow/phase1-clean/", delete_paths)
        self.assertIn("install/", replace_paths)
        self.assertIn("tools/csk/install_lib.py", replace_paths)
        self.assertIn("tools/csk/install_client_workflow.py", replace_paths)
        self.assertIn("tools/csk/update_client_workflow.py", replace_paths)

    def test_digest_and_shadow_readme_no_longer_present_phase1_clean_as_active(self) -> None:
        digest = self.digest_path.read_text(encoding="utf-8")
        shadow_readme = self.shadow_readme_path.read_text(encoding="utf-8")

        self.assertNotIn("Phase 1 clean rewrite", digest)
        self.assertIn("shadow/canonical", digest)
        self.assertIn("compatibility-only", digest)
        self.assertIn("legacy-reference-only", digest)

        self.assertIn("only active redesign source", shadow_readme)
        self.assertIn("legacy-reference-only", shadow_readme)

    def test_master_roadmap_reflects_stage05_completion(self) -> None:
        roadmap = self.roadmap_path.read_text(encoding="utf-8")
        self.assertIn("- `Stage 0.5`: closed", roadmap)
        self.assertIn("canonical is now the only redesign source", roadmap)
        self.assertIn("live is compatibility-only", roadmap)
        self.assertIn("phase1-clean is legacy-reference-only", roadmap)


if __name__ == "__main__":
    unittest.main()
