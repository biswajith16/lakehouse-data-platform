"""Environment-based PostgreSQL connection settings for a future serving load."""

from __future__ import annotations

import os


def postgres_dsn() -> str:
    """Build a DSN without storing credentials in repository configuration."""
    required = ("POSTGRES_HOST", "POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD")
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing PostgreSQL environment variables: {', '.join(missing)}")
    return f"postgresql://{os.environ['POSTGRES_USER']}:{os.environ['POSTGRES_PASSWORD']}@{os.environ['POSTGRES_HOST']}:{os.getenv('POSTGRES_PORT', '5432')}/{os.environ['POSTGRES_DB']}"
