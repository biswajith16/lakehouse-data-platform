"""Command-line entry point for configurable local lakehouse processing."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import logging
import uuid
from pathlib import Path

from src.bronze.bronze_writer import bronze_output_path, write_bronze
from src.config.config_loader import ConfigurationError, load_dataset_definitions, load_settings
from src.ingestion.source_reader import read_source, validate_dataset_definition
from src.ingestion.spark_session import create_spark_session
from src.metadata.run_metrics import PipelineRunMetric, append_run_metric, utc_now
from src.gold.gold_builder import build_demo_gold
from src.quality.validation import validate_dataframe
from src.silver.silver_processor import transform_for_silver
from src.silver.silver_writer import write_quarantine, write_silver
from src.utils.logging_utils import configure_logging


def parse_arguments() -> argparse.Namespace:
    """Parse the intentionally small Phase 3 pipeline interface."""
    parser = argparse.ArgumentParser(description="Run the config-driven lakehouse pipeline.")
    parser.add_argument("--mode", choices=("demo", "user"), default="demo")
    parser.add_argument("--stage", choices=("bronze", "silver", "gold"), required=True)
    parser.add_argument("--config", type=Path, help="Dataset YAML; required in user mode.")
    parser.add_argument("--dataset", action="append", help="Dataset name to process; repeatable.")
    parser.add_argument("--run-id", default=None, help="Optional stable ID for one pipeline run.")
    arguments = parser.parse_args()
    if arguments.mode == "user" and arguments.config is None:
        parser.error("--config is required when --mode user")
    return arguments


def run_bronze(
    dataset_definitions: dict[str, dict], settings: dict, selected_datasets: list[str] | None, run_id: str
) -> None:
    """Ingest selected datasets and write each as a Delta Bronze directory."""
    logger = logging.getLogger("lakehouse")
    selected = selected_datasets or list(dataset_definitions)
    unknown = sorted(set(selected) - set(dataset_definitions))
    if unknown:
        raise ConfigurationError(f"Unknown dataset(s): {', '.join(unknown)}")

    spark = create_spark_session(settings["spark"]["app_name"])
    try:
        for dataset_name in selected:
            dataset_config = dataset_definitions[dataset_name]
            validate_dataset_definition(dataset_name, dataset_config)
            dataframe = read_source(spark, dataset_name, dataset_config)
            record_count = dataframe.count()
            output_path = write_bronze(dataframe, dataset_name, settings, run_id, dataset_config)
            logger.info(
                "bronze_write_complete | dataset=%s records_read=%s output_path=%s pipeline_run_id=%s",
                dataset_name,
                record_count,
                output_path,
                run_id,
            )
    finally:
        spark.stop()


def run_silver(
    dataset_definitions: dict[str, dict], settings: dict, selected_datasets: list[str] | None, run_id: str
) -> None:
    """Transform Bronze Delta data, quarantine failures, and write valid Silver rows."""
    logger = logging.getLogger("lakehouse")
    selected = selected_datasets or list(dataset_definitions)
    unknown = sorted(set(selected) - set(dataset_definitions))
    if unknown:
        raise ConfigurationError(f"Unknown dataset(s): {', '.join(unknown)}")

    spark = create_spark_session(settings["spark"]["app_name"])
    try:
        for dataset_name in selected:
            dataset_config = dataset_definitions[dataset_name]
            source_path = bronze_output_path(dataset_name, settings)
            if not source_path.exists():
                raise FileNotFoundError(
                    f"Bronze Delta data was not found for '{dataset_name}': {source_path}. Run --stage bronze first."
                )
            bronze_dataframe = spark.read.format("delta").load(str(source_path))
            transformed = transform_for_silver(bronze_dataframe, dataset_config)
            result = validate_dataframe(transformed, dataset_name, dataset_config)
            silver_path = write_silver(result.valid_dataframe, dataset_name, settings)
            quarantine_path = write_quarantine(
                result.invalid_dataframe, dataset_name, settings, run_id
            )
            logger.info(
                "silver_write_complete | dataset=%s metrics=%s silver_path=%s quarantine_path=%s pipeline_run_id=%s",
                dataset_name,
                asdict(result.metrics),
                silver_path,
                quarantine_path,
                run_id,
            )
    finally:
        spark.stop()


def run_gold(settings: dict) -> None:
    """Build the e-commerce demo Gold star schema from Silver Delta data."""
    spark = create_spark_session(settings["spark"]["app_name"])
    try:
        counts = build_demo_gold(spark, settings)
        logging.getLogger("lakehouse").info("gold_write_complete | table_counts=%s", counts)
    finally:
        spark.stop()


def main() -> None:
    """Run the requested pipeline stage with clear top-level failures."""
    arguments = parse_arguments()
    started_at = utc_now()
    settings = None
    run_id = arguments.run_id or str(uuid.uuid4())
    try:
        settings = load_settings()
        logger = configure_logging(settings["logging"]["level"])
        definitions = load_dataset_definitions(arguments.config if arguments.mode == "user" else None)
        if arguments.stage == "bronze":
            run_bronze(definitions, settings, arguments.dataset, run_id)
        elif arguments.stage == "silver":
            run_silver(definitions, settings, arguments.dataset, run_id)
        else:
            if arguments.mode != "demo":
                raise ConfigurationError("Gold modeling is currently available for --mode demo only")
            run_gold(settings)
        finished_at = utc_now()
        append_run_metric(settings, PipelineRunMetric(run_id, arguments.stage, "SUCCESS", started_at.isoformat(), finished_at.isoformat(), (finished_at - started_at).total_seconds()))
    except (ConfigurationError, FileNotFoundError, RuntimeError) as exc:
        if settings is not None:
            finished_at = utc_now()
            append_run_metric(settings, PipelineRunMetric(run_id, arguments.stage, "FAILED", started_at.isoformat(), finished_at.isoformat(), (finished_at - started_at).total_seconds()))
        logging.getLogger("lakehouse").error("pipeline_failed | reason=%s", exc)
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
