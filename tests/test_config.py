from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from issue_writer_agent.config import load_config, write_default_config


class ConfigTests(unittest.TestCase):
    def test_loads_toml_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(
                "\n".join(
                    [
                        'api_key = "secret"',
                        'model_url = "https://example.test/v1/"',
                        'model_name = "model-a"',
                        'default_output_format = "user_story"',
                        'default_implementation_entity = "human_team"',
                        'default_render_format = "html"',
                        "gherkin_acceptance_criteria = true",
                    ]
                ),
                encoding="utf-8",
            )

            config = load_config(path)

        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.model_url, "https://example.test/v1")
        self.assertEqual(config.model_name, "model-a")
        self.assertEqual(config.default_output_format, "user_story")
        self.assertEqual(config.default_implementation_entity, "human_team")
        self.assertEqual(config.default_render_format, "html")
        self.assertTrue(config.gherkin_acceptance_criteria)

    def test_environment_overrides_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text('model_name = "from-file"\n', encoding="utf-8")
            with patch.dict(os.environ, {"ISSUE_WRITER_MODEL_NAME": "from-env"}):
                config = load_config(path)

        self.assertEqual(config.model_name, "from-env")

    def test_rejects_invalid_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text('default_output_format = "pdf"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "default_output_format"):
                load_config(path)

    def test_rejects_invalid_render_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text('default_render_format = "pdf"\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "default_render_format"):
                load_config(path)

    def test_write_default_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            write_default_config(path)

            config = load_config(path)

        self.assertEqual(config.default_output_format, "github_issue")
        self.assertEqual(config.default_render_format, "markdown")


if __name__ == "__main__":
    unittest.main()
