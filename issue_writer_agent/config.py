from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import tomllib
from typing import Any


OUTPUT_FORMATS = ("user_story", "task", "github_issue")
IMPLEMENTATION_ENTITIES = ("ai_agent", "human_team")


DEFAULT_CONFIG_PATHS = (
    Path("issue_writer_config.toml"),
    Path.home() / ".config" / "issue-writer-agent" / "config.toml",
)


@dataclass(frozen=True)
class AppConfig:
    api_key: str = ""
    model_url: str = "http://localhost:11434/v1"
    model_name: str = "llama3.1"
    default_output_format: str = "github_issue"
    default_implementation_entity: str = "ai_agent"
    gherkin_acceptance_criteria: bool = False


def load_config(path: Path | None = None) -> AppConfig:
    data: dict[str, Any] = {}
    config_path = path or _first_existing_config_path()
    if config_path and config_path.exists():
        with config_path.open("rb") as config_file:
            loaded = tomllib.load(config_file)
        if not isinstance(loaded, dict):
            raise ValueError(f"Config file {config_path} must contain TOML key/value data.")
        data.update(loaded)

    env_map = {
        "api_key": os.getenv("ISSUE_WRITER_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "model_url": os.getenv("ISSUE_WRITER_MODEL_URL"),
        "model_name": os.getenv("ISSUE_WRITER_MODEL_NAME"),
        "default_output_format": os.getenv("ISSUE_WRITER_DEFAULT_OUTPUT_FORMAT"),
        "default_implementation_entity": os.getenv(
            "ISSUE_WRITER_DEFAULT_IMPLEMENTATION_ENTITY"
        ),
        "gherkin_acceptance_criteria": os.getenv(
            "ISSUE_WRITER_GHERKIN_ACCEPTANCE_CRITERIA"
        ),
    }
    for key, value in env_map.items():
        if value is not None:
            data[key] = value

    config = AppConfig(
        api_key=str(data.get("api_key", AppConfig.api_key)),
        model_url=str(data.get("model_url", AppConfig.model_url)).rstrip("/"),
        model_name=str(data.get("model_name", AppConfig.model_name)),
        default_output_format=str(
            data.get("default_output_format", AppConfig.default_output_format)
        ),
        default_implementation_entity=str(
            data.get(
                "default_implementation_entity",
                AppConfig.default_implementation_entity,
            )
        ),
        gherkin_acceptance_criteria=_to_bool(
            data.get(
                "gherkin_acceptance_criteria",
                AppConfig.gherkin_acceptance_criteria,
            )
        ),
    )
    _validate_config(config)
    return config


def write_default_config(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Config file already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                'api_key = ""',
                'model_url = "http://localhost:11434/v1"',
                'model_name = "llama3.1"',
                'default_output_format = "github_issue"',
                'default_implementation_entity = "ai_agent"',
                "gherkin_acceptance_criteria = false",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _first_existing_config_path() -> Path | None:
    for path in DEFAULT_CONFIG_PATHS:
        if path.exists():
            return path
    return None


def _validate_config(config: AppConfig) -> None:
    if not config.model_url:
        raise ValueError("model_url cannot be empty.")
    if not config.model_name:
        raise ValueError("model_name cannot be empty.")
    if config.default_output_format not in OUTPUT_FORMATS:
        raise ValueError(
            "default_output_format must be one of: " + ", ".join(OUTPUT_FORMATS)
        )
    if config.default_implementation_entity not in IMPLEMENTATION_ENTITIES:
        raise ValueError(
            "default_implementation_entity must be one of: "
            + ", ".join(IMPLEMENTATION_ENTITIES)
        )


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)

