from pathlib import Path

import pytest

from safemap.benchmarks.benchmark_runner import (
    RESULT_SCHEMA_VERSION,
    dry_run_benchmarks,
    export_combined_evaluation,
    export_latex_tables,
    export_paper_tables,
    publication_metric_summary,
    run_final_evaluation,
    _failure_summary_rows,
    _failed_target_result,
    _idiom_success_counts,
    _idiom_summary_rows,
    _mode_summary_rows,
    _primary_summary_rows,
    _primary_target_result,
    _row_status,
    _selected_modes,
    _validation_status_summary_rows,
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


def test_validation_status_summary_rows_aggregate_per_check() -> None:
    rows = [
        {
            "mode": "safemap_full",
            "safemap_cargo_check_status": "passed",
            "safemap_cargo_test_status": "skipped",
            "safemap_clippy_status": "failed",
            "miri_status": "unsupported",
            "safemap_differential_status": "not_applicable",
        },
        {
            "mode": "safemap_full",
            "validation_status_counts": '{"passed": 2, "skipped": 1}',
        },
    ]

    assert _validation_status_summary_rows(rows) == [
        "| safemap_full | all | passed | 2 |",
        "| safemap_full | all | skipped | 1 |",
        "| safemap_full | cargo_check | passed | 1 |",
        "| safemap_full | cargo_test | skipped | 1 |",
        "| safemap_full | clippy | failed | 1 |",
        "| safemap_full | differential | not_applicable | 1 |",
        "| safemap_full | miri | unsupported | 1 |",
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


def test_primary_target_result_uses_declared_benchmark_target(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "expected.json").write_text(
        (
            '{"primary_function": "apply", '
            '"expected_eligibility": "unsupported"}'
        ),
        encoding="utf-8",
    )
    plans = tmp_path / "run" / "plans"
    plans.mkdir(parents=True)
    (plans / "unit_0.json").write_text(
        (
            '{"unit_id": "unit_0", "function": "helper", '
            '"status": "planned", "eligibility": "safe_translatable"}'
        ),
        encoding="utf-8",
    )
    (plans / "unit_1.json").write_text(
        (
            '{"unit_id": "unit_1", "function": "apply", '
            '"status": "rejected", "eligibility": "unsupported"}'
        ),
        encoding="utf-8",
    )

    result = _primary_target_result(
        project,
        DummyStore(tmp_path / "run"),
        {"fully_safe_accepted_unit_ids": ["unit_0"]},
    )

    assert result["primary_function"] == "apply"
    assert result["primary_expected_eligibility"] == "unsupported"
    assert result["primary_plan_status"] == "rejected"
    assert result["primary_eligible"] is False
    assert result["primary_fully_safe_accepted"] is False
    assert result["primary_outcome"] == "unsupported"
    assert result["target_functions"] == "apply"
    assert result["target_count"] == 1
    assert result["target_fully_safe_accepted_units"] == 0
    assert result["target_acceptance_rate"] == 0.0
    assert result["target_outcomes"] == '{"unsupported": 1}'


def test_primary_target_result_handles_multi_function_case_study(
    tmp_path: Path,
) -> None:
    project = tmp_path / "case"
    project.mkdir()
    (project / "expected.json").write_text(
        (
            '{"expected_functions": {'
            '"first": {"expected_eligibility": "safe_translatable"}, '
            '"second": {"expected_eligibility": "safe_translatable"}}}'
        ),
        encoding="utf-8",
    )
    plans = tmp_path / "run" / "plans"
    plans.mkdir(parents=True)
    (plans / "unit_0.json").write_text(
        (
            '{"unit_id": "unit_0", "function": "first", '
            '"status": "planned", "eligibility": "safe_translatable"}'
        ),
        encoding="utf-8",
    )
    (plans / "unit_1.json").write_text(
        (
            '{"unit_id": "unit_1", "function": "second", '
            '"status": "planned", "eligibility": "safe_translatable"}'
        ),
        encoding="utf-8",
    )

    result = _primary_target_result(
        project,
        DummyStore(tmp_path / "run"),
        {"fully_safe_accepted_unit_ids": ["unit_0"]},
    )

    assert result["primary_function"] == ""
    assert result["target_functions"] == "first,second"
    assert result["target_count"] == 2
    assert result["target_fully_safe_accepted_units"] == 1
    assert result["target_acceptance_rate"] == 0.5
    assert result["target_outcomes"] == '{"accepted": 1, "not_accepted": 1}'


def test_failed_target_result_counts_declared_target_as_failed(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "expected.json").write_text(
        (
            '{"primary_function": "read_value", '
            '"expected_eligibility": "safe_translatable_with_api_change"}'
        ),
        encoding="utf-8",
    )

    result = _failed_target_result(project)

    assert result["primary_function"] == "read_value"
    assert result["primary_fully_safe_accepted"] is False
    assert result["primary_outcome"] == "failed"
    assert result["target_count"] == 1
    assert result["target_fully_safe_accepted_units"] == 0
    assert result["target_outcomes"] == '{"failed": 1}'


def test_primary_summary_rows_aggregate_target_acceptance() -> None:
    rows = [
        {
            "mode": "safemap_full",
            "primary_function": "ok",
            "primary_fully_safe_accepted": True,
            "primary_outcome": "accepted",
        },
        {
            "mode": "safemap_full",
            "primary_function": "bad",
            "primary_fully_safe_accepted": "False",
            "primary_outcome": "unsupported",
        },
    ]

    assert _primary_summary_rows(rows) == [
        "| safemap_full | 2 | 1 | 0.500 | `accepted`: 1, `unsupported`: 1 |"
    ]


def test_selected_modes_filters_known_modes() -> None:
    selected = _selected_modes(["llm_only"])

    assert [mode.name for mode in selected] == ["llm_only"]


def test_selected_modes_rejects_unknown_modes() -> None:
    with pytest.raises(ValueError, match="Unknown benchmark mode"):
        _selected_modes(["missing"])


def test_dry_run_reports_missing_llm_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    result = dry_run_benchmarks(
        Path("examples/simple_sum"),
        tmp_path / "out",
        SafeMapConfig(),
        modes=["llm_only"],
    )

    assert result["project_count"] == 1
    assert result["modes"] == ["llm_only"]
    checks = result["checks"]
    assert checks["llm_api_key"]["status"] == "missing"
    assert any("LLM modes will run without" in item for item in result["warnings"])


def test_dry_run_reports_existing_run_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "reports"
    (output / "safemap_full" / ".safemap" / "runs").mkdir(parents=True)

    result = dry_run_benchmarks(
        Path("examples/simple_sum"),
        output,
        SafeMapConfig(),
        modes=["safemap_full"],
    )

    assert any("already contains SafeMAP run artifacts" in item for item in result["warnings"])


def test_export_paper_tables_from_benchmark_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        (
            "project,mode,status,eligible_units,fully_safe_accepted_units,"
            "fully_safe_translation_unit_acceptance_rate,idiom_success_counts,"
            "failure_categories,safemap_cargo_check_status,"
            "safemap_cargo_test_status,safemap_clippy_status,miri_status,"
            "safemap_differential_status\n"
            "demo,safemap_full,completed,2,1,0.5,"
            "\"{\"\"output_parameter\"\": {\"\"planned\"\": 1, \"\"accepted\"\": 1}}\","
            "\"{\"\"unsupported\"\": 1}\",passed,skipped,failed,unsupported,"
            "not_applicable\n"
        ),
        encoding="utf-8",
    )
    output = tmp_path / "paper.md"

    text = export_paper_tables(csv_path, output)

    assert output.read_text(encoding="utf-8") == text
    assert "| safemap_full | 1 | `completed`: 1 | 1 | 2 | 0.500 |" in text
    assert "| safemap_full | output_parameter | 1 | 1 | 1.000 |" in text
    assert "| safemap_full | unsupported | 1 |" in text
    assert "| safemap_full | cargo_check | passed | 1 |" in text
    assert "| safemap_full | differential | not_applicable | 1 |" in text


def test_markdown_and_latex_table_exports_have_summary_parity(tmp_path: Path) -> None:
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        (
            "project,mode,status,eligible_units,fully_safe_accepted_units,"
            "target_count,target_fully_safe_accepted_units,"
            "failure_categories,safemap_cargo_check_status,"
            "safemap_cargo_test_status,safemap_clippy_status,miri_status,"
            "safemap_differential_status\n"
            "demo,safemap_full,completed,2,1,1,1,"
            "\"{\"\"unsupported\"\": 1}\",passed,skipped,failed,unsupported,"
            "not_applicable\n"
        ),
        encoding="utf-8",
    )
    markdown_output = tmp_path / "paper.md"
    latex_output = tmp_path / "paper.tex"

    markdown = export_paper_tables(csv_path, markdown_output)
    latex = export_latex_tables(csv_path, latex_output)

    assert markdown_output.read_text(encoding="utf-8") == markdown
    assert latex_output.read_text(encoding="utf-8") == latex
    assert "| safemap_full | 1 | `completed`: 1 | 1 | 2 | 0.500 |" in markdown
    assert "safemap\\_full & 1 & 1 & 2 & 0.500 \\\\" in latex
    assert "| safemap_full | unsupported | 1 |" in markdown
    assert "safemap\\_full & unsupported & 1 \\\\" in latex
    assert "| safemap_full | differential | not_applicable | 1 |" in markdown
    assert (
        "safemap\\_full & differential & not\\_applicable & 1 \\\\" in latex
    )
    assert "\\label{tab:safemap-validation-statuses}" in latex


def test_export_combined_evaluation_summary(tmp_path: Path) -> None:
    main_csv = tmp_path / "main.csv"
    main_csv.write_text(
        (
            "project,mode,eligible_units,fully_safe_accepted_units,"
            "safemap_differential_status,primary_function,"
            "primary_fully_safe_accepted\n"
            "a,safemap_full,2,1,passed,foo,True\n"
            "b,safemap_full,3,2,failed,bar,False\n"
        ),
        encoding="utf-8",
    )
    case_csv = tmp_path / "case.csv"
    case_csv.write_text(
        (
            "project,mode,eligible_units,fully_safe_accepted_units,"
            "safemap_differential_status\n"
            "case,safemap_full,4,3,passed\n"
        ),
        encoding="utf-8",
    )
    output = tmp_path / "combined.md"

    text = export_combined_evaluation(
        output,
        main_csv,
        case_study_csv=case_csv,
    )

    assert output.read_text(encoding="utf-8") == text
    assert "| Microbenchmarks | safemap_full | 2 | 3 | 5 | 0.600 | 1 |" in text
    assert "| Microbenchmarks | safemap_full | 2 | 3 | 5 | 0.600 | 1 | 1 | 2 | 0.500 |" in text
    assert "| Case studies | safemap_full | 1 | 3 | 4 | 0.750 | 1 |" in text


def test_combined_evaluation_rejects_c2rust_denominator_mismatch(
    tmp_path: Path,
) -> None:
    main_csv = tmp_path / "main.csv"
    main_csv.write_text(
        "project,mode,eligible_units,fully_safe_accepted_units\n"
        "a,safemap_full,2,1\n",
        encoding="utf-8",
    )
    c2rust_csv = tmp_path / "c2rust.csv"
    c2rust_csv.write_text(
        "project,mode,eligible_units,fully_safe_accepted_units\n"
        "a,c2rust_only,1,0\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="denominator 1 does not match"):
        export_combined_evaluation(
            tmp_path / "combined.md",
            main_csv,
            c2rust_csv=c2rust_csv,
        )


def test_combined_evaluation_allows_documented_denominator_mismatch(
    tmp_path: Path,
) -> None:
    main_csv = tmp_path / "main.csv"
    main_csv.write_text(
        "project,mode,eligible_units,fully_safe_accepted_units\n"
        "a,safemap_full,2,1\n",
        encoding="utf-8",
    )
    c2rust_csv = tmp_path / "c2rust.csv"
    c2rust_csv.write_text(
        "project,mode,eligible_units,fully_safe_accepted_units\n"
        "a,c2rust_only,1,0\n",
        encoding="utf-8",
    )

    text = export_combined_evaluation(
        tmp_path / "combined.md",
        main_csv,
        c2rust_csv=c2rust_csv,
        allow_denominator_mismatch=True,
    )

    assert "| C2Rust baseline | c2rust_only | 1 | 0 | 1 |" in text


def test_publication_metric_summary_uses_canonical_csv_fields(
    tmp_path: Path,
) -> None:
    main_csv = tmp_path / "main.csv"
    main_csv.write_text(
        (
            "project,mode,status,eligible_units,fully_safe_accepted_units,"
            "target_count,target_fully_safe_accepted_units\n"
            "a,safemap_full,completed,2,1,1,1\n"
            "b,safemap_full,completed,3,2,1,0\n"
        ),
        encoding="utf-8",
    )
    c2rust_csv = tmp_path / "c2rust.csv"
    c2rust_csv.write_text(
        (
            "project,mode,status,eligible_units,fully_safe_accepted_units,"
            "target_count,target_fully_safe_accepted_units\n"
            "a,c2rust_only,completed,5,0,2,0\n"
        ),
        encoding="utf-8",
    )
    llm_csv = tmp_path / "llm.csv"
    llm_csv.write_text(
        "project,mode,status,eligible_units,fully_safe_accepted_units\n"
        "a,llm_only,no_final_output,2,0\n"
        "b,llm_only,completed,3,1\n",
        encoding="utf-8",
    )

    text = publication_metric_summary(
        main_csv,
        c2rust_csv=c2rust_csv,
        llm_subset_csv=llm_csv,
    )

    assert "`3 / 5` eligible units" in text
    assert "Declared target functions accepted: `1 / 2`" in text
    assert "C2Rust baseline: `c2rust_only` accepted `0 / 5`" in text
    assert "LLM subset `llm_only`: accepted `1 / 5`" in text
    assert "`completed`: `1`" in text
    assert "`no_final_output`: `1`" in text


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
    assert manifest["result_schema_version"] == RESULT_SCHEMA_VERSION
    assert manifest["generated_at_utc"]
    assert manifest["git_commit"]
    csv_text = (tmp_path / "final" / "benchmark_results.csv").read_text(
        encoding="utf-8"
    )
    assert "result_schema_version" in csv_text.splitlines()[0]
    assert RESULT_SCHEMA_VERSION in csv_text
    assert "primary_function" in csv_text.splitlines()[0]
    assert "primary_fully_safe_accepted" in csv_text.splitlines()[0]
    assert "target_fully_safe_accepted_units" in csv_text.splitlines()[0]
    assert "validation_status_counts" in csv_text.splitlines()[0]
    assert "safemap_cargo_check_status" in csv_text.splitlines()[0]
    assert "miri_reason" in csv_text.splitlines()[0]
    assert "miri_diagnostics" in csv_text.splitlines()[0]
    assert (tmp_path / "final" / "benchmark_results.md").exists()
    assert (tmp_path / "final" / "paper_tables.md").exists()
    assert (tmp_path / "final" / "paper_tables.tex").exists()
    assert (tmp_path / "final" / "manifest.json").exists()
