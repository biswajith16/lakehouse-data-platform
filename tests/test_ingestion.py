"""Unit tests for Phase 3 generic ingestion validation and source selection."""

from pathlib import Path

import pytest

from src.config.config_loader import ConfigurationError, load_dataset_definitions
from src.ingestion.source_reader import read_source, resolve_source_path, validate_dataset_definition


class FakeReader:
    """Small Spark reader substitute that records which read method was selected."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def option(self, key: str, value: str) -> "FakeReader":
        self.calls.append((key, value))
        return self

    def csv(self, path: str) -> str:
        self.calls.append(("csv", path))
        return "csv_dataframe"

    def json(self, path: str) -> str:
        self.calls.append(("json", path))
        return "json_dataframe"

    def parquet(self, path: str) -> str:
        self.calls.append(("parquet", path))
        return "parquet_dataframe"


class FakeSpark:
    def __init__(self) -> None:
        self.read = FakeReader()


def _dataset_config(source_path: Path, source_format: str = "csv") -> dict:
    return {
        "dataset_name": "example",
        "source": {"path": str(source_path), "format": source_format},
        "required_columns": ["id"],
    }


def test_project_dataset_definitions_load() -> None:
    definitions = load_dataset_definitions()

    assert set(definitions) == {"customers", "products", "orders", "order_items", "payments"}


def test_direct_user_dataset_definition_loads(tmp_path: Path) -> None:
    config_path = tmp_path / "dataset.yaml"
    config_path.write_text(
        "dataset_name: transactions\nsource:\n  path: data/input/transactions.csv\n  format: csv\nrequired_columns: [transaction_id]\n",
        encoding="utf-8",
    )

    definitions = load_dataset_definitions(config_path)

    assert definitions["transactions"]["source"]["format"] == "csv"


def test_source_reader_selects_csv_reader(tmp_path: Path) -> None:
    source_file = tmp_path / "source.csv"
    source_file.write_text("id\n1\n", encoding="utf-8")
    spark = FakeSpark()

    result = read_source(spark, "example", _dataset_config(source_file))

    assert result == "csv_dataframe"
    assert spark.read.calls[-1][0] == "csv"


def test_unsupported_format_is_rejected() -> None:
    with pytest.raises(ConfigurationError, match="unsupported format"):
        validate_dataset_definition("example", _dataset_config(Path("missing.xml"), "xml"))


def test_missing_source_file_has_helpful_error() -> None:
    with pytest.raises(FileNotFoundError, match="Configured source file was not found"):
        resolve_source_path("data/input/not_here.csv")
