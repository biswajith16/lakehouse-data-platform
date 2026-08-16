"""Delta writers for validated Silver records and quarantined failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.config_loader import PROJECT_ROOT


def _zone_path(zone: str, dataset_name: str, settings: dict[str, Any]) -> Path:
    """Resolve a project-relative data-zone path for one dataset."""
    root = Path(settings["paths"][zone])
    if not root.is_absolute():
        root = PROJECT_ROOT / root
    return root / dataset_name


def write_silver(valid_df: Any, dataset_name: str, settings: dict[str, Any]) -> Path:
    """Overwrite a Silver Delta dataset for a rerunnable full-refresh phase."""
    output_path = _zone_path("silver", dataset_name, settings)
    valid_df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(str(output_path))
    return output_path


def write_quarantine(invalid_df: Any, dataset_name: str, settings: dict[str, Any], pipeline_run_id: str) -> Path:
    """Add failure metadata and write invalid records to a Delta quarantine zone."""
    try:
        from pyspark.sql import functions as functions
    except ImportError as exc:
        raise RuntimeError("PySpark is required to write quarantine records.") from exc

    output_path = _zone_path("quarantine", dataset_name, settings)
    enriched = (
        invalid_df.withColumn("validation_timestamp", functions.current_timestamp())
        .withColumn("pipeline_run_id", functions.lit(pipeline_run_id))
    )
    enriched.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(str(output_path))
    return output_path
