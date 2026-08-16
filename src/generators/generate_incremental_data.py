"""Create a deterministic second demo batch with new and updated customer rows."""

from __future__ import annotations

import csv
from pathlib import Path

from src.generators.generate_demo_data import PROJECT_ROOT


def generate_incremental_customers(output_dir: Path) -> Path:
    """Write one update and one new customer for a reproducible merge demonstration."""
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "customers_incremental.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("customer_id", "first_name", "last_name", "email", "city", "state", "country", "signup_date", "updated_at"))
        writer.writeheader()
        writer.writerows((
            {"customer_id": "C000001", "first_name": "Updated", "last_name": "Customer", "email": "updated.customer@example.com", "city": "Austin", "state": "TX", "country": "US", "signup_date": "2024-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"},
            {"customer_id": "C999999", "first_name": "New", "last_name": "Customer", "email": "new.customer@example.com", "city": "Chicago", "state": "IL", "country": "US", "signup_date": "2026-01-01T00:00:00", "updated_at": "2026-01-01T00:00:00"},
        ))
    return path


def generate_incremental_orders(output_dir: Path) -> Path:
    """Write one updated and one new order for a reproducible merge demonstration."""
    path = output_dir / "orders_incremental.csv"
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=("order_id", "customer_id", "order_timestamp", "status", "order_total", "updated_at"))
        writer.writeheader()
        writer.writerows((
            {"order_id": "O0000001", "customer_id": "C000001", "order_timestamp": "2025-01-01T00:00:00", "status": "shipped", "order_total": "99.99", "updated_at": "2026-01-01T00:00:00"},
            {"order_id": "O9999999", "customer_id": "C999999", "order_timestamp": "2026-01-01T00:00:00", "status": "completed", "order_total": "49.99", "updated_at": "2026-01-01T00:00:00"},
        ))
    return path


if __name__ == "__main__":
    directory = PROJECT_ROOT / "data" / "demo" / "incremental"
    generate_incremental_customers(directory)
    generate_incremental_orders(directory)
