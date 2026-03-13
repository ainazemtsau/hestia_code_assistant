import unittest
from pathlib import Path


class ShadowPhase1SkillRoutingTests(unittest.TestCase):
    def test_phase1_clean_installed_skills_are_not_dead_end_stubs(self) -> None:
        root = Path("shadow/phase1-clean/install/source/base/.agents/skills")
        init_text = (root / "csk-init/SKILL.md").read_text(encoding="utf-8")
        adopt_text = (root / "csk-adopt/SKILL.md").read_text(encoding="utf-8")
        update_text = (root / "csk-project-update/SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("Shadow stub.", init_text)
        self.assertNotIn("Shadow stub.", adopt_text)
        self.assertNotIn("Shadow stub.", update_text)
        self.assertIn(".csk-base/docs/INIT_GUIDE.md", init_text)
        self.assertIn(".csk-base/docs/INIT_GUIDE.md", adopt_text)
        self.assertIn(".csk-base/docs/UPDATE_GUIDE.md", update_text)


if __name__ == "__main__":
    unittest.main()
