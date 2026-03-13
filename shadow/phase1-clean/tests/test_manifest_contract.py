import json
import unittest

from support import SHADOW_ROOT


class ManifestContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = SHADOW_ROOT / "install/manifest/client_base_manifest.json"
        self.assertTrue(self.path.exists(), "shadow client manifest must exist")
        self.data = json.loads(self.path.read_text(encoding="utf-8"))

    def test_manifest_has_assets_and_cleanup_paths(self) -> None:
        assets = self.data.get("assets")
        cleanup_paths = self.data.get("managed_cleanup_paths")
        self.assertIsInstance(assets, list)
        self.assertTrue(assets)
        self.assertIsInstance(cleanup_paths, list)
        self.assertTrue(cleanup_paths)

    def test_managed_targets_are_covered_by_cleanup_paths(self) -> None:
        cleanup_paths = {
            path.replace("\\", "/").strip("/")
            for path in self.data.get("managed_cleanup_paths", [])
            if isinstance(path, str) and path.strip()
        }
        managed_targets = {
            asset["target"].replace("\\", "/").strip("/")
            for asset in self.data["assets"]
            if asset["ownership"] == "managed"
        }

        uncovered = []
        for target in managed_targets:
            if not any(target == cleanup or target.startswith(f"{cleanup}/") for cleanup in cleanup_paths):
                uncovered.append(target)

        self.assertEqual([], uncovered)

    def test_manifest_does_not_own_client_gitignore_or_codex_config(self) -> None:
        targets = {
            asset["target"]
            for asset in self.data["assets"]
            if asset["ownership"] != "bridge"
        }
        self.assertNotIn(".gitignore", targets)
        self.assertNotIn(".codex/config.toml", targets)

    def test_manifest_has_no_upstream_or_source_sync_configuration(self) -> None:
        self.assertNotIn("source_url", self.data)
        self.assertNotIn("source_ref", self.data)
        self.assertNotIn("source_subdir", self.data)


if __name__ == "__main__":
    unittest.main()
