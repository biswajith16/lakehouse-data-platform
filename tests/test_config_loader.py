"""Tests for the Phase 1 configuration contract."""

from src.config.config_loader import load_dataset_definitions, load_datasets, load_settings


def test_settings_can_be_loaded() -> None:
    settings = load_settings()

    assert settings["pipeline"]["mode"] == "demo"
    assert settings["paths"]["bronze"] == "data/bronze"


def test_datasets_can_be_loaded() -> None:
    datasets = load_datasets()

    assert "customers" in datasets["datasets"]


def test_control_plane_dataset_contract_is_normalized() -> None:
    datasets = load_dataset_definitions("config/datasets/customers.yaml")

    assert datasets["customers"]["dataset_name"] == "customers"
    assert datasets["customers"]["output"]["table_name"] == "customers"


def test_customers_configuration_has_required_contract_keys() -> None:
    customers = load_datasets()["datasets"]["customers"]

    assert {"dataset_name", "source", "primary_key", "required_columns"} <= customers.keys()
    assert {"path", "format"} <= customers["source"].keys()
    assert {"columns"} <= customers["deduplication"].keys()
    assert {"enabled", "column"} <= customers["incremental"].keys()
