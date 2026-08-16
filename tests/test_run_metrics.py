"""Tests for local pipeline metadata persistence."""

from src.metadata.run_metrics import PipelineRunMetric, append_run_metric


def test_run_metric_is_appended(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("src.metadata.run_metrics.PROJECT_ROOT", tmp_path)
    append_run_metric({"metadata": {"run_history_path": "data/metadata/runs.jsonl"}}, PipelineRunMetric("run-1", "bronze", "SUCCESS", "start", "end", 1.2))
    assert "run-1" in (tmp_path / "data/metadata/runs.jsonl").read_text()
