"""Reusable Spark DataFrame validation for the Silver pipeline layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config.config_loader import ConfigurationError


@dataclass(frozen=True)
class QualityMetrics:
    """Actual record counts calculated while validating one dataset."""

    input_records: int
    valid_records: int
    invalid_records: int
    duplicates_removed: int
    null_failures: int
    business_rule_failures: int


@dataclass(frozen=True)
class ValidationResult:
    """Valid and quarantined DataFrames plus quality metrics."""

    valid_dataframe: Any
    invalid_dataframe: Any
    metrics: QualityMetrics


def validate_quality_rule_config(dataset_name: str, rules: list[dict[str, Any]] | None) -> None:
    """Check business-rule metadata before a Spark job is started."""
    for rule in rules or []:
        if not {"name", "column", "operator", "value"} <= rule.keys():
            raise ConfigurationError(
                f"Dataset '{dataset_name}' has a quality rule missing name, column, operator, or value"
            )
        if rule["operator"] not in {"greater_than", "greater_than_or_equal"}:
            raise ConfigurationError(
                f"Dataset '{dataset_name}' rule '{rule['name']}' has unsupported operator '{rule['operator']}'"
            )


def _missing_value_condition(functions: Any, column_name: str) -> Any:
    """Return a null-or-blank condition that works for every Spark column type."""
    return functions.col(column_name).isNull() | (functions.trim(functions.col(column_name).cast("string")) == "")


def validate_dataframe(df: Any, dataset_name: str, dataset_config: dict[str, Any]) -> ValidationResult:
    """Split a DataFrame into valid Silver rows and quarantine candidates.

    The generic checks are driven by required columns and primary keys. Business
    rules are declared in YAML so they stay separate from ingestion logic.
    """
    try:
        from pyspark.sql import Window, functions as functions
    except ImportError as exc:
        raise RuntimeError("PySpark is required to run Silver data-quality validation.") from exc

    required_columns = dataset_config.get("required_columns", [])
    primary_key = dataset_config.get("primary_key", [])
    missing_columns = sorted(set(required_columns + primary_key) - set(df.columns))
    if missing_columns:
        raise ConfigurationError(
            f"Dataset '{dataset_name}' is missing configured columns: {', '.join(missing_columns)}"
        )
    rules = dataset_config.get("quality_rules", [])
    validate_quality_rule_config(dataset_name, rules)

    failure_expressions = []
    for column_name in required_columns:
        failure_expressions.append(
            functions.when(_missing_value_condition(functions, column_name), functions.lit(f"required_value:{column_name}"))
        )
    for column_name in primary_key:
        failure_expressions.append(
            functions.when(_missing_value_condition(functions, column_name), functions.lit(f"primary_key_null:{column_name}"))
        )

    ranked = df
    if primary_key:
        ranked = ranked.withColumn(
            "_dedupe_rank",
            functions.row_number().over(Window.partitionBy(*primary_key).orderBy(functions.monotonically_increasing_id())),
        )
        failure_expressions.append(
            functions.when(functions.col("_dedupe_rank") > 1, functions.lit("duplicate_primary_key"))
        )

    for rule in rules:
        if rule["column"] not in ranked.columns:
            raise ConfigurationError(
                f"Dataset '{dataset_name}' rule '{rule['name']}' references missing column '{rule['column']}'"
            )
        column = functions.col(rule["column"])
        failing_condition = column <= functions.lit(rule["value"])
        if rule["operator"] == "greater_than_or_equal":
            failing_condition = column < functions.lit(rule["value"])
        failure_expressions.append(
            functions.when(failing_condition, functions.lit(f"business_rule:{rule['name']}"))
        )

    failure_column = (
        functions.concat_ws(";", *failure_expressions) if failure_expressions else functions.lit("")
    )
    evaluated = ranked.withColumn("failed_rule", failure_column)
    invalid = evaluated.filter(functions.col("failed_rule") != "")
    valid = evaluated.filter(functions.col("failed_rule") == "").drop("failed_rule", "_dedupe_rank")
    invalid = invalid.drop("_dedupe_rank")

    input_records = df.count()
    invalid_records = invalid.count()
    valid_records = valid.count()
    duplicates_removed = invalid.filter(functions.instr("failed_rule", "duplicate_primary_key") > 0).count()
    null_failures = invalid.filter(
        (functions.instr("failed_rule", "required_value:") > 0)
        | (functions.instr("failed_rule", "primary_key_null:") > 0)
    ).count()
    business_rule_failures = invalid.filter(functions.instr("failed_rule", "business_rule:") > 0).count()
    return ValidationResult(
        valid_dataframe=valid,
        invalid_dataframe=invalid,
        metrics=QualityMetrics(
            input_records=input_records,
            valid_records=valid_records,
            invalid_records=invalid_records,
            duplicates_removed=duplicates_removed,
            null_failures=null_failures,
            business_rule_failures=business_rule_failures,
        ),
    )
