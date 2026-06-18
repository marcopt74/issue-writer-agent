from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from issue_writer_agent.cli import (
    GeneratedSpecification,
    _ask_choice,
    _prompt,
    _write_specification_file,
    run_interview,
)
from issue_writer_agent.config import AppConfig


class FakeClient:
    def __init__(self) -> None:
        self.calls: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.2) -> str:
        self.calls.append(messages)
        if "Draft the final specification now." in messages[-1]["content"]:
            return "# Draft Issue"
        return "Who is the primary user?"


class CliTests(unittest.TestCase):
    def test_prompt_prints_question_and_answer_prompt_on_separate_lines(self) -> None:
        with (
            patch("builtins.input", return_value="JDBC access") as input_mock,
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            answer = _prompt("What is the source format?")

        self.assertEqual(answer, "JDBC access")
        input_mock.assert_called_once_with("Answer: ")
        self.assertEqual(
            stdout.getvalue(),
            "\nWhat is the source format?\n\n",
        )

    def test_run_interview_uses_defaults_when_user_presses_enter(self) -> None:
        config = AppConfig(
            default_output_format="user_story",
            default_implementation_entity="human_team",
            default_render_format="html",
        )
        client = FakeClient()

        with (
            patch("builtins.input", side_effect=["Product managers", "done", "", "", ""]),
            patch("sys.stdout"),
        ):
            spec = run_interview("Improve roadmap planning", config, client)  # type: ignore[arg-type]

        self.assertEqual(spec.content, "# Draft Issue")
        self.assertEqual(spec.render_format, "html")
        final_prompt = client.calls[-1][-1]["content"]
        self.assertIn("Output format: user_story", final_prompt)
        self.assertIn("Implementation audience: human_team", final_prompt)
        self.assertIn("Render format: html", final_prompt)
        self.assertIn("Product managers", final_prompt)

    def test_write_specification_file_uses_render_extension_and_tmp_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("issue_writer_agent.cli.tempfile.gettempdir", return_value=tmp):
                output_path = _write_specification_file(
                    GeneratedSpecification(
                        content="\n<h1>Draft Issue</h1>\n",
                        render_format="html",
                    )
                )

            self.assertEqual(output_path.parent, Path(tmp).resolve())
            self.assertEqual(output_path.suffix, ".html")
            self.assertEqual(output_path.read_text(encoding="utf-8"), "<h1>Draft Issue</h1>\n")

    def test_choice_prompt_echoes_default_selection(self) -> None:
        with (
            patch("builtins.input", return_value=""),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            choice = _ask_choice(
                "Output format",
                ("user_story", "task", "github_issue"),
                "user_story",
            )

        self.assertEqual(choice, "user_story")
        self.assertIn("Selected: user_story\n", stdout.getvalue())

    def test_choice_prompt_echoes_normalized_selection(self) -> None:
        with (
            patch("builtins.input", return_value="human"),
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            choice = _ask_choice(
                "Who will implement it",
                ("ai_agent", "human_team"),
                "ai_agent",
            )

        self.assertEqual(choice, "human_team")
        self.assertIn("Selected: human_team\n", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
