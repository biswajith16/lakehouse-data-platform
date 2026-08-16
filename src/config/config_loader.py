"""Utilities for loading the project's YAML configuration files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigurationError(ValueError):
    """Raised when a configuration file is missing or invalid."""


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRECTORY = PROJECT_ROOT / "config"


def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML mapping and return it as a dictionary.

    Relative paths are resolved from the project root so commands work from
    any directory. The function intentionally validates only file structure;
    dataset-specific validation will arrive with later pipeline phases.
    """
    path = Path(config_path)
    resolved_path = path if path.is_absolute() else PROJECT_ROOT / path

    if not resolved_path.is_file():
        raise ConfigurationError(f"Configuration file was not found: {resolved_path}")

    try:
        with resolved_path.open("r", encoding="utf-8") as config_file:
            content = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"Invalid YAML in configuration file: {resolved_path}") from exc

    if content is None:
        raise ConfigurationError(f"Configuration file is empty: {resolved_path}")
    if not isinstance(content, dict):
        raise ConfigurationError(
            f"Configuration file must contain a top-level mapping: {resolved_path}"
        )

    return content


def load_settings() -> dict[str, Any]:
    """Load global pipeline settings."""
    return load_yaml_config(CONFIG_DIRECTORY / "settings.yaml")


def load_datasets() -> dict[str, Any]:
    """Load dataset definitions."""
    return load_yaml_config(CONFIG_DIRECTORY / "datasets.yaml")


def load_dataset_definitions(config_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    """Load either the project dataset registry or a user dataset configuration.

    A user configuration may contain a ``datasets`` mapping, a flat
    ``dataset_name`` definition, or the control-plane-friendly ``dataset.name``
    contract. All forms are normalized to the pipeline engine's flat shape.
    """
    content = load_datasets() if config_path is None else load_yaml_config(config_path)
    definitions = content.get("datasets")
    if definitions is not None:
        if not isinstance(definitions, dict) or not definitions:
            raise ConfigurationError("'datasets' must be a non-empty mapping")
        return definitions
    if isinstance(content.get("dataset_name"), str):
        return {content["dataset_name"]: content}
    dataset = content.get("dataset")
    if isinstance(dataset, dict) and isinstance(dataset.get("name"), str):
        normalized = dict(content)
        normalized["dataset_name"] = dataset["name"]
        normalized.pop("dataset", None)
        output = normalized.get("output")
        if isinstance(output, dict) and "table" in output and "table_name" not in output:
            normalized["output"] = {**output, "table_name": output["table"]}
        return {normalized["dataset_name"]: normalized}
    raise ConfigurationError(
        "Dataset configuration must contain a 'datasets' mapping or a 'dataset_name' field"
    )
