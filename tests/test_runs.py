import json
from pathlib import Path

from safemap.runs import latest_run, summarize_runs


def test_latest_run_returns_newest_named_run(tmp_path: Path) -> None:
    runs = tmp_path / ".safemap" / "runs"
    older = runs / "20260101T000000Z-alpha-11111111"
    newer = runs / "20260102T000000Z-beta-22222222"
    older.mkdir(parents=True)
    newer.mkdir()

    assert latest_run(tmp_path) == newer


def test_latest_run_finds_mode_subdirectory_runs(tmp_path: Path) -> None:
    run = (
        tmp_path / "safemap_full" / ".safemap" / "runs"
        / "20260102T000000Z-beta-22222222"
    )
    run.mkdir(parents=True)

    assert latest_run(tmp_path) == run


def test_summarize_runs_reads_metrics_status_and_validation(tmp_path: Path) -> None:
    run = tmp_path / ".safemap" / "runs" / "20260101T000000Z-demo-11111111"
    (run / "reports").mkdir(parents=True)
    (run / "validation").mkdir()
    (run / "reports" / "metrics.json").write_text(
        json.dumps({
            "project": "demo",
            "total_units": 2,
            "eligible_units": 1,
            "fully_safe_accepted_units": 1,
            "fully_safe_translation_unit_acceptance_rate": 1.0,
            "safemap_compile": True,
        }),
        encoding="utf-8",
    )
    (run / "run_status.json").write_text(
        json.dumps({"status": "completed", "baseline_status": "skipped"}),
        encoding="utf-8",
    )
    (run / "validation" / "results.json").write_text(
        json.dumps({"differential": {"status": "passed"}}),
        encoding="utf-8",
    )

    assert summarize_runs(tmp_path) == [{
        "run_dir": str(run),
        "project": "demo",
        "status": "completed",
        "baseline_status": "skipped",
        "total_units": 2,
        "eligible_units": 1,
        "fully_safe_accepted_units": 1,
        "fully_safe_translation_unit_acceptance_rate": 1.0,
        "safemap_compile": True,
        "differential_status": "passed",
    }]
