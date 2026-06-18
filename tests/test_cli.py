from __future__ import annotations

from io import StringIO
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from issue_writer_agent.cli import (
    GeneratedSpecification,
    _ask_choice,
    _configure_config,
    _flush_pending_terminal_input,
    _prompt,
    _write_specification_file,
    run_interview,
)
from issue_writer_agent.config import AppConfig, load_config, write_config


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
            patch("issue_writer_agent.cli._flush_pending_terminal_input") as flush_mock,
            patch("sys.stdout", new_callable=StringIO) as stdout,
        ):
            answer = _prompt("What is the source format?")

        self.assertEqual(answer, "JDBC access")
        flush_mock.assert_called_once_with()
        input_mock.assert_called_once_with("Answer: ")
        self.assertEqual(
            stdout.getvalue(),
            "\nWhat is the source format?\n\n",
        )

    def test_flush_pending_terminal_input_flushes_tty_stdin(self) -> None:
        fake_stdin = Mock()
        fake_stdin.isatty.return_value = True
        fake_stdin.fileno.return_value = 7
        fake_termios = SimpleNamespace(TCIFLUSH=0, tcflush=Mock(), error=OSError)

        with (
            patch("issue_writer_agent.cli.sys.stdin", fake_stdin),
            patch("issue_writer_agent.cli.termios", fake_termios),
        ):
            _flush_pending_terminal_input()

        fake_termios.tcflush.assert_called_once_with(7, 0)

    def test_flush_pending_terminal_input_skips_non_tty_stdin(self) -> None:
        fake_stdin = Mock()
        fake_stdin.isatty.return_value = False
        fake_termios = SimpleNamespace(TCIFLUSH=0, tcflush=Mock(), error=OSError)

        with (
            patch("issue_writer_agent.cli.sys.stdin", fake_stdin),
            patch("issue_writer_agent.cli.termios", fake_termios),
        ):
            _flush_pending_terminal_input()

        fake_termios.tcflush.assert_not_called()

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

    def test_write_specification_file_uses_configured_output_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_folder = Path(tmp) / "configured" / "issues"

            output_path = _write_specification_file(
                GeneratedSpecification(content="# Draft Issue", render_format="markdown"),
                str(output_folder),
            )

            self.assertEqual(output_path.parent, output_folder.resolve())
            self.assertEqual(output_path.suffix, ".md")
            self.assertEqual(output_path.read_text(encoding="utf-8"), "# Draft Issue\n")

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

    def test_configure_config_creates_guided_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"

            with (
                patch("issue_writer_agent.cli._prompt_secret", return_value="secret"),
                patch(
                    "builtins.input",
                    side_effect=[
                        "https://api.x.ai/v1/",
                        "grok-4.3",
                        "task",
                        "human",
                        "html",
                        str(Path(tmp) / "issues"),
                        "yes",
                    ],
                ),
                patch("sys.stdout"),
            ):
                exit_code = _configure_config(path)

            config = load_config(path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(config.api_key, "secret")
        self.assertEqual(config.model_url, "https://api.x.ai/v1")
        self.assertEqual(config.model_name, "grok-4.3")
        self.assertEqual(config.default_output_format, "task")
        self.assertEqual(config.default_implementation_entity, "human_team")
        self.assertEqual(config.default_render_format, "html")
        self.assertEqual(config.output_folder, str(Path(tmp) / "issues"))
        self.assertTrue(config.gherkin_acceptance_criteria)

    def test_configure_config_updates_existing_config_with_defaults(self) -> None:
        original = AppConfig(
            api_key="saved-secret",
            model_url="https://api.x.ai/v1",
            model_name="grok-4.3",
            default_output_format="github_issue",
            default_implementation_entity="ai_agent",
            default_render_format="markdown",
            output_folder="/tmp/issue-writer-output",
            gherkin_acceptance_criteria=False,
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            write_config(path, original)

            with (
                patch("issue_writer_agent.cli._prompt_secret", return_value=""),
                patch("builtins.input", side_effect=["", "", "", "", "", "", ""]),
                patch("sys.stdout", new_callable=StringIO) as stdout,
            ):
                exit_code = _configure_config(path)

            config = load_config(path)

        self.assertEqual(exit_code, 0)
        self.assertEqual(config, original)
        self.assertNotIn("saved-secret", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
