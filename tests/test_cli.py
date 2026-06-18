from __future__ import annotations

from io import StringIO
import unittest
from unittest.mock import patch

from issue_writer_agent.cli import _prompt, run_interview
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
        )
        client = FakeClient()

        with (
            patch("builtins.input", side_effect=["Product managers", "done", "", ""]),
            patch("sys.stdout"),
        ):
            spec = run_interview("Improve roadmap planning", config, client)  # type: ignore[arg-type]

        self.assertEqual(spec, "# Draft Issue")
        final_prompt = client.calls[-1][-1]["content"]
        self.assertIn("Output format: user_story", final_prompt)
        self.assertIn("Implementation audience: human_team", final_prompt)
        self.assertIn("Product managers", final_prompt)


if __name__ == "__main__":
    unittest.main()
