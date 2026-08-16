"""Append-only local pipeline-run metadata for future monitoring views."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.config.config_loader import PROJECT_ROOT


@dataclass(frozen=True)
class PipelineRunMetric:
    pipeline_run_id: str
    stage: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float


def append_run_metric(settings: dict, metric: PipelineRunMetric) -> None:
    """Persist an actual execution outcome as one local JSONL record."""
    path = PROJECT_ROOT / settings["metadata"]["run_history_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(asdict(metric), sort_keys=True) + "\n")


def utc_now() -> datetime:
    """Return timezone-aware current time for run-duration calculation."""
    return datetime.now(timezone.utc)
