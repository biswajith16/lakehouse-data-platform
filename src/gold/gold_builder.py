"""Build the demo e-commerce star schema from validated Silver Delta tables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.config.config_loader import PROJECT_ROOT


GOLD_TABLES = ("dim_customer", "dim_product", "dim_date", "fact_orders", "fact_order_items")


def gold_table_path(table_name: str, settings: dict[str, Any]) -> Path:
    """Resolve a project-relative Delta location for one Gold table."""
    root = Path(settings["paths"]["gold"])
    return (root if root.is_absolute() else PROJECT_ROOT / root) / table_name


def _silver_path(dataset_name: str, settings: dict[str, Any]) -> Path:
    root = Path(settings["paths"]["silver"])
    return (root if root.is_absolute() else PROJECT_ROOT / root) / dataset_name


def _write_delta(df: Any, table_name: str, settings: dict[str, Any]) -> Path:
    path = gold_table_path(table_name, settings)
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(str(path))
    return path


def build_demo_gold(spark: Any, settings: dict[str, Any]) -> dict[str, int]:
    """Create a compact star schema for the demo dataset.

    Fact order grain is one order; fact order-item grain is one line item. Hash
    keys are deterministic dimension surrogate keys for this full-refresh phase.
    SCD history and incremental MERGE are intentionally deferred to Phase 6.
    """
    try:
        from pyspark.sql import functions as F
    except ImportError as exc:
        raise RuntimeError("PySpark is required to build Gold tables.") from exc

    needed = ("customers", "products", "orders", "order_items")
    missing = [name for name in needed if not _silver_path(name, settings).exists()]
    if missing:
        raise FileNotFoundError(f"Silver data missing for: {', '.join(missing)}. Run --stage silver first.")
    customers = spark.read.format("delta").load(str(_silver_path("customers", settings)))
    products = spark.read.format("delta").load(str(_silver_path("products", settings)))
    orders = spark.read.format("delta").load(str(_silver_path("orders", settings)))
    order_items = spark.read.format("delta").load(str(_silver_path("order_items", settings)))

    dim_customer = customers.select("customer_id", "first_name", "last_name", "email", "city", "state", "country").withColumn("customer_key", F.sha2("customer_id", 256))
    dim_product = products.select("product_id", "product_name", "category", "price").withColumn("product_key", F.sha2("product_id", 256))
    dim_date = orders.select(F.to_date("order_timestamp").alias("date")).distinct().withColumn("date_key", F.date_format("date", "yyyyMMdd").cast("int")).withColumn("year", F.year("date")).withColumn("month", F.month("date")).withColumn("day", F.dayofmonth("date"))
    fact_orders = orders.join(dim_customer.select("customer_id", "customer_key"), "customer_id", "left").withColumn("date_key", F.date_format(F.to_date("order_timestamp"), "yyyyMMdd").cast("int")).select("order_id", "customer_key", "date_key", "order_timestamp", "status", "order_total")
    fact_order_items = order_items.join(dim_product.select("product_id", "product_key"), "product_id", "left").select("order_item_id", "order_id", "product_key", "quantity", "unit_price", "line_total")

    tables = {"dim_customer": dim_customer, "dim_product": dim_product, "dim_date": dim_date, "fact_orders": fact_orders, "fact_order_items": fact_order_items}
    for table_name, dataframe in tables.items():
        _write_delta(dataframe, table_name, settings)
    return {table_name: dataframe.count() for table_name, dataframe in tables.items()}
