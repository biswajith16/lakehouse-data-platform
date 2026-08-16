"""Tests for local incremental state persistence."""

from pathlib import Path

from src.metadata.watermarks import load_watermarks, save_watermark


def test_watermark_round_trip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("src.metadata.watermarks.PROJECT_ROOT", tmp_path)
    settings = {"metadata": {"run_history_path": "data/metadata/state.json"}}
    save_watermark(settings, "customers", "2026-01-01T00:00:00")
    assert load_watermarks(settings) == {"customers": "2026-01-01T00:00:00"}
