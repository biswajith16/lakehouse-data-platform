"""UI-facing helpers; execution is delegated to the existing pipeline CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from src.config.config_loader import PROJECT_ROOT


def write_dataset_config(name: str, source_path: str, source_format: str, primary_key: str, required_columns: list[str]) -> Path:
    """Create a user dataset contract from control-plane selections."""
    import yaml

    target = PROJECT_ROOT / "config" / "datasets" / f"{name}.yaml"
    config = {"dataset": {"name": name}, "source": {"path": source_path, "format": source_format}, "primary_key": [primary_key] if primary_key else [], "required_columns": required_columns, "deduplication": {"columns": [primary_key] if primary_key else []}, "incremental": {"enabled": False, "column": None}, "quality_rules": [], "output": {"table": name}}
    target.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return target


def run_pipeline(config_path: Path, stage: str) -> subprocess.CompletedProcess[str]:
    """Invoke the same engine used by command-line users."""
    return subprocess.run([sys.executable, "run_pipeline.py", "--mode", "user", "--config", str(config_path), "--stage", stage], cwd=PROJECT_ROOT, text=True, capture_output=True, check=False)
