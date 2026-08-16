"""Delta Lake upsert operations used by configuration-driven incremental loads."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def merge_to_delta(df: Any, target_path: Path, primary_key: list[str]) -> None:
    """Insert new records and update changed records using Delta MERGE."""
    if not primary_key:
        raise ValueError("Incremental Delta MERGE requires at least one primary key column")
    try:
        from delta.tables import DeltaTable
    except ImportError as exc:
        raise RuntimeError("delta-spark is required for incremental Delta MERGE.") from exc

    if not target_path.exists():
        df.write.format("delta").mode("overwrite").save(str(target_path))
        return
    condition = " AND ".join(f"target.{column} = source.{column}" for column in primary_key)
    (
        DeltaTable.forPath(df.sparkSession, str(target_path))
        .alias("target")
        .merge(df.alias("source"), condition)
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
