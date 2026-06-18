from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import tomllib
from typing import Any


OUTPUT_FORMATS = ("user_story", "task", "github_issue")
IMPLEMENTATION_ENTITIES = ("ai_agent", "human_team")
RENDER_FORMATS = ("markdown", "html")


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
    default_render_format: str = "markdown"
    gherkin_acceptance_criteria: bool = False


def load_config(path: Path | None = None) -> AppConfig:
    data: dict[str, Any] = {}
    config_path = path or _first_existing_config_path()
    if config_path and config_path.exists():
        data.update(_load_toml_data(config_path))

    env_map = {
        "api_key": os.getenv("ISSUE_WRITER_API_KEY") or os.getenv("OPENAI_API_KEY"),
        "model_url": os.getenv("ISSUE_WRITER_MODEL_URL"),
        "model_name": os.getenv("ISSUE_WRITER_MODEL_NAME"),
        "default_output_format": os.getenv("ISSUE_WRITER_DEFAULT_OUTPUT_FORMAT"),
        "default_implementation_entity": os.getenv(
            "ISSUE_WRITER_DEFAULT_IMPLEMENTATION_ENTITY"
        ),
        "default_render_format": os.getenv("ISSUE_WRITER_DEFAULT_RENDER_FORMAT"),
        "gherkin_acceptance_criteria": os.getenv(
            "ISSUE_WRITER_GHERKIN_ACCEPTANCE_CRITERIA"
        ),
    }
    for key, value in env_map.items():
        if value is not None:
            data[key] = value

    return _config_from_data(data)


def load_config_file(path: Path) -> AppConfig:
    return _config_from_data(_load_toml_data(path))


def _load_toml_data(path: Path) -> dict[str, Any]:
    with path.open("rb") as config_file:
        loaded = tomllib.load(config_file)
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file {path} must contain TOML key/value data.")
    return loaded


def _config_from_data(data: dict[str, Any]) -> AppConfig:
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
        default_render_format=str(
            data.get("default_render_format", AppConfig.default_render_format)
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
    write_config(path, AppConfig())


def write_config(path: Path, config: AppConfig) -> None:
    _validate_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"api_key = {_toml_string(config.api_key)}",
                f"model_url = {_toml_string(config.model_url)}",
                f"model_name = {_toml_string(config.model_name)}",
                f"default_output_format = {_toml_string(config.default_output_format)}",
                (
                    "default_implementation_entity = "
                    f"{_toml_string(config.default_implementation_entity)}"
                ),
                f"default_render_format = {_toml_string(config.default_render_format)}",
                f"gherkin_acceptance_criteria = {_toml_bool(config.gherkin_acceptance_criteria)}",
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
    if config.default_render_format not in RENDER_FORMATS:
        raise ValueError(
            "default_render_format must be one of: " + ", ".join(RENDER_FORMATS)
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


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"
