from __future__ import annotations

import csv
from pathlib import Path

import pytest

from scripts.run_conference_heldout import merge_stage_results


def _write_results(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["project", "mode", "status"])
        writer.writeheader()
        writer.writerows(rows)


def test_merge_stage_results_is_sorted_and_complete(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    _write_results(first / "benchmark_results.csv", [
        {"project": "libcsv", "mode": "safemap_deterministic", "status": "completed"},
        {"project": "cjson", "mode": "c2rust_only", "status": "completed"},
    ])
    _write_results(second / "benchmark_results.csv", [
        {"project": "cjson", "mode": "llm_only", "status": "failed"},
    ])

    output = tmp_path / "combined.csv"
    assert merge_stage_results([first, second], output) == 3
    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [(row["project"], row["mode"]) for row in rows] == [
        ("cjson", "c2rust_only"),
        ("cjson", "llm_only"),
        ("libcsv", "safemap_deterministic"),
    ]


def test_merge_stage_results_rejects_duplicate_project_mode(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    row = {"project": "inih", "mode": "llm_only", "status": "completed"}
    _write_results(first / "benchmark_results.csv", [row])
    _write_results(second / "benchmark_results.csv", [row])

    with pytest.raises(ValueError, match="duplicate"):
        merge_stage_results([first, second], tmp_path / "combined.csv")


def test_merge_stage_results_rejects_schema_drift(tmp_path: Path) -> None:
    first = tmp_path / "non-llm"
    second = tmp_path / "llm"
    _write_results(first / "benchmark_results.csv", [
        {"project": "inih", "mode": "c2rust_only", "status": "completed"},
    ])
    second.mkdir(parents=True)
    (second / "benchmark_results.csv").write_text(
        "project,mode,reason\ninih,llm_only,quota\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="schemas differ"):
        merge_stage_results([first, second], tmp_path / "combined.csv")
