import unittest

from support import SHADOW_ROOT


class BootstrapContractTests(unittest.TestCase):
    def test_client_bootstrap_block_exposes_entrypoint_and_installed_skills(self) -> None:
        path = SHADOW_ROOT / "install/source/bridge/root_AGENTS_managed_block.md"
        self.assertTrue(path.exists(), "shadow bootstrap block must exist")

        text = path.read_text(encoding="utf-8")
        self.assertIn("<!-- CSK:BEGIN ROOT BOOTSTRAP -->", text)
        self.assertIn("<!-- CSK:END ROOT BOOTSTRAP -->", text)
        self.assertIn(".csk-base/ENTRYPOINT.md", text)
        self.assertIn("## Skills", text)
        self.assertIn("csk-init", text)
        self.assertIn("csk-adopt", text)
        self.assertIn("csk-project-update", text)
        self.assertIn(".agents/skills/csk-init/SKILL.md", text)
        self.assertIn(".csk-local/", text)

    def test_client_bootstrap_stays_thin_and_navigational(self) -> None:
        path = SHADOW_ROOT / "install/source/bridge/root_AGENTS_managed_block.md"
        text = path.read_text(encoding="utf-8")

        self.assertLessEqual(len(text.splitlines()), 20)
        self.assertNotIn("Planning Studio", text)
        self.assertNotIn("Hard Plan Review", text)
        self.assertNotIn("Autonomous Execution Mode", text)


if __name__ == "__main__":
    unittest.main()
