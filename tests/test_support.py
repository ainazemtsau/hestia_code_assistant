import inspect
import unittest

from tests import support


class SupportTests(unittest.TestCase):
    def test_repo_temp_dir_is_writable_and_cleans_up(self) -> None:
        created_path = None

        with support.repo_temp_dir() as tmp:
            created_path = tmp
            probe = tmp / "probe.txt"
            probe.write_text("ok\n", encoding="utf-8")
            self.assertTrue(probe.exists())
            self.assertTrue(tmp.is_relative_to(support.REPO_ROOT))

        self.assertIsNotNone(created_path)
        self.assertFalse(created_path.exists())

    def test_repo_temp_dir_uses_manual_mkdir_not_tempfile_helpers(self) -> None:
        module_source = inspect.getsource(support)
        self.assertIn(".mkdir(", module_source)
        self.assertIn("uuid4", module_source)
        self.assertNotIn("mkdtemp", module_source)
        self.assertNotIn("TemporaryDirectory", module_source)

    def test_support_module_does_not_resolve_repo_root(self) -> None:
        source = inspect.getsource(support)
        self.assertNotIn("resolve()", source)

    def test_workflow_test_roots_creates_realistic_checkout_inside_parent_project(self) -> None:
        with support.workflow_test_roots() as (project_root, workflow_root):
            self.assertEqual(project_root, workflow_root.parent)
            self.assertTrue((workflow_root / "install/manifest/client_base_manifest.json").exists())
            self.assertTrue((workflow_root / "tools/csk/install_client_workflow.py").exists())
            self.assertFalse((workflow_root / "tools/csk/sync_upstream.py").exists())


if __name__ == "__main__":
    unittest.main()
