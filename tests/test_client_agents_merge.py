import unittest
from pathlib import Path

from tools.csk.install_lib import BEGIN_MARKER, END_MARKER, ensure_root_agents_block
from tests.support import repo_temp_dir


def managed_block(body: str) -> str:
    return f"{BEGIN_MARKER}\n{body}\n{END_MARKER}\n"


class ClientAgentsMergeTests(unittest.TestCase):
    def test_existing_file_keeps_client_content(self) -> None:
        with repo_temp_dir() as tmp:
            path = tmp / "AGENTS.md"
            path.write_text("# Client notes\n\nKeep this content.\n", encoding="utf-8")
            ensure_root_agents_block(path, managed_block("bootstrap v1"))
            text = path.read_text(encoding="utf-8")
            self.assertIn("# Client notes", text)
            self.assertIn("Keep this content.", text)
            self.assertIn("bootstrap v1", text)
            self.assertEqual(text.count(BEGIN_MARKER), 1)
            self.assertEqual(text.count(END_MARKER), 1)

    def test_rerun_updates_only_managed_block(self) -> None:
        with repo_temp_dir() as tmp:
            path = tmp / "AGENTS.md"
            path.write_text("Client intro\n\nLocal workflow notes.\n", encoding="utf-8")
            ensure_root_agents_block(path, managed_block("bootstrap v1"))
            ensure_root_agents_block(path, managed_block("bootstrap v2"))
            text = path.read_text(encoding="utf-8")
            self.assertIn("Client intro", text)
            self.assertIn("Local workflow notes.", text)
            self.assertNotIn("bootstrap v1", text)
            self.assertIn("bootstrap v2", text)
            self.assertEqual(text.count(BEGIN_MARKER), 1)

    def test_missing_file_is_created(self) -> None:
        with repo_temp_dir() as tmp:
            path = tmp / "AGENTS.md"
            action = ensure_root_agents_block(path, managed_block("bootstrap v1"))
            self.assertEqual(action, "created")
            self.assertTrue(path.exists())
            self.assertIn("bootstrap v1", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
