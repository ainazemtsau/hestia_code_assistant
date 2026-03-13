import json
import subprocess
import sys
import unittest

from tools.csk.install_client_workflow import install_client_workflow
from tools.csk.update_client_workflow import update_client_workflow
from tests.support import workflow_test_roots


class ClientUpdatePreservesCustomizationsTests(unittest.TestCase):
    def test_update_refreshes_managed_base_and_keeps_local_customizations(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client project\n", encoding="utf-8")

            install_client_workflow(workflow_root, manifest_path)

            managed_file = project_root / ".csk-base/README.md"
            local_file = project_root / ".csk-local/README.md"

            managed_file.write_text("stale managed content\n", encoding="utf-8")
            local_file.write_text("custom local content\n", encoding="utf-8")

            summary = update_client_workflow(workflow_root, manifest_path)

            self.assertIn("managed base workflow layer", managed_file.read_text(encoding="utf-8"))
            self.assertEqual("custom local content\n", local_file.read_text(encoding="utf-8"))
            self.assertIn("Primary workflow entrypoint", (project_root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual(str(project_root.resolve(strict=True)), summary["project_root"])
            self.assertTrue(summary["updated_assets"])

    def test_update_can_sync_base_into_empty_parent_project(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"

            summary = update_client_workflow(workflow_root, manifest_path)

            self.assertTrue((project_root / ".csk-base/README.md").exists())
            self.assertTrue((project_root / ".csk-local/README.md").exists())
            self.assertTrue((project_root / ".agents/skills/csk-init/SKILL.md").exists())
            self.assertIn("Primary workflow entrypoint", (project_root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertEqual("update", summary["mode"])

    def test_update_removes_stale_managed_assets_no_longer_in_manifest(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            install_client_workflow(workflow_root, manifest_path)

            custom_skill = project_root / ".agents/skills/project-custom/SKILL.md"
            custom_skill.parent.mkdir(parents=True, exist_ok=True)
            custom_skill.write_text("custom\n", encoding="utf-8")

            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_data["assets"] = [
                asset for asset in manifest_data["assets"]
                if asset["target"] != ".agents/skills/csk-init/SKILL.md"
            ]
            reduced_manifest = workflow_root / "reduced_manifest.json"
            reduced_manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

            update_client_workflow(workflow_root, reduced_manifest)

            self.assertFalse((project_root / ".agents/skills/csk-init/SKILL.md").exists())
            self.assertTrue(custom_skill.exists())

    def test_update_removes_legacy_managed_assets_without_state_file(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            legacy_skill = project_root / ".agents/skills/csk-init/SKILL.md"
            legacy_skill.parent.mkdir(parents=True, exist_ok=True)
            legacy_skill.write_text("legacy stale skill\n", encoding="utf-8")

            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_data["assets"] = [
                asset for asset in manifest_data["assets"]
                if asset["target"] != ".agents/skills/csk-init/SKILL.md"
            ]
            reduced_manifest = workflow_root / "reduced_manifest.json"
            reduced_manifest.write_text(json.dumps(manifest_data), encoding="utf-8")

            update_client_workflow(workflow_root, reduced_manifest)

            self.assertFalse(legacy_skill.exists())

    def test_cli_update_defaults_to_script_checkout_and_parent_project(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client notes\n", encoding="utf-8")
            install_client_workflow(workflow_root, manifest_path)
            (project_root / ".csk-local/README.md").write_text("keep local\n", encoding="utf-8")
            (workflow_root / "install/source/base/.csk-base/README.md").write_text("managed via cli\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(workflow_root / "tools/csk/update_client_workflow.py")],
                cwd=project_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("[csk-update]", result.stdout)
            self.assertEqual("managed via cli\n", (project_root / ".csk-base/README.md").read_text(encoding="utf-8"))
            self.assertEqual("keep local\n", (project_root / ".csk-local/README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
