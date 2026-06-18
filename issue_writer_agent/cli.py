from __future__ import annotations

import argparse
from dataclasses import dataclass
import getpass
from pathlib import Path
import sys
import tempfile

try:
    import termios
except ImportError:  # pragma: no cover - termios is unavailable on some platforms.
    termios = None  # type: ignore[assignment]

_TERMINAL_FLUSH_ERRORS = (AttributeError, OSError, ValueError)
if termios is not None:
    _TERMINAL_FLUSH_ERRORS = _TERMINAL_FLUSH_ERRORS + (termios.error,)

from .config import (
    IMPLEMENTATION_ENTITIES,
    OUTPUT_FORMATS,
    RENDER_FORMATS,
    AppConfig,
    DEFAULT_CONFIG_PATHS,
    load_config_file,
    load_config,
    write_config,
    write_default_config,
)
from .llm import LlmError, OpenAICompatibleClient
from .prompts import (
    build_question_messages,
    build_spec_messages,
    is_stop_request,
    normalize_choice,
)


@dataclass(frozen=True)
class GeneratedSpecification:
    content: str
    render_format: str


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Turn a rough software idea into an implementation-ready issue."
    )
    parser.add_argument("idea", nargs="*", help="Rough software idea to explore.")
    parser.add_argument("--config", type=Path, help="Path to a TOML config file.")
    config_group = parser.add_mutually_exclusive_group()
    config_group.add_argument(
        "--init-config",
        action="store_true",
        help="Create a starter config file and exit.",
    )
    config_group.add_argument(
        "--configure",
        action="store_true",
        help="Run guided config setup/update and exit.",
    )
    parser.add_argument(
        "--config-path",
        type=Path,
        default=DEFAULT_CONFIG_PATHS[0],
        help=(
            "Path used with --init-config or --configure. "
            "Defaults to ./issue_writer_config.toml."
        ),
    )
    args = parser.parse_args(argv)

    config_write_path = args.config or args.config_path
    if args.configure:
        return _configure_config(config_write_path)

    if args.init_config:
        return _init_config(config_write_path)

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
        output_path = _write_specification_file(specification, config.output_folder)
    except LlmError as exc:
        print(f"\nLLM error: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"\nCould not write specification file: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130

    print(f"\nSpecification written to: {output_path}\n")
    return 0


def run_interview(
    idea: str,
    config: AppConfig,
    client: OpenAICompatibleClient,
) -> GeneratedSpecification:
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
    render_format = _ask_choice(
        "Render format",
        RENDER_FORMATS,
        config.default_render_format,
    )

    content = client.chat(
        build_spec_messages(
            idea=idea,
            transcript=transcript,
            output_format=output_format,
            implementation_entity=implementation_entity,
            render_format=render_format,
            gherkin_acceptance_criteria=config.gherkin_acceptance_criteria,
        )
    )
    return GeneratedSpecification(content=content, render_format=render_format)


def _write_specification_file(
    specification: GeneratedSpecification,
    output_folder: str = "",
) -> Path:
    suffix = ".html" if specification.render_format == "html" else ".md"
    output_dir = _resolve_output_folder(output_folder)
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        delete=False,
        dir=output_dir,
        encoding="utf-8",
        prefix="issue-writer-",
        suffix=suffix,
    ) as output_file:
        output_file.write(specification.content.strip() + "\n")
        return Path(output_file.name).resolve()


def _resolve_output_folder(output_folder: str) -> Path:
    if output_folder.strip():
        return Path(output_folder).expanduser()
    return Path(tempfile.gettempdir())


def _configure_config(path: Path) -> int:
    existing = _load_config_for_onboarding(path)
    action = "Updating" if path.exists() else "Creating"

    print("\nIssue Writer Agent configuration")
    print(f"{action} config file: {path}")
    print("Press Enter to keep the value shown in brackets.")

    api_key = _ask_api_key(existing.api_key)
    model_url = _ask_required_text(
        "Model URL (OpenAI-compatible base URL)",
        existing.model_url,
    ).rstrip("/")
    model_name = _ask_required_text("Model name", existing.model_name)
    default_output_format = _ask_choice(
        "Default output format",
        OUTPUT_FORMATS,
        existing.default_output_format,
    )
    default_implementation_entity = _ask_choice(
        "Default implementer",
        IMPLEMENTATION_ENTITIES,
        existing.default_implementation_entity,
    )
    default_render_format = _ask_choice(
        "Default render format",
        RENDER_FORMATS,
        existing.default_render_format,
    )
    output_folder = _ask_output_folder(existing.output_folder)
    gherkin_acceptance_criteria = _ask_bool(
        "Use Gherkin acceptance criteria by default",
        existing.gherkin_acceptance_criteria,
    )

    config = AppConfig(
        api_key=api_key,
        model_url=model_url,
        model_name=model_name,
        default_output_format=default_output_format,
        default_implementation_entity=default_implementation_entity,
        default_render_format=default_render_format,
        output_folder=output_folder,
        gherkin_acceptance_criteria=gherkin_acceptance_criteria,
    )

    try:
        write_config(path, config)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"Could not write config file: {exc}", file=sys.stderr)
        return 1

    print(f"\nConfiguration written to: {path.resolve()}\n")
    return 0


def _load_config_for_onboarding(path: Path) -> AppConfig:
    if not path.exists():
        return AppConfig()
    try:
        return load_config_file(path)
    except (OSError, ValueError) as exc:
        print(f"Existing config could not be loaded: {exc}", file=sys.stderr)
        print("Starting from built-in defaults.", file=sys.stderr)
        return AppConfig()


def _ask_api_key(default: str) -> str:
    if default:
        label = "API key [current value hidden; press Enter to keep it, type 'clear' to remove it]"
    else:
        label = "API key [empty; press Enter to leave empty]"
    raw = _prompt_secret(label).strip()
    if not raw:
        selected = "kept" if default else "empty"
        print(f"Selected: {selected}")
        return default
    if raw.lower() == "clear":
        print("Selected: empty")
        return ""
    print("Selected: new hidden value")
    return raw


def _ask_required_text(label: str, default: str) -> str:
    while True:
        value = _prompt(f"{label} [{default}]").strip() or default
        if value:
            return value
        print("Value is required.")


def _ask_output_folder(default: str) -> str:
    if default:
        label = (
            f"Output folder [{default}; press Enter to keep it, "
            "type 'clear' to use the operating system temp folder]"
        )
    else:
        label = (
            "Output folder [operating system temp folder; "
            "press Enter to use it]"
        )
    raw = _prompt(label).strip()
    if not raw:
        selected = default or "operating system temp folder"
        print(f"Selected: {selected}")
        return default
    if raw.lower() == "clear":
        print("Selected: operating system temp folder")
        return ""
    print(f"Selected: {raw}")
    return raw


def _ask_choice(label: str, choices: tuple[str, ...], default: str) -> str:
    choice_list = ", ".join(choices)
    while True:
        raw = _prompt(
            f"{label} [{default}] ({choice_list})",
            response_label="Selection",
        ).strip()
        if not raw:
            print(f"Selected: {default}")
            return default
        normalized = normalize_choice(raw, choices)
        if normalized is not None:
            print(f"Selected: {normalized}")
            return normalized
        print(f"Please choose one of: {choice_list}")


def _ask_bool(label: str, default: bool) -> bool:
    default_label = "yes" if default else "no"
    while True:
        raw = _prompt(
            f"{label} [{default_label}] (yes, no)",
            response_label="Selection",
        ).strip()
        if not raw:
            print(f"Selected: {default_label}")
            return default
        normalized = raw.lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            print("Selected: yes")
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            print("Selected: no")
            return False
        print("Please choose yes or no.")


def _prompt(label: str, response_label: str = "Answer") -> str:
    print()
    print(label)
    print()
    _flush_pending_terminal_input()
    return input(f"{response_label}: ").strip()


def _prompt_secret(label: str) -> str:
    print()
    print(label)
    print()
    _flush_pending_terminal_input()
    return getpass.getpass("Value: ").strip()


def _flush_pending_terminal_input() -> None:
    if termios is None or not sys.stdin.isatty():
        return
    try:
        termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
    except _TERMINAL_FLUSH_ERRORS:
        return


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
