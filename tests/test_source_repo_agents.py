import unittest
from pathlib import Path


class SourceRepoAgentsTests(unittest.TestCase):
    def test_source_repo_agents_does_not_use_client_bootstrap(self) -> None:
        text = Path("AGENTS.md").read_text(encoding="utf-8")

        self.assertNotIn("This project has the CSK workflow installed.", text)
        self.assertNotIn(".csk-base/ENTRYPOINT.md", text)
        self.assertNotIn("<!-- CSK:BEGIN ROOT BOOTSTRAP -->", text)
        self.assertNotIn("<!-- CSK:END ROOT BOOTSTRAP -->", text)


if __name__ == "__main__":
    unittest.main()
