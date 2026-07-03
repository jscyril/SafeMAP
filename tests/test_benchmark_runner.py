from pathlib import Path

import pytest

from safemap.benchmarks.benchmark_runner import (
    export_paper_tables,
    run_final_evaluation,
    _failure_summary_rows,
    _idiom_success_counts,
    _idiom_summary_rows,
    _mode_summary_rows,
    _row_status,
    _selected_modes,
)
from safemap.config import SafeMapConfig


class DummyStore:
    def __init__(self, root: Path):
        self.root = root

    def path(self, relative: str) -> Path:
        return self.root / relative


def test_row_status_reports_missing_llm_final_output(tmp_path: Path) -> None:
    log = tmp_path / "logs" / "direct_llm_error.json"
    log.parent.mkdir()
    log.write_text('{"reason": "Missing API key"}\n', encoding="utf-8")

    status, reason = _row_status(
        "llm_only",
        {"safemap": None, "safemap_compile": None},
        DummyStore(tmp_path),
    )

    assert status == "no_final_output"
    assert reason == "Missing API key"


def test_mode_summary_rows_aggregate_acceptance() -> None:
    rows = [
        {
            "mode": "safemap_full",
            "status": "completed",
            "eligible_units": 2,
            "fully_safe_accepted_units": 1,
        },
        {
            "mode": "safemap_full",
            "status": "completed",
            "eligible_units": 3,
            "fully_safe_accepted_units": 2,
        },
    ]

    assert _mode_summary_rows(rows) == [
        "| safemap_full | 2 | `completed`: 2 | 3 | 5 | 0.600 |"
    ]


def test_idiom_summary_rows_aggregate_by_mode_and_pattern() -> None:
    rows = [
        {
            "mode": "safemap_full",
            "idiom_success_counts": {
                "output_parameter": {"planned": 1, "accepted": 1}
            },
        },
        {
            "mode": "safemap_full",
            "idiom_success_counts": (
                '{"output_parameter": {"planned": 2, "accepted": 1}}'
            ),
        },
    ]

    assert _idiom_summary_rows(rows) == [
        "| safemap_full | output_parameter | 3 | 2 | 0.667 |"
    ]


def test_failure_summary_rows_aggregate_csv_json() -> None:
    rows = [
        {
            "mode": "safemap_full",
            "failure_categories": '{"unsupported": 2}',
        },
        {
            "mode": "safemap_full",
            "failure_categories": {"unsupported": 1, "validation_failed": 1},
        },
    ]

    assert _failure_summary_rows(rows) == [
        "| safemap_full | unsupported | 3 |",
        "| safemap_full | validation_failed | 1 |",
    ]


def test_idiom_success_counts_reads_plans_and_accepted_units(tmp_path: Path) -> None:
    plans = tmp_path / "plans"
    plans.mkdir()
    (plans / "unit_0.json").write_text(
        (
            '{"unit_id": "unit_0", "status": "planned", '
            '"patterns": [{"pattern": "output_parameter"}]}'
        ),
        encoding="utf-8",
    )
    (plans / "unit_1.json").write_text(
        (
            '{"unit_id": "unit_1", "status": "rejected", '
            '"patterns": [{"pattern": "nullable_pointer"}]}'
        ),
        encoding="utf-8",
    )
    (plans / "unit_2.json").write_text(
        (
            '{"unit_id": "unit_2", "status": "planned", '
            '"patterns": [{"pattern": "unguided_rewrite"}]}'
        ),
        encoding="utf-8",
    )

    counts = _idiom_success_counts(
        DummyStore(tmp_path),
        {"fully_safe_accepted_unit_ids": ["unit_0"]},
    )

    assert counts == {"output_parameter": {"planned": 1, "accepted": 1}}


def test_selected_modes_filters_known_modes() -> None:
    selected = _selected_modes(["llm_only"])

    assert [mode.name for mode in selected] == ["llm_only"]


def test_selected_modes_rejects_unknown_modes() -> None:
    with pytest.raises(ValueError, match="Unknown benchmark mode"):
        _selected_modes(["missing"])


def test_export_paper_tables_from_benchmark_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        (
            "project,mode,status,eligible_units,fully_safe_accepted_units,"
            "fully_safe_translation_unit_acceptance_rate,idiom_success_counts,"
            "failure_categories,safemap_differential_status\n"
            "demo,safemap_full,completed,2,1,0.5,"
            "\"{\"\"output_parameter\"\": {\"\"planned\"\": 1, \"\"accepted\"\": 1}}\","
            "\"{\"\"unsupported\"\": 1}\",passed\n"
        ),
        encoding="utf-8",
    )
    output = tmp_path / "paper.md"

    text = export_paper_tables(csv_path, output)

    assert output.read_text(encoding="utf-8") == text
    assert "| safemap_full | 1 | `completed`: 1 | 1 | 2 | 0.500 |" in text
    assert "| safemap_full | output_parameter | 1 | 1 | 1.000 |" in text
    assert "| safemap_full | unsupported | 1 |" in text


def test_run_final_evaluation_writes_durable_artifacts(tmp_path: Path) -> None:
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False
    config.validation.differential_test_inputs = 2

    manifest = run_final_evaluation(
        Path("examples/simple_sum"),
        tmp_path / "final",
        config,
        modes=["safemap_full"],
    )

    assert manifest["rows"] == 1
    csv_text = (tmp_path / "final" / "benchmark_results.csv").read_text(
        encoding="utf-8"
    )
    assert "miri_reason" in csv_text.splitlines()[0]
    assert "miri_diagnostics" in csv_text.splitlines()[0]
    assert (tmp_path / "final" / "benchmark_results.md").exists()
    assert (tmp_path / "final" / "paper_tables.md").exists()
    assert (tmp_path / "final" / "manifest.json").exists()
