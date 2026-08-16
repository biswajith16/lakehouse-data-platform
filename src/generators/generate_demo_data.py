"""Generate deterministic, intentionally imperfect e-commerce source data."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from faker import Faker

from src.config.config_loader import load_settings
from src.utils.logging_utils import configure_logging


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCT_CATEGORIES = ("Electronics", "Home", "Books", "Clothing", "Sports")
ORDER_STATUSES = ("completed", "processing", "shipped", "cancelled")
PAYMENT_METHODS = ("card", "paypal", "bank_transfer", "gift_card")


@dataclass(frozen=True)
class GenerationSummary:
    """Record counts and controlled issue counts from one generation run."""

    customers: int
    products: int
    orders: int
    order_items: int
    payments: int
    duplicate_customer_rows: int
    duplicate_order_rows: int
    missing_emails: int
    malformed_emails: int
    null_states: int


def _timestamp(rng: random.Random, days_back: int = 730) -> str:
    """Create a deterministic ISO timestamp in a realistic recent range."""
    start = datetime(2024, 1, 1)
    return (start + timedelta(days=rng.randrange(days_back), seconds=rng.randrange(86_400))).isoformat()


def _issue_count(record_count: int, rate: float) -> int:
    """Calculate a small, bounded number of intentional source-data issues."""
    return min(record_count, max(1, round(record_count * rate))) if record_count else 0


def _write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    """Write records to a CSV file, preserving field ordering from the first row."""
    if not records:
        return
    with path.open("w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def _write_json(path: Path, records: list[dict[str, Any]]) -> None:
    """Write a deterministic JSON array for multi-format ingestion demonstrations."""
    with path.open("w", encoding="utf-8") as output_file:
        json.dump(records, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def generate_demo_data(
    output_dir: Path,
    customers_count: int = 100,
    products_count: int = 50,
    orders_count: int = 300,
    seed: int = 42,
) -> GenerationSummary:
    """Create related demo source files with controlled data-quality issues.

    IDs in the base records always maintain referential integrity. Duplicate
    source rows are added deliberately so later Silver processing can exercise
    deduplication without breaking foreign-key relationships.
    """
    if customers_count < 1 or products_count < 1 or orders_count < 1:
        raise ValueError("customers, products, and orders must each be at least 1")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    faker = Faker("en_US")
    faker.seed_instance(seed)

    customers: list[dict[str, Any]] = []
    for number in range(1, customers_count + 1):
        signup_date = _timestamp(rng, days_back=1_460)
        customers.append(
            {
                "customer_id": f"C{number:06d}",
                "first_name": faker.first_name(),
                "last_name": faker.last_name(),
                "email": faker.email(),
                "city": faker.city(),
                "state": faker.state_abbr(),
                "country": "US",
                "signup_date": signup_date,
                "updated_at": _timestamp(rng),
            }
        )

    missing_emails = _issue_count(customers_count, 0.02)
    malformed_emails = _issue_count(max(customers_count - missing_emails, 0), 0.01)
    null_states = _issue_count(customers_count, 0.01)
    for index in range(missing_emails):
        customers[index]["email"] = ""
    for index in range(malformed_emails):
        customers[missing_emails + index]["email"] = f"invalid-email-{index + 1}"
    for index in range(null_states):
        customers[-(index + 1)]["state"] = ""

    products: list[dict[str, Any]] = []
    for number in range(1, products_count + 1):
        products.append(
            {
                "product_id": f"P{number:06d}",
                "product_name": f"{faker.color_name()} {faker.word().title()} {number}",
                "category": rng.choice(PRODUCT_CATEGORIES),
                "price": f"{rng.uniform(5, 500):.2f}",
                "created_at": _timestamp(rng),
                "updated_at": _timestamp(rng),
            }
        )

    orders: list[dict[str, Any]] = []
    order_items: list[dict[str, Any]] = []
    payments: list[dict[str, Any]] = []
    for number in range(1, orders_count + 1):
        order_id = f"O{number:07d}"
        item_total = 0.0
        for item_number in range(1, rng.randint(1, 4) + 1):
            product = rng.choice(products)
            quantity = rng.randint(1, 5)
            unit_price = float(product["price"])
            line_total = round(quantity * unit_price, 2)
            item_total += line_total
            order_items.append(
                {
                    "order_item_id": f"OI{number:07d}-{item_number}",
                    "order_id": order_id,
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": f"{unit_price:.2f}",
                    "line_total": f"{line_total:.2f}",
                }
            )
        order_timestamp = _timestamp(rng)
        status = rng.choice(ORDER_STATUSES)
        orders.append(
            {
                "order_id": order_id,
                "customer_id": rng.choice(customers)["customer_id"],
                "order_timestamp": order_timestamp,
                "status": status,
                "order_total": f"{item_total:.2f}",
                "updated_at": _timestamp(rng),
            }
        )
        payments.append(
            {
                "payment_id": f"PAY{number:07d}",
                "order_id": order_id,
                "payment_method": rng.choice(PAYMENT_METHODS),
                "payment_status": "refunded" if status == "cancelled" else "paid",
                "amount": f"{item_total:.2f}",
                "payment_timestamp": order_timestamp,
            }
        )

    duplicate_customer_rows = _issue_count(customers_count, 0.01)
    duplicate_order_rows = _issue_count(orders_count, 0.01)
    customers.extend(dict(record) for record in customers[:duplicate_customer_rows])
    orders.extend(dict(record) for record in orders[:duplicate_order_rows])

    _write_csv(output_dir / "customers.csv", customers)
    _write_json(output_dir / "products.json", products)
    _write_csv(output_dir / "orders.csv", orders)
    _write_csv(output_dir / "order_items.csv", order_items)
    _write_csv(output_dir / "payments.csv", payments)

    return GenerationSummary(
        customers=len(customers),
        products=len(products),
        orders=len(orders),
        order_items=len(order_items),
        payments=len(payments),
        duplicate_customer_rows=duplicate_customer_rows,
        duplicate_order_rows=duplicate_order_rows,
        missing_emails=missing_emails,
        malformed_emails=malformed_emails,
        null_states=null_states,
    )


def _parse_arguments() -> argparse.Namespace:
    settings = load_settings()["demo_data"]
    parser = argparse.ArgumentParser(description="Generate deterministic e-commerce demo source data.")
    parser.add_argument("--customers", type=int, default=settings["default_customers"])
    parser.add_argument("--products", type=int, default=settings["default_products"])
    parser.add_argument("--orders", type=int, default=settings["default_orders"])
    parser.add_argument("--seed", type=int, default=settings["seed"])
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "data" / "demo")
    return parser.parse_args()


def main() -> None:
    """Run the generator from the command line and log its true output counts."""
    arguments = _parse_arguments()
    logger = configure_logging(load_settings()["logging"]["level"])
    summary = generate_demo_data(
        output_dir=arguments.output_dir,
        customers_count=arguments.customers,
        products_count=arguments.products,
        orders_count=arguments.orders,
        seed=arguments.seed,
    )
    logger.info("demo_data_generation_complete | %s", json.dumps(asdict(summary), sort_keys=True))


if __name__ == "__main__":
    main()
