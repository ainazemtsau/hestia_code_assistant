import subprocess
import sys
import unittest

from tools.csk.install_client_workflow import install_client_workflow
from tests.support import workflow_test_roots


class ClientInstallFlowTests(unittest.TestCase):
    def test_install_copies_managed_base_and_merges_bootstrap(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client project\n", encoding="utf-8")

            summary = install_client_workflow(workflow_root, manifest_path)

            self.assertTrue((project_root / ".csk-base/README.md").exists())
            self.assertTrue((project_root / ".csk-base/ENTRYPOINT.md").exists())
            self.assertTrue((project_root / ".csk-base/CHANGELOG.md").exists())
            self.assertTrue((project_root / ".csk-base/docs/INIT_GUIDE.md").exists())
            self.assertTrue((project_root / ".csk-base/docs/UPDATE_GUIDE.md").exists())
            self.assertTrue((project_root / ".csk-local/README.md").exists())
            self.assertTrue((project_root / ".csk-local/examples/review.browser.md").exists())
            self.assertTrue((project_root / ".agents/skills/csk-init/SKILL.md").exists())
            self.assertTrue((project_root / ".agents/skills/csk-adopt/SKILL.md").exists())
            self.assertTrue((project_root / ".agents/skills/csk-project-update/SKILL.md").exists())

            agents_text = (project_root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Primary workflow entrypoint", agents_text)
            self.assertIn("## Skills", agents_text)
            self.assertIn("csk-init", agents_text)
            self.assertIn("csk-adopt", agents_text)
            self.assertIn("csk-project-update", agents_text)
            self.assertIn(".agents/skills/csk-init/SKILL.md", agents_text)
            self.assertFalse((project_root / "README_CSKM_PRO.md").exists())
            self.assertFalse((project_root / ".codex/config.toml").exists())
            self.assertEqual(str(project_root.resolve(strict=True)), summary["project_root"])
            self.assertTrue(summary["installed_assets"])

    def test_install_preserves_unrelated_files_and_rerun_keeps_single_managed_block(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            untouched = project_root / "notes.txt"
            untouched.write_text("keep me\n", encoding="utf-8")
            agents_path = project_root / "AGENTS.md"
            agents_path.write_text("# Client project\n\nLocal notes.\n", encoding="utf-8")

            install_client_workflow(workflow_root, manifest_path)
            (workflow_root / "install/source/base/.csk-base/README.md").write_text("managed v2\n", encoding="utf-8")
            install_client_workflow(workflow_root, manifest_path)

            self.assertEqual("keep me\n", untouched.read_text(encoding="utf-8"))
            self.assertEqual("managed v2\n", (project_root / ".csk-base/README.md").read_text(encoding="utf-8"))

            agents_text = agents_path.read_text(encoding="utf-8")
            self.assertIn("Local notes.", agents_text)
            self.assertEqual(1, agents_text.count("<!-- CSK:BEGIN ROOT BOOTSTRAP -->"))
            self.assertEqual(1, agents_text.count("<!-- CSK:END ROOT BOOTSTRAP -->"))

    def test_cli_install_defaults_to_script_checkout_and_parent_project(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            (project_root / "AGENTS.md").write_text("# Client project\n", encoding="utf-8")

            result = subprocess.run(
                [sys.executable, str(workflow_root / "tools/csk/install_client_workflow.py")],
                cwd=project_root,
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertIn("[csk-install]", result.stdout)
            self.assertTrue((project_root / ".csk-base/ENTRYPOINT.md").exists())


if __name__ == "__main__":
    unittest.main()
