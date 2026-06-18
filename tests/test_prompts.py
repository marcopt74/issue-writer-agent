from __future__ import annotations

import unittest

from issue_writer_agent.prompts import (
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
        self.assertIsNone(normalize_choice("spreadsheet", ("user_story", "task")))

    def test_spec_prompt_preserves_unknowns_and_audience(self) -> None:
        messages = build_spec_messages(
            idea="Add passwordless login",
            transcript=[("What auth provider?", "I don't know yet")],
            output_format="github_issue",
            implementation_entity="ai_agent",
            gherkin_acceptance_criteria=True,
        )

        prompt = messages[1]["content"]
        self.assertIn("I don't know yet", prompt)
        self.assertIn("ai_agent", prompt)
        self.assertIn("Given/When/Then", prompt)


if __name__ == "__main__":
    unittest.main()
