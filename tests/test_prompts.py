from __future__ import annotations

import unittest

from issue_writer_agent.prompts import (
    build_question_messages,
    build_spec_messages,
    is_stop_request,
    normalize_choice,
)


class PromptTests(unittest.TestCase):
    def test_stop_request_matches_generation_phrases(self) -> None:
        self.assertTrue(is_stop_request(" done "))
        self.assertTrue(is_stop_request("Generate spec"))
        self.assertTrue(is_stop_request("write the spec"))
        self.assertTrue(is_stop_request("Can you write the specification now?"))
        self.assertFalse(is_stop_request("I am done with login but need signup too"))

    def test_normalize_choice_aliases(self) -> None:
        self.assertEqual(
            normalize_choice("GitHub", ("user_story", "task", "github_issue")),
            "github_issue",
        )
        self.assertEqual(
            normalize_choice("human", ("ai_agent", "human_team")),
            "human_team",
        )
        self.assertEqual(normalize_choice("md", ("markdown", "html")), "markdown")
        self.assertIsNone(normalize_choice("spreadsheet", ("user_story", "task")))

    def test_question_prompt_uses_senior_product_owner_brainstorming_role(self) -> None:
        messages = build_question_messages("Add passwordless login", [])

        system_prompt = messages[0]["content"]
        self.assertIn("senior product owner", system_prompt)
        self.assertIn("user/customer outcomes", system_prompt)
        self.assertIn("business value", system_prompt)
        self.assertIn("one concise clarifying question", system_prompt)
        self.assertIn("must-have", system_prompt)

    def test_spec_prompt_preserves_unknowns_and_audience(self) -> None:
        messages = build_spec_messages(
            idea="Add passwordless login",
            transcript=[("What auth provider?", "I don't know yet")],
            output_format="github_issue",
            implementation_entity="ai_agent",
            render_format="markdown",
            gherkin_acceptance_criteria=True,
        )

        system_prompt = messages[0]["content"]
        prompt = messages[1]["content"]
        self.assertIn("senior product owner", system_prompt)
        self.assertIn("user value", system_prompt)
        self.assertIn("desired outcomes", system_prompt)
        self.assertIn("I don't know yet", prompt)
        self.assertIn("ai_agent", prompt)
        self.assertIn("Render format: markdown", prompt)
        self.assertIn("Given/When/Then", prompt)

    def test_spec_prompt_can_request_html_rendering(self) -> None:
        messages = build_spec_messages(
            idea="Export billing report",
            transcript=[],
            output_format="task",
            implementation_entity="human_team",
            render_format="html",
            gherkin_acceptance_criteria=False,
        )

        prompt = messages[1]["content"]
        self.assertIn("Render format: html", prompt)
        self.assertIn("<!doctype html>", prompt)
        self.assertIn("Do not include Markdown", prompt)


if __name__ == "__main__":
    unittest.main()
