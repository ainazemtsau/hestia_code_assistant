import json
import unittest
from pathlib import Path


class ClientInstallManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        path = Path("install/manifest/client_base_manifest.json")
        self.assertTrue(path.exists(), "client install manifest must exist")
        self.data = json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_has_required_fields(self) -> None:
        assets = self.data.get("assets")
        self.assertIsInstance(assets, list)
        self.assertTrue(assets)

        cleanup_paths = self.data.get("managed_cleanup_paths")
        self.assertIsInstance(cleanup_paths, list)
        self.assertTrue(cleanup_paths)

        allowed = {"managed", "bridge", "project-owned-template"}
        for asset in assets:
            self.assertIn("source", asset)
            self.assertIn("target", asset)
            self.assertIn("ownership", asset)
            self.assertIn(asset["ownership"], allowed)
            self.assertTrue(asset["source"])
            self.assertTrue(asset["target"])

        for cleanup_path in cleanup_paths:
            self.assertIsInstance(cleanup_path, str)
            self.assertTrue(cleanup_path)

    def test_manifest_excludes_dev_only_root_files(self) -> None:
        assets = self.data["assets"]
        sources = {asset["source"] for asset in assets}
        forbidden_sources = {
            "AGENTS.md",
            ".gitignore",
            ".codex/config.toml",
            "README_CSKM_PRO.md",
        }
        self.assertTrue(
            forbidden_sources.isdisjoint(sources),
            "root dev files must not be installed directly into client projects",
        )

        targets = {asset["target"] for asset in assets if asset["ownership"] != "bridge"}
        forbidden_targets = {
            ".gitignore",
            ".codex/config.toml",
        }
        self.assertTrue(
            forbidden_targets.isdisjoint(targets),
            "install manifest must not own client .gitignore or client .codex/config.toml",
        )

    def test_manifest_declares_excludes(self) -> None:
        excludes = set(self.data.get("dev_only_excludes", []))
        self.assertIn("AGENTS.md", excludes)
        self.assertIn(".gitignore", excludes)
        self.assertIn(".codex/config.toml", excludes)

    def test_manifest_declares_bridge_cleanup_targets(self) -> None:
        bridge_cleanup_targets = set(self.data.get("bridge_cleanup_targets", []))
        self.assertIn("AGENTS.md", bridge_cleanup_targets)

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

    def test_manifest_has_no_upstream_or_source_sync_configuration(self) -> None:
        self.assertNotIn("source_url", self.data)
        self.assertNotIn("source_ref", self.data)
        self.assertNotIn("source_subdir", self.data)


if __name__ == "__main__":
    unittest.main()
