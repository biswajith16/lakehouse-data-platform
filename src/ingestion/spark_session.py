"""Single place for Spark and Delta Lake session construction."""

from __future__ import annotations


def create_spark_session(app_name: str):
    """Create a local Spark session configured to read and write Delta tables.

    Imports remain inside this function so configuration-only tooling and unit
    tests do not require a full Spark installation.
    """
    try:
        from delta import configure_spark_with_delta_pip
        from pyspark.sql import SparkSession
    except ImportError as exc:
        raise RuntimeError(
            "PySpark and delta-spark are required to run ingestion. Install requirements.txt first."
        ) from exc

    builder = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    return configure_spark_with_delta_pip(builder).getOrCreate()
