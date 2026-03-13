import json
import unittest
from pathlib import Path


class ShadowCanonicalWorkspaceTests(unittest.TestCase):
    def test_master_roadmap_and_stage_zero_docs_exist(self) -> None:
        self.assertTrue(
            Path("docs/plans/2026-03-13-workflow-redesign-master-roadmap.md").exists()
        )
        self.assertTrue(
            Path("docs/plans/2026-03-13-stage-0-global-workflow-audit.md").exists()
        )
        self.assertTrue(
            Path("docs/plans/2026-03-13-stage-0-5-source-installed-shadow-architecture.md").exists()
        )

    def test_canonical_shadow_workspace_has_expected_top_level_structure(self) -> None:
        root = Path("shadow/canonical")
        self.assertTrue((root / "runtime").exists())
        self.assertTrue((root / "client-package").exists())
        self.assertTrue((root / "delivery").exists())
        self.assertTrue((root / "tests").exists())
        self.assertTrue((root / "cutover").exists())

    def test_canonical_client_package_has_real_routing_skills(self) -> None:
        package_root = Path("shadow/canonical/client-package/install/source/base/.agents/skills")
        init_text = (package_root / "csk-init/SKILL.md").read_text(encoding="utf-8")
        adopt_text = (package_root / "csk-adopt/SKILL.md").read_text(encoding="utf-8")
        update_text = (package_root / "csk-project-update/SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("Shadow stub.", init_text)
        self.assertNotIn("Shadow stub.", adopt_text)
        self.assertNotIn("Shadow stub.", update_text)
        self.assertIn(".csk-base/docs/INIT_GUIDE.md", init_text)
        self.assertIn(".csk-base/docs/INIT_GUIDE.md", adopt_text)
        self.assertIn(".csk-base/docs/UPDATE_GUIDE.md", update_text)

    def test_canonical_cutover_manifests_exist_and_are_json(self) -> None:
        replace_manifest = Path("shadow/canonical/cutover/live-replace-manifest.json")
        delete_manifest = Path("shadow/canonical/cutover/live-delete-manifest.json")

        self.assertTrue(replace_manifest.exists())
        self.assertTrue(delete_manifest.exists())
        self.assertIsInstance(json.loads(replace_manifest.read_text(encoding="utf-8")), dict)
        self.assertIsInstance(json.loads(delete_manifest.read_text(encoding="utf-8")), dict)


if __name__ == "__main__":
    unittest.main()
