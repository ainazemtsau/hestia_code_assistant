import unittest

from tests.support import repo_temp_dir
from tools.csk import install_lib


class InstallLibTests(unittest.TestCase):
    def test_safe_rel_path_rejects_root_absolute_and_escape_paths(self) -> None:
        bad_values = [".", "..", "../escape", r"..\escape", r"C:\abs", r"C:anchored"]
        for raw in bad_values:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    install_lib.safe_rel_path(raw)

    def test_resolve_workflow_root_requires_existing_directory(self) -> None:
        with repo_temp_dir() as workspace:
            workflow_root = workspace / "missing-workflow"

            with self.assertRaisesRegex(ValueError, "workflow_root must exist"):
                install_lib.resolve_workflow_root(workflow_root)

    def test_resolve_manifest_path_requires_manifest_inside_workflow_root(self) -> None:
        with repo_temp_dir() as workspace:
            workflow_root = workspace / "workflow"
            workflow_root.mkdir(parents=True, exist_ok=True)
            inside_manifest = workflow_root / "install/manifest/client_base_manifest.json"
            inside_manifest.parent.mkdir(parents=True, exist_ok=True)
            inside_manifest.write_text("{}", encoding="utf-8")

            outside_manifest = workspace / "outside.json"
            outside_manifest.write_text("{}", encoding="utf-8")

            workflow_root_real = install_lib.resolve_workflow_root(workflow_root)
            resolved = install_lib.resolve_manifest_path(workflow_root_real, inside_manifest)
            self.assertEqual(inside_manifest.resolve(strict=True), resolved)

            with self.assertRaisesRegex(ValueError, "must live inside workflow_root"):
                install_lib.resolve_manifest_path(workflow_root_real, outside_manifest)

    def test_apply_manifest_removes_stale_managed_paths_from_cleanup_surfaces(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            readme_source = source_root / "install/source/base/.csk-base/README.md"
            readme_source.parent.mkdir(parents=True, exist_ok=True)
            readme_source.write_text("managed\n", encoding="utf-8")

            stale = target_root / ".csk-base/stale.txt"
            stale.parent.mkdir(parents=True, exist_ok=True)
            stale.write_text("stale\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/README.md",
                        "target": ".csk-base/README.md",
                        "ownership": "managed",
                    }
                ],
            }

            install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertFalse(stale.exists())
            self.assertEqual("managed\n", (target_root / ".csk-base/README.md").read_text(encoding="utf-8"))

    def test_apply_manifest_prevalidates_all_targets_before_mutation(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            first_source = source_root / "install/source/base/.csk-base/README.md"
            first_source.parent.mkdir(parents=True, exist_ok=True)
            first_source.write_text("managed\n", encoding="utf-8")

            bad_source = source_root / "install/source/base/.csk-base/BAD.md"
            bad_source.write_text("bad\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/README.md",
                        "target": ".csk-base/README.md",
                        "ownership": "managed",
                    },
                    {
                        "source": "install/source/base/.csk-base/BAD.md",
                        "target": "../escape.txt",
                        "ownership": "managed",
                    },
                ],
            }

            with self.assertRaises(ValueError):
                install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertFalse((target_root / ".csk-base/README.md").exists())

    def test_apply_manifest_rejects_duplicate_asset_targets_before_mutation(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            readme_source = source_root / "install/source/base/.csk-base/README.md"
            other_source = source_root / "install/source/base/.csk-base/OTHER.md"
            readme_source.parent.mkdir(parents=True, exist_ok=True)
            readme_source.write_text("managed\n", encoding="utf-8")
            other_source.write_text("other\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/README.md",
                        "target": ".csk-base/README.md",
                        "ownership": "managed",
                    },
                    {
                        "source": "install/source/base/.csk-base/OTHER.md",
                        "target": ".csk-base/README.md",
                        "ownership": "managed",
                    },
                ],
            }

            with self.assertRaisesRegex(ValueError, "duplicate asset target"):
                install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertFalse((target_root / ".csk-base/README.md").exists())

    def test_apply_manifest_verifies_replacement_source_before_deleting_existing_target(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            existing_target = target_root / ".csk-base/README.md"
            existing_target.parent.mkdir(parents=True, exist_ok=True)
            existing_target.write_text("old\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/README.md",
                        "target": ".csk-base/README.md",
                        "ownership": "managed",
                    }
                ],
            }

            with self.assertRaises(FileNotFoundError):
                install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertEqual("old\n", existing_target.read_text(encoding="utf-8"))

    def test_apply_manifest_handles_file_to_directory_shape_change(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            source_dir = source_root / "install/source/base/.csk-base/docs"
            source_dir.mkdir(parents=True, exist_ok=True)
            (source_dir / "GUIDE.md").write_text("dir content\n", encoding="utf-8")

            target_file = target_root / ".csk-base/docs"
            target_file.parent.mkdir(parents=True, exist_ok=True)
            target_file.write_text("old file\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base/docs"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/docs",
                        "target": ".csk-base/docs",
                        "ownership": "managed",
                    }
                ],
            }

            install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertTrue(target_file.is_dir())
            self.assertEqual("dir content\n", (target_root / ".csk-base/docs/GUIDE.md").read_text(encoding="utf-8"))

    def test_apply_manifest_handles_directory_to_file_shape_change(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            source_file = source_root / "install/source/base/.csk-base/STATE"
            source_file.parent.mkdir(parents=True, exist_ok=True)
            source_file.write_text("new file\n", encoding="utf-8")

            target_dir = target_root / ".csk-base/STATE"
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "stale.txt").write_text("stale\n", encoding="utf-8")

            manifest = {
                "managed_cleanup_paths": [".csk-base/STATE"],
                "assets": [
                    {
                        "source": "install/source/base/.csk-base/STATE",
                        "target": ".csk-base/STATE",
                        "ownership": "managed",
                    }
                ],
            }

            install_lib.apply_manifest(source_root, target_root, manifest)

            self.assertTrue((target_root / ".csk-base/STATE").is_file())
            self.assertEqual("new file\n", (target_root / ".csk-base/STATE").read_text(encoding="utf-8"))

    def test_apply_manifest_removes_stale_bridge_block_when_bridge_asset_is_absent(self) -> None:
        with repo_temp_dir() as workspace:
            source_root = workspace / "source"
            target_root = workspace / "client"
            source_root.mkdir(parents=True, exist_ok=True)
            target_root.mkdir(parents=True, exist_ok=True)

            agents_path = target_root / "AGENTS.md"
            agents_path.write_text(
                "# Client notes\n\nKeep this.\n\n"
                "<!-- CSK:BEGIN ROOT BOOTSTRAP -->\n"
                "bootstrap\n"
                "<!-- CSK:END ROOT BOOTSTRAP -->\n",
                encoding="utf-8",
            )

            manifest = {
                "managed_cleanup_paths": [],
                "bridge_cleanup_targets": ["AGENTS.md"],
                "assets": [],
            }

            install_lib.apply_manifest(source_root, target_root, manifest)

            text = agents_path.read_text(encoding="utf-8")
            self.assertIn("# Client notes", text)
            self.assertIn("Keep this.", text)
            self.assertNotIn("BEGIN ROOT BOOTSTRAP", text)
            self.assertNotIn("END ROOT BOOTSTRAP", text)


if __name__ == "__main__":
    unittest.main()
