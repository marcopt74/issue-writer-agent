from __future__ import annotations

from pathlib import Path
import tomllib
import unittest


class PackagingTests(unittest.TestCase):
    def test_exposes_underscore_console_command(self) -> None:
        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

        scripts = pyproject["project"]["scripts"]

        self.assertEqual(scripts["issue_writer_agent"], "issue_writer_agent.cli:main")


if __name__ == "__main__":
    unittest.main()

