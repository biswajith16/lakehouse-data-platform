"""Centralized, idempotent application logging setup."""

from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configure the project logger and return it.

    Repeated calls do not add duplicate handlers, which keeps tests and future
    command-line entry points predictable.
    """
    logger = logging.getLogger("lakehouse")
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Unsupported logging level: {level}")

    logger.setLevel(numeric_level)
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
            )
        )
        logger.addHandler(handler)

    return logger
