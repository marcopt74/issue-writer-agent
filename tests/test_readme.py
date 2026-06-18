from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


class RepositoryContentTests(unittest.TestCase):
    def test_tracked_text_files_do_not_contain_local_machine_paths(self) -> None:
        blocked_patterns = [
            "/" + "Users" + r"/[^/\s`\"']+",
            "/" + "home" + r"/[^/\s`\"']+",
            r"[A-Za-z]:\\" + "Users" + r"\\[^\\\s`\"']+",
            "/" + "var" + "/" + "folders" + "/",
        ]

        tracked_files = subprocess.run(
            ["git", "ls-files"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()

        for file_name in tracked_files:
            try:
                content = Path(file_name).read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue

            for pattern in blocked_patterns:
                with self.subTest(file=file_name):
                    self.assertIsNone(re.search(pattern, content))


if __name__ == "__main__":
    unittest.main()
