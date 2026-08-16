"""Small JSON-backed watermark store for local incremental processing."""

from __future__ import annotations

import json
from pathlib import Path

from src.config.config_loader import PROJECT_ROOT


def _state_path(settings: dict) -> Path:
    path = Path(settings["metadata"]["run_history_path"])
    return path if path.is_absolute() else PROJECT_ROOT / path


def load_watermarks(settings: dict) -> dict[str, str]:
    """Return stored dataset watermarks, or an empty state on first execution."""
    path = _state_path(settings)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_watermark(settings: dict, dataset_name: str, watermark: str) -> None:
    """Persist the latest successfully processed watermark for one dataset."""
    path = _state_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = load_watermarks(settings)
    state[dataset_name] = watermark
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
