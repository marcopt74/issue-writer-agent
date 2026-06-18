from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import (
    IMPLEMENTATION_ENTITIES,
    OUTPUT_FORMATS,
    AppConfig,
    DEFAULT_CONFIG_PATHS,
    load_config,
    write_default_config,
)
from .llm import LlmError, OpenAICompatibleClient
from .prompts import (
    build_question_messages,
    build_spec_messages,
    is_stop_request,
    normalize_choice,
)


PROMPT_SEPARATOR = "-" * 72


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn a rough software idea into an implementation-ready issue."
    )
    parser.add_argument("idea", nargs="*", help="Rough software idea to explore.")
    parser.add_argument("--config", type=Path, help="Path to a TOML config file.")
    parser.add_argument(
        "--init-config",
        action="store_true",
        help="Create a starter config file and exit.",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATHS[0],
        help="Path used with --init-config. Defaults to ./issue_writer_config.toml.",
    )
    args = parser.parse_args(argv)

    if args.init_config:
        return _init_config(args.config_path)

    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    idea = " ".join(args.idea).strip() or _prompt("Describe the rough idea")
    if not idea:
        print("No idea provided.", file=sys.stderr)
        return 2

    client = OpenAICompatibleClient(
        api_key=config.api_key,
        model_url=config.model_url,
        model_name=config.model_name,
    )

    try:
        specification = run_interview(idea, config, client)
    except LlmError as exc:
        print(f"\nLLM error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130

    print("\n" + specification.strip() + "\n")
    return 0


def run_interview(
    idea: str,
    config: AppConfig,
    client: OpenAICompatibleClient,
) -> str:
    transcript: list[tuple[str, str]] = []
    print("\nAnswer the questions one at a time. Type 'done' when you want the specification.\n")

    while True:
        question = client.chat(build_question_messages(idea, transcript)).strip()
        if not question:
            question = "What should be clarified before drafting the specification?"
        answer = _prompt(question)
        if is_stop_request(answer):
            break
        transcript.append((question, answer))

    output_format = _ask_choice(
        "Output format",
        OUTPUT_FORMATS,
        config.default_output_format,
    )
    implementation_entity = _ask_choice(
        "Who will implement it",
        IMPLEMENTATION_ENTITIES,
        config.default_implementation_entity,
    )

    return client.chat(
        build_spec_messages(
            idea=idea,
            transcript=transcript,
            output_format=output_format,
            implementation_entity=implementation_entity,
            gherkin_acceptance_criteria=config.gherkin_acceptance_criteria,
        )
    )


def _ask_choice(label: str, choices: tuple[str, ...], default: str) -> str:
    choice_list = ", ".join(choices)
    while True:
        raw = _prompt(
            f"{label} [{default}] ({choice_list})",
            response_label="Selection",
        ).strip()
        if not raw:
            return default
        normalized = normalize_choice(raw, choices)
        if normalized is not None:
            return normalized
        print(f"Please choose one of: {choice_list}")


def _prompt(label: str, response_label: str = "Answer") -> str:
    print()
    print(PROMPT_SEPARATOR)
    print(label)
    print()
    return input(f"{response_label}: ").strip()


def _init_config(path: Path) -> int:
    try:
        write_default_config(path)
    except FileExistsError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Could not write config file: {exc}", file=sys.stderr)
        return 1
    print(f"Created config file: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
