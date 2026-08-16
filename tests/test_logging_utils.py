"""Tests for logging setup."""

import logging

from src.utils.logging_utils import configure_logging


def test_configure_logging_returns_project_logger() -> None:
    logger = configure_logging("DEBUG")

    assert logger.name == "lakehouse"
    assert logger.level == logging.DEBUG
    assert logger.handlers
