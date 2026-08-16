"""Configurable normalization and type casting for the Silver layer."""

from __future__ import annotations

from typing import Any


def transform_for_silver(df: Any, dataset_config: dict[str, Any]) -> Any:
    """Trim strings, cast configured fields, and normalize configured columns."""
    try:
        from pyspark.sql import functions as functions
    except ImportError as exc:
        raise RuntimeError("PySpark is required to transform Silver data.") from exc

    transformed = df
    string_columns = [field.name for field in df.schema.fields if field.dataType.simpleString() == "string"]
    for column_name in string_columns:
        transformed = transformed.withColumn(column_name, functions.trim(functions.col(column_name)))
    for column_name, target_type in dataset_config.get("type_casts", {}).items():
        if column_name in transformed.columns:
            transformed = transformed.withColumn(column_name, functions.col(column_name).cast(target_type))
    for column_name in dataset_config.get("normalization", {}).get("lowercase_columns", []):
        if column_name in transformed.columns:
            transformed = transformed.withColumn(column_name, functions.lower(functions.col(column_name)))
    return transformed
