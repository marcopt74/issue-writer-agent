from __future__ import annotations

from .config import IMPLEMENTATION_ENTITIES, OUTPUT_FORMATS


STOP_WORDS = {
    "done",
    "finish",
    "finished",
    "generate",
    "generate spec",
    "spec",
    "write spec",
    "write the spec",
    "draft",
    "draft issue",
    "create issue",
    "specification",
    "write specification",
    "write the specification",
    "generate specification",
}

STOP_PHRASES = (
    "write the spec",
    "write the specification",
    "generate the spec",
    "generate the specification",
    "draft the issue",
    "create the issue",
)


def is_stop_request(text: str) -> bool:
    normalized = " ".join(text.strip().lower().split())
    return normalized in STOP_WORDS or any(phrase in normalized for phrase in STOP_PHRASES)


def normalize_choice(value: str, choices: tuple[str, ...]) -> str | None:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "story": "user_story",
        "user": "user_story",
        "userstory": "user_story",
        "issue": "github_issue",
        "github": "github_issue",
        "gh_issue": "github_issue",
        "gh": "github_issue",
        "human": "human_team",
        "team": "human_team",
        "humans": "human_team",
        "ai": "ai_agent",
        "agent": "ai_agent",
        "aiagent": "ai_agent",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized in choices:
        return normalized
    return None


def build_question_messages(idea: str, transcript: list[tuple[str, str]]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You are a senior software product analyst helping define a software issue. "
                "Ask exactly one concise clarifying question at a time. "
                "Prefer questions that reduce implementation ambiguity: users, workflow, scope, "
                "inputs, outputs, edge cases, constraints, integrations, data, permissions, "
                "success criteria, and rollout. Do not draft the issue yet. "
                "If the idea is already adequately defined, ask whether the user wants to proceed "
                "to the specification."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Rough idea:\n{idea}\n\n"
                f"Conversation so far:\n{_format_transcript(transcript)}\n\n"
                "Ask the next single question. Return only the question."
            ),
        },
    ]


def build_spec_messages(
    idea: str,
    transcript: list[tuple[str, str]],
    output_format: str,
    implementation_entity: str,
    gherkin_acceptance_criteria: bool,
) -> list[dict[str, str]]:
    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"Unsupported output format: {output_format}")
    if implementation_entity not in IMPLEMENTATION_ENTITIES:
        raise ValueError(f"Unsupported implementation entity: {implementation_entity}")

    format_instructions = {
        "user_story": (
            "Write a user story with sections: Title, User Story, Context, Scope, "
            "Out of Scope, Acceptance Criteria, Unknowns and Assumptions, Implementation Notes."
        ),
        "task": (
            "Write an implementation task with sections: Title, Objective, Background, "
            "Requirements, Acceptance Criteria, Unknowns and Assumptions, Implementation Notes."
        ),
        "github_issue": (
            "Write a GitHub issue in Markdown with sections: Summary, Problem, Proposed Scope, "
            "Acceptance Criteria, Unknowns and Assumptions, Implementation Notes, Test Notes."
        ),
    }[output_format]

    audience_instruction = {
        "ai_agent": (
            "Tune the issue for an AI coding agent: be explicit about file-level discovery, "
            "edge cases, expected tests, and preserving existing behavior. Include clear constraints "
            "and avoid relying on tacit product context."
        ),
        "human_team": (
            "Tune the issue for a human development team: include rationale, collaboration points, "
            "product tradeoffs, and implementation flexibility where details are intentionally open."
        ),
    }[implementation_entity]

    acceptance_instruction = (
        "Write acceptance criteria in Gherkin Given/When/Then format."
        if gherkin_acceptance_criteria
        else "Write acceptance criteria as clear checklist bullets."
    )

    return [
        {
            "role": "system",
            "content": (
                "You are a senior product engineer writing implementation-ready software issues. "
                "Use only the provided idea and interview transcript. If the user said they do not "
                "know an answer, preserve it as an unknown instead of inventing certainty. "
                "Be specific, testable, and concise."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Rough idea:\n{idea}\n\n"
                f"Interview transcript:\n{_format_transcript(transcript)}\n\n"
                f"Output format: {output_format}\n"
                f"Implementation audience: {implementation_entity}\n"
                f"Format instructions: {format_instructions}\n"
                f"Audience instructions: {audience_instruction}\n"
                f"Acceptance criteria instructions: {acceptance_instruction}\n\n"
                "Draft the final specification now."
            ),
        },
    ]


def _format_transcript(transcript: list[tuple[str, str]]) -> str:
    if not transcript:
        return "No clarifying questions have been answered yet."
    lines: list[str] = []
    for index, (question, answer) in enumerate(transcript, start=1):
        lines.append(f"{index}. Question: {question}")
        lines.append(f"   Answer: {answer}")
    return "\n".join(lines)
