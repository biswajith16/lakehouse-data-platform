"""Tests for configuration-level validation of reusable quality rules."""

import pytest

from src.config.config_loader import ConfigurationError, load_dataset_definitions
from src.quality.validation import validate_quality_rule_config


def test_demo_datasets_declare_expected_business_rules() -> None:
    definitions = load_dataset_definitions()

    validate_quality_rule_config("products", definitions["products"]["quality_rules"])
    validate_quality_rule_config("orders", definitions["orders"]["quality_rules"])
    validate_quality_rule_config("order_items", definitions["order_items"]["quality_rules"])
    validate_quality_rule_config("payments", definitions["payments"]["quality_rules"])


def test_quality_rule_requires_complete_metadata() -> None:
    with pytest.raises(ConfigurationError, match="missing name, column, operator, or value"):
        validate_quality_rule_config("orders", [{"name": "missing_fields"}])


def test_quality_rule_rejects_unknown_operator() -> None:
    with pytest.raises(ConfigurationError, match="unsupported operator"):
        validate_quality_rule_config(
            "orders",
            [{"name": "bad", "column": "order_total", "operator": "equals", "value": 0}],
        )
