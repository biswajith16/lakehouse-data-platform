"""Generic, configuration-driven readers for local source data."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.config_loader import PROJECT_ROOT, ConfigurationError


SUPPORTED_FORMATS = frozenset({"csv", "json", "parquet"})


def validate_dataset_definition(dataset_name: str, dataset_config: dict[str, Any]) -> None:
    """Validate the minimum metadata required for generic ingestion."""
    source = dataset_config.get("source")
    if not isinstance(source, dict):
        raise ConfigurationError(f"Dataset '{dataset_name}' must define a source mapping")
    missing = [key for key in ("dataset_name", "required_columns") if key not in dataset_config]
    missing.extend(f"source.{key}" for key in ("path", "format") if key not in source)
    if missing:
        raise ConfigurationError(f"Dataset '{dataset_name}' is missing required keys: {', '.join(missing)}")
    if source["format"].lower() not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ConfigurationError(
            f"Dataset '{dataset_name}' has unsupported format '{source['format']}'. Supported formats: {supported}"
        )


def resolve_source_path(source_path: str | Path) -> Path:
    """Resolve a source path from the project root and validate it exists."""
    path = Path(source_path)
    resolved_path = path if path.is_absolute() else PROJECT_ROOT / path
    if not resolved_path.exists():
        raise FileNotFoundError(f"Configured source file was not found: {resolved_path}")
    return resolved_path


def read_source(spark: Any, dataset_name: str, dataset_config: dict[str, Any]):
    """Read CSV, JSON, or Parquet using a dataset's configuration metadata."""
    validate_dataset_definition(dataset_name, dataset_config)
    source = dataset_config["source"]
    source_path = resolve_source_path(source["path"])
    source_format = source["format"].lower()

    if source_format == "csv":
        return spark.read.option("header", "true").option("inferSchema", "true").csv(str(source_path))
    if source_format == "json":
        return spark.read.json(str(source_path))
    return spark.read.parquet(str(source_path))
