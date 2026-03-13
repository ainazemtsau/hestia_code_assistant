import inspect
import unittest

import support


class ShadowSupportTests(unittest.TestCase):
    def test_repo_temp_dir_is_writable_and_cleans_up(self) -> None:
        created_path = None
        with support.repo_temp_dir() as tmp:
            created_path = tmp
            probe = tmp / "probe.txt"
            probe.write_text("ok\n", encoding="utf-8")
            self.assertTrue(probe.exists())
            self.assertTrue(tmp.is_relative_to(support.SHADOW_ROOT))

        self.assertIsNotNone(created_path)
        self.assertFalse(created_path.exists())

    def test_support_uses_manual_directory_creation(self) -> None:
        module_source = inspect.getsource(support)
        self.assertIn(".mkdir(", module_source)
        self.assertIn("uuid4", module_source)
        self.assertNotIn("mkdtemp", module_source)
        self.assertNotIn("TemporaryDirectory", module_source)

    def test_workflow_test_roots_creates_realistic_checkout_inside_project(self) -> None:
        with support.workflow_test_roots() as (project_root, workflow_root):
            self.assertEqual(project_root, workflow_root.parent)
            self.assertTrue((workflow_root / "install/manifest/client_base_manifest.json").exists())
            self.assertTrue((workflow_root / "tools/install_client_workflow.py").exists())


if __name__ == "__main__":
    unittest.main()
