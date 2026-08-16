"""Write raw source records to rerunnable Bronze Delta tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.config_loader import PROJECT_ROOT
from src.ingestion.incremental import merge_to_delta
from src.metadata.watermarks import save_watermark


def bronze_output_path(dataset_name: str, settings: dict[str, Any]) -> Path:
    """Return the project-relative Delta directory for one Bronze dataset."""
    bronze_root = Path(settings["paths"]["bronze"])
    if not bronze_root.is_absolute():
        bronze_root = PROJECT_ROOT / bronze_root
    return bronze_root / dataset_name


def write_bronze(df: Any, dataset_name: str, settings: dict[str, Any], pipeline_run_id: str, dataset_config: dict[str, Any] | None = None) -> Path:
    """Attach ingestion metadata and overwrite one Delta Bronze dataset.

    Overwrite makes a same-input rerun idempotent in this initial Bronze phase.
    Incremental append and MERGE behavior are deliberately deferred to Phase 6.
    """
    try:
        from pyspark.sql import functions as functions
    except ImportError as exc:
        raise RuntimeError("PySpark is required to write Bronze Delta tables.") from exc

    output_path = bronze_output_path(dataset_name, settings)
    enriched = (
        df.withColumn("ingestion_timestamp", functions.current_timestamp())
        .withColumn("source_file", functions.input_file_name())
        .withColumn("pipeline_run_id", functions.lit(pipeline_run_id))
    )
    incremental = (dataset_config or {}).get("incremental", {})
    if incremental.get("enabled"):
        merge_to_delta(enriched, output_path, (dataset_config or {}).get("primary_key", []))
        watermark_column = incremental.get("column")
        if watermark_column and watermark_column in enriched.columns:
            watermark = enriched.agg(functions.max(watermark_column)).first()[0]
            if watermark is not None:
                save_watermark(settings, dataset_name, str(watermark))
    else:
        enriched.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(str(output_path))
    return output_path
