import json
import unittest

from tools.csk.install_client_workflow import install_client_workflow
from tools.csk.update_client_workflow import update_client_workflow
from tests.support import workflow_test_roots


class ClientInstallUpdateE2ETests(unittest.TestCase):
    def test_install_customize_update_cycle(self) -> None:
        with workflow_test_roots() as (project_root, workflow_root):
            manifest_path = workflow_root / "install/manifest/client_base_manifest.json"
            (project_root / "AGENTS.md").write_text("# Client project\n", encoding="utf-8")

            install_client_workflow(workflow_root, manifest_path)

            local_readme = project_root / ".csk-local/README.md"
            local_readme.write_text("custom local content\n", encoding="utf-8")

            managed_readme_source = workflow_root / "install/source/base/.csk-base/README.md"
            managed_readme_source.write_text("managed base v2\n", encoding="utf-8")

            manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_data["assets"] = [
                asset for asset in manifest_data["assets"]
                if asset["target"] != ".agents/skills/csk-init/SKILL.md"
            ]
            reduced_manifest = workflow_root / "install/manifest/reduced_client_base_manifest.json"
            reduced_manifest.write_text(json.dumps(manifest_data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

            summary = update_client_workflow(workflow_root, reduced_manifest)

            self.assertEqual("managed base v2\n", (project_root / ".csk-base/README.md").read_text(encoding="utf-8"))
            self.assertEqual("custom local content\n", local_readme.read_text(encoding="utf-8"))
            self.assertFalse((project_root / ".agents/skills/csk-init/SKILL.md").exists())
            self.assertIn("Primary workflow entrypoint", (project_root / "AGENTS.md").read_text(encoding="utf-8"))
            self.assertTrue(any(item["action"] == "removed" for item in summary["updated_assets"]))


if __name__ == "__main__":
    unittest.main()
