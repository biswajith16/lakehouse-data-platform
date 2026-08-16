"""Tests for deterministic e-commerce demo source generation."""

import csv
import json
from pathlib import Path

from src.generators.generate_demo_data import generate_demo_data


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source_file:
        return list(csv.DictReader(source_file))


def test_generation_creates_all_expected_files_and_columns(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, customers_count=10, products_count=5, orders_count=12)

    expected_files = {
        "customers.csv",
        "products.json",
        "orders.csv",
        "order_items.csv",
        "payments.csv",
    }
    assert {path.name for path in tmp_path.iterdir()} == expected_files

    customers = _read_csv(tmp_path / "customers.csv")
    with (tmp_path / "products.json").open(encoding="utf-8") as source_file:
        products = json.load(source_file)

    assert {"customer_id", "email", "updated_at"} <= customers[0].keys()
    assert {"product_id", "price", "category"} <= products[0].keys()


def test_generated_relationships_reference_valid_parent_ids(tmp_path: Path) -> None:
    generate_demo_data(tmp_path, customers_count=12, products_count=6, orders_count=15)

    customer_ids = {record["customer_id"] for record in _read_csv(tmp_path / "customers.csv")}
    order_ids = {record["order_id"] for record in _read_csv(tmp_path / "orders.csv")}
    with (tmp_path / "products.json").open(encoding="utf-8") as source_file:
        product_ids = {record["product_id"] for record in json.load(source_file)}

    assert all(record["customer_id"] in customer_ids for record in _read_csv(tmp_path / "orders.csv"))
    assert all(record["order_id"] in order_ids for record in _read_csv(tmp_path / "order_items.csv"))
    assert all(record["product_id"] in product_ids for record in _read_csv(tmp_path / "order_items.csv"))
    assert all(record["order_id"] in order_ids for record in _read_csv(tmp_path / "payments.csv"))


def test_generation_is_reproducible_and_contains_controlled_issues(tmp_path: Path) -> None:
    first_run = tmp_path / "first"
    second_run = tmp_path / "second"
    first_summary = generate_demo_data(first_run, 20, 8, 25, seed=99)
    second_summary = generate_demo_data(second_run, 20, 8, 25, seed=99)

    assert first_summary == second_summary
    assert first_summary.duplicate_customer_rows > 0
    assert first_summary.missing_emails > 0
    assert (first_run / "customers.csv").read_bytes() == (second_run / "customers.csv").read_bytes()
    assert (first_run / "products.json").read_bytes() == (second_run / "products.json").read_bytes()
