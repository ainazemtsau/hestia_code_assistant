import subprocess
import sys
import unittest

from support import load_shadow_module, workflow_test_roots


class ShadowUpdateFlowTests(unittest.TestCase):
    def test_update_refreshes_managed_base_and_preserves_project_owned_files(self) -> None:
        install_module = load_shadow_module("shadow_install_client_workflow", "tools/install_client_workflow.py")
        update_module = load_shadow_module("shadow_update_client_workflow", "tools/update_client_workflow.py")

        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client notes\n\nKeep this.\n", encoding="utf-8")
            install_module.install_client_workflow(workflow_root, manifest_path)

            (project_root / ".csk-base/README.md").write_text("stale managed\n", encoding="utf-8")
            (project_root / ".csk-local/README.md").write_text("client-owned change\n", encoding="utf-8")
            (project_root / ".csk-base/stale.txt").write_text("stale\n", encoding="utf-8")
            (workflow_root / "install/source/base/.csk-base/README.md").write_text("fresh managed\n", encoding="utf-8")

            summary = update_module.update_client_workflow(workflow_root, manifest_path)

            self.assertEqual("fresh managed\n", (project_root / ".csk-base/README.md").read_text(encoding="utf-8"))
            self.assertEqual(
                "client-owned change\n",
                (project_root / ".csk-local/README.md").read_text(encoding="utf-8"),
            )
            self.assertFalse((project_root / ".csk-base/stale.txt").exists())

            agents_text = (project_root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("# Client notes", agents_text)
            self.assertIn("Keep this.", agents_text)
            self.assertEqual(1, agents_text.count("<!-- CSK:BEGIN ROOT BOOTSTRAP -->"))
            self.assertEqual(1, agents_text.count("<!-- CSK:END ROOT BOOTSTRAP -->"))
            self.assertEqual("update", summary["mode"])
            self.assertEqual(str(project_root.resolve(strict=True)), summary["project_root"])
            self.assertTrue(summary["updated_assets"])

    def test_update_on_empty_client_root_installs_base_and_templates(self) -> None:
        update_module = load_shadow_module("shadow_update_client_workflow_empty", "tools/update_client_workflow.py")

        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"

            summary = update_module.update_client_workflow(workflow_root, manifest_path)

            self.assertTrue((project_root / ".csk-base/ENTRYPOINT.md").exists())
            self.assertTrue((project_root / ".csk-local/README.md").exists())
            self.assertTrue((project_root / ".agents/skills/csk-project-update/SKILL.md").exists())
            self.assertTrue((project_root / "AGENTS.md").exists())
            self.assertEqual("update", summary["mode"])

    def test_cli_update_defaults_to_script_parent_checkout_and_parent_project(self) -> None:
        install_module = load_shadow_module("shadow_install_for_cli_update", "tools/install_client_workflow.py")

        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client notes\n", encoding="utf-8")
            install_module.install_client_workflow(workflow_root, manifest_path)
            (project_root / ".csk-local/README.md").write_text("keep local\n", encoding="utf-8")
            (workflow_root / "install/source/base/.csk-base/README.md").write_text("managed via cli\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(workflow_root / "tools/update_client_workflow.py")],
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
