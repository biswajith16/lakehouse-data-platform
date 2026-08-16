"""Tests for Gold model configuration that do not require a Spark runtime."""

from src.gold.gold_builder import GOLD_TABLES, gold_table_path
from src.config.config_loader import load_settings


def test_gold_table_paths_are_project_relative() -> None:
    assert gold_table_path("fact_orders", load_settings()).name == "fact_orders"
    assert set(GOLD_TABLES) == {"dim_customer", "dim_product", "dim_date", "fact_orders", "fact_order_items"}
