from __future__ import annotations

import csv
import copy
import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from ..config import SafeMapConfig
from ..llm.client import LLMClient
from ..pipeline import run_pipeline
from .baseline_runner import BASELINES

RESULT_SCHEMA_VERSION = "safemap.benchmark_results.v1"


def run_benchmarks(
    benchmarks: Path,
    output_csv: Path,
    config: SafeMapConfig,
    client: LLMClient | None = None,
    modes: list[str] | None = None,
) -> list[dict]:
    selected = _selected_modes(modes)
    metadata = _artifact_metadata()
    projects = sorted({
        file.parent for file in benchmarks.rglob("*.c")
        if ".safemap" not in file.parts
    })
    rows = []
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    for project in projects:
        for mode in selected:
            mode_config = copy.deepcopy(config)
            mode_config.translation.use_c2rust = mode.use_c2rust
            mode_config.translation.use_llm = mode.use_llm
            mode_config.translation.use_static_guidance = mode.guided
            try:
                store = run_pipeline(
                    project, output_csv.parent / mode.name, mode_config, client
                )
                metrics = json.loads(
                    store.path("reports/metrics.json").read_text(encoding="utf-8")
                )
                baseline = metrics.get("baseline") or {}
                final = metrics.get("safemap") or {}
                validation = _read_json_if_exists(store.path("validation/results.json"))
                compile_check = _validation_check(validation, "compile")
                test_check = _validation_check(validation, "tests")
                clippy_check = _validation_check(validation, "clippy")
                differential = validation.get("differential", {}) if validation else {}
                miri = validation.get("miri", {}) if validation else {}
                miri_passed = miri.get("passed")
                miri_failed = miri.get("failed")
                row_status, row_reason = _row_status(mode.name, metrics, store)
                idiom_success_counts = _idiom_success_counts(store, metrics)
                primary = _primary_target_result(project, store, metrics)
                rows.append({
                    **metadata,
                    "project": project.name,
                    "mode": mode.name,
                    "run_dir": str(store.root),
                    **primary,
                    "loc_c": sum(
                        len(f.read_text().splitlines()) for f in project.rglob("*.c")
                    ),
                    "total_units": metrics.get("total_units"),
                    "eligible_units": metrics.get("eligible_units"),
                    "fully_safe_accepted_units": metrics.get(
                        "fully_safe_accepted_units"
                    ),
                    "fully_safe_translation_unit_acceptance_rate": metrics.get(
                        "fully_safe_translation_unit_acceptance_rate"
                    ),
                    "eligibility_counts": json.dumps(
                        metrics.get("eligibility_counts", {}), sort_keys=True
                    ),
                    "idiom_success_counts": json.dumps(
                        idiom_success_counts, sort_keys=True
                    ),
                    "failure_categories": json.dumps(
                        metrics.get("failure_categories", {}), sort_keys=True
                    ),
                    "loc_rust_baseline": _rust_loc(store.path("baseline/rust")),
                    "loc_rust_safemap": _rust_loc(store.path("final/rust")),
                    "c2rust_compile": metrics.get("baseline_compile"),
                    "safemap_compile": metrics.get("safemap_compile"),
                    "c2rust_tests": "",
                    "safemap_tests": metrics.get("test_pass_rate"),
                    "safemap_cargo_check_status": compile_check.get("status", ""),
                    "safemap_cargo_check_reason": compile_check.get("reason", ""),
                    "safemap_cargo_test_status": test_check.get("status", ""),
                    "safemap_cargo_test_reason": test_check.get("reason", ""),
                    "safemap_clippy_status": clippy_check.get("status", ""),
                    "safemap_clippy_reason": clippy_check.get("reason", ""),
                    "safemap_differential_status": differential.get("status"),
                    "safemap_differential_reason": differential.get("reason", ""),
                    "validation_status_counts": json.dumps(
                        _validation_status_counts(validation), sort_keys=True
                    ),
                    "c2rust_unsafe_blocks": baseline.get("unsafe_blocks"),
                    "safemap_unsafe_blocks": final.get("unsafe_blocks"),
                    "c2rust_raw_pointers": baseline.get("raw_pointer_types"),
                    "safemap_raw_pointers": final.get("raw_pointer_types"),
                    "clippy_warnings": "",
                    "miri_status": miri.get("status"),
                    "miri_reason": miri.get("reason"),
                    "miri_passed": miri_passed if miri_passed is not None else "",
                    "miri_failed": miri_failed if miri_failed is not None else "",
                    "miri_diagnostics": _diagnostic_summary(miri.get("errors", [])),
                    "differential_pass_rate": metrics.get("differential_pass_rate"),
                    "repair_attempts": metrics.get("repair_attempts", 0),
                    "llm_calls": metrics.get("llm_calls", 0),
                    "llm_input_tokens": metrics.get("llm_input_tokens", 0),
                    "llm_output_tokens": metrics.get("llm_output_tokens", 0),
                    "status": row_status,
                    "reason": row_reason,
                })
            except Exception as error:
                rows.append({
                    **metadata,
                    "project": project.name, "mode": mode.name,
                    **_failed_target_result(project),
                    "status": "failed", "reason": str(error),
                })
    columns = [
        "result_schema_version", "generated_at_utc", "git_commit",
        "project", "mode", "status", "reason", "run_dir", "loc_c",
        "primary_function", "primary_expected_eligibility",
        "primary_plan_status", "primary_eligible",
        "primary_fully_safe_accepted", "primary_outcome",
        "target_functions", "target_count",
        "target_fully_safe_accepted_units", "target_acceptance_rate",
        "target_outcomes",
        "total_units", "eligible_units", "fully_safe_accepted_units",
        "fully_safe_translation_unit_acceptance_rate", "eligibility_counts",
        "idiom_success_counts", "failure_categories", "loc_rust_baseline",
        "loc_rust_safemap", "c2rust_compile", "safemap_compile", "c2rust_tests",
        "safemap_tests", "safemap_cargo_check_status",
        "safemap_cargo_check_reason", "safemap_cargo_test_status",
        "safemap_cargo_test_reason", "safemap_clippy_status",
        "safemap_clippy_reason", "safemap_differential_status",
        "safemap_differential_reason", "validation_status_counts",
        "c2rust_unsafe_blocks",
        "safemap_unsafe_blocks", "c2rust_raw_pointers", "safemap_raw_pointers",
        "clippy_warnings", "miri_status", "miri_reason", "miri_passed",
        "miri_failed", "miri_diagnostics", "differential_pass_rate",
        "repair_attempts", "llm_calls", "llm_input_tokens", "llm_output_tokens",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary = [
        "# SafeMAP Benchmark Summary",
        "",
        "## Mode Summary",
        "",
        "| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |",
        "|---|---:|---|---:|---:|---:|",
        *_mode_summary_rows(rows),
        "",
        "## Declared Target Summary",
        "",
        "| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |",
        "|---|---:|---:|---:|---|",
        *_primary_summary_rows(rows),
        "",
        "## Idiom Success",
        "",
        "| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |",
        "|---|---|---:|---:|---:|",
        *_idiom_summary_rows(rows),
        "",
        "## Validation Statuses",
        "",
        "| Mode | Check | Status | Count |",
        "|---|---|---|---:|",
        *_validation_status_summary_rows(rows),
        "",
        "## Project Results",
        "",
        "| Project | Mode | Status | Accepted | Acceptance Rate | Differential | Miri |",
        "|---|---|---|---:|---:|---|---|",
    ]
    summary.extend(
        "| {project} | {mode} | {status} | {accepted} | {rate} | {diff} | {miri} |".format(
            project=row.get("project", ""),
            mode=row.get("mode", ""),
            status=row.get("status", ""),
            accepted=row.get("fully_safe_accepted_units", ""),
            rate=row.get("fully_safe_translation_unit_acceptance_rate", ""),
            diff=row.get("safemap_differential_status", ""),
            miri=row.get("miri_status", ""),
        )
        for row in rows
    )
    output_csv.with_suffix(".md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return rows


def dry_run_benchmarks(
    benchmarks: Path,
    output: Path,
    config: SafeMapConfig,
    modes: list[str] | None = None,
) -> dict[str, object]:
    selected = _selected_modes(modes)
    projects = sorted({
        file.parent for file in benchmarks.rglob("*.c")
        if ".safemap" not in file.parts
    })
    checks = _preflight_checks(config, selected)
    return {
        **_artifact_metadata(),
        "benchmarks": str(benchmarks),
        "output": str(output),
        "project_count": len(projects),
        "projects": [project.name for project in projects],
        "modes": [mode.name for mode in selected],
        "checks": checks,
        "warnings": _preflight_warnings(config, selected, output, checks),
    }


def export_paper_tables(input_csv: Path, output_md: Path) -> str:
    with input_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    summary = [
        "# SafeMAP Paper Tables",
        "",
        "## Mode Summary",
        "",
        "| Mode | Rows | Status Counts | Accepted Units | Eligible Units | Acceptance Rate |",
        "|---|---:|---|---:|---:|---:|",
        *_mode_summary_rows(rows),
        "",
        "## Declared Target Summary",
        "",
        "| Mode | Target Functions | Accepted Target Functions | Acceptance Rate | Outcomes |",
        "|---|---:|---:|---:|---|",
        *_primary_summary_rows(rows),
        "",
        "## Idiom Success",
        "",
        "| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |",
        "|---|---|---:|---:|---:|",
        *_idiom_summary_rows(rows),
        "",
        "## Failure Categories",
        "",
        "| Mode | Category | Count |",
        "|---|---|---:|",
        *_failure_summary_rows(rows),
        "",
        "## Validation Statuses",
        "",
        "| Mode | Check | Status | Count |",
        "|---|---|---|---:|",
        *_validation_status_summary_rows(rows),
        "",
        "## Project Results",
        "",
        "| Project | Mode | Status | Accepted | Acceptance Rate | Differential | Miri |",
        "|---|---|---|---:|---:|---|---|",
    ]
    summary.extend(
        "| {project} | {mode} | {status} | {accepted} | {rate} | {diff} | {miri} |".format(
            project=row.get("project", ""),
            mode=row.get("mode", ""),
            status=row.get("status", ""),
            accepted=row.get("fully_safe_accepted_units", ""),
            rate=row.get("fully_safe_translation_unit_acceptance_rate", ""),
            diff=row.get("safemap_differential_status", ""),
            miri=row.get("miri_status", ""),
        )
        for row in rows
    )
    text = "\n".join(summary) + "\n"
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(text, encoding="utf-8")
    return text


def export_latex_tables(input_csv: Path, output_tex: Path) -> str:
    with input_csv.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    text = "\n\n".join([
        _latex_mode_summary(rows),
        _latex_target_summary(rows),
        _latex_failure_summary(rows),
        _latex_validation_status_summary(rows),
    ]) + "\n"
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(text, encoding="utf-8")
    return text


def export_combined_evaluation(
    output_md: Path,
    main_csv: Path,
    case_study_csv: Path | None = None,
    c2rust_csv: Path | None = None,
    llm_smoke_csv: Path | None = None,
    allow_denominator_mismatch: bool = False,
) -> str:
    if c2rust_csv is not None and not allow_denominator_mismatch:
        _validate_baseline_denominator(main_csv, c2rust_csv)
    sections = [
        "# SafeMAP Combined Evaluation Summary",
        "",
        "## Evaluation Overview",
        "",
        "| Dataset | Mode | Rows | Accepted Units | Eligible Units | Acceptance Rate | Differential Passed | Accepted Target Functions | Target Functions | Target Function Rate | Notes |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    sections.extend(_combined_summary_rows([
        ("Microbenchmarks", main_csv, "SafeMAP fully safe output"),
        ("Case studies", case_study_csv, "Authored module-shaped case studies"),
        ("C2Rust baseline", c2rust_csv, "Strict SafeMAP acceptance applied to raw C2Rust baseline"),
        ("LLM subset", llm_smoke_csv, "Optional bounded LLM subset"),
    ]))
    sections.extend([
        "",
        "## Interpretation",
        "",
        "- Accepted units are counted only when the final Rust output satisfies SafeMAP's fully safe policy.",
        "- C2Rust baseline rows are not treated as SafeMAP success unless they satisfy the same no-unsafe/no-raw-pointer policy.",
        "- LLM subset results are latency/model dependent and should not be generalized to the full benchmark suite.",
        "- Unsupported C constructs are reported as explicit outcomes rather than crashes.",
        "",
    ])
    text = "\n".join(sections)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(text, encoding="utf-8")
    return text


def publication_metric_summary(
    main_csv: Path,
    case_study_csv: Path | None = None,
    c2rust_csv: Path | None = None,
    llm_subset_csv: Path | None = None,
) -> str:
    sections = [
        "# SafeMAP Publication Metric Summary",
        "",
        _publication_dataset_sentence(
            "Microbenchmarks",
            main_csv,
            "safemap_full",
            include_targets=True,
        ),
    ]
    if case_study_csv is not None:
        sections.append(_publication_dataset_sentence(
            "Case studies",
            case_study_csv,
            "safemap_full",
            include_targets=True,
        ))
    if c2rust_csv is not None:
        sections.append(_publication_dataset_sentence(
            "C2Rust baseline",
            c2rust_csv,
            "c2rust_only",
            include_targets=True,
        ))
    if llm_subset_csv is not None:
        sections.extend(_publication_llm_sentences(llm_subset_csv))
    sections.extend([
        "",
        "Use these numbers with the restricted-subset SafeMAP claim. Do not "
        "treat LLM subset rows as a full LLM baseline unless the evaluated "
        "scope is explicitly described.",
    ])
    return "\n".join(item for item in sections if item) + "\n"


def run_final_evaluation(
    benchmarks: Path,
    output_dir: Path,
    config: SafeMapConfig,
    client: LLMClient | None = None,
    modes: list[str] | None = None,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_csv = output_dir / "benchmark_results.csv"
    rows = run_benchmarks(
        benchmarks, benchmark_csv, config, client=client, modes=modes
    )
    benchmark_summary = benchmark_csv.with_suffix(".md")
    paper_tables = output_dir / "paper_tables.md"
    latex_tables = output_dir / "paper_tables.tex"
    export_paper_tables(benchmark_csv, paper_tables)
    export_latex_tables(benchmark_csv, latex_tables)
    manifest = {
        **_artifact_metadata(),
        "benchmarks": str(benchmarks),
        "output_dir": str(output_dir),
        "rows": len(rows),
        "modes": sorted({row.get("mode", "") for row in rows}),
        "artifacts": {
            "benchmark_csv": str(benchmark_csv),
            "benchmark_summary": str(benchmark_summary),
            "paper_tables": str(paper_tables),
            "latex_tables": str(latex_tables),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _publication_dataset_sentence(
    label: str,
    csv_path: Path,
    mode: str,
    include_targets: bool = False,
) -> str:
    rows = [
        row for row in _read_csv_if_exists(csv_path)
        if row.get("mode", "") == mode
    ]
    if not rows:
        return f"- {label}: no `{mode}` rows found in `{csv_path}`."
    accepted = sum(_int(row.get("fully_safe_accepted_units")) for row in rows)
    eligible = sum(_int(row.get("eligible_units")) for row in rows)
    rate = accepted / eligible if eligible else 0.0
    sentence = (
        f"- {label}: `{mode}` accepted `{accepted} / {eligible}` eligible "
        f"units across `{len(rows)}` rows (`{rate:.3f}` acceptance rate)."
    )
    if include_targets:
        target_total = sum(_target_count(row) for row in rows)
        target_accepted = sum(_target_accepted_count(row) for row in rows)
        target_rate = target_accepted / target_total if target_total else 0.0
        sentence += (
            f" Declared target functions accepted: `{target_accepted} / "
            f"{target_total}` (`{target_rate:.3f}`)."
        )
    return sentence


def _publication_llm_sentences(csv_path: Path) -> list[str]:
    rows = _read_csv_if_exists(csv_path)
    if not rows:
        return [f"- LLM subset: no rows found in `{csv_path}`."]
    output = []
    for mode in sorted({row.get("mode", "") for row in rows}):
        mode_rows = [row for row in rows if row.get("mode", "") == mode]
        accepted = sum(_int(row.get("fully_safe_accepted_units")) for row in mode_rows)
        eligible = sum(_int(row.get("eligible_units")) for row in mode_rows)
        rate = accepted / eligible if eligible else 0.0
        statuses: dict[str, int] = {}
        for row in mode_rows:
            status = row.get("status", "")
            statuses[status] = statuses.get(status, 0) + 1
        status_text = ", ".join(
            f"`{name}`: `{count}`" for name, count in sorted(statuses.items())
        )
        output.append(
            f"- LLM subset `{mode}`: accepted `{accepted} / {eligible}` "
            f"eligible units across `{len(mode_rows)}` rows (`{rate:.3f}`); "
            f"row statuses: {status_text}."
        )
    return output


def _artifact_metadata() -> dict[str, str]:
    return {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).replace(
            microsecond=0
        ).isoformat().replace("+00:00", "Z"),
        "git_commit": _git_commit(),
    }


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _tool_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "clang": _command_version(["clang", "--version"]),
        "rustc": _command_version(["rustc", "--version"]),
        "cargo": _command_version(["cargo", "--version"]),
        "clippy": _command_version(["cargo", "clippy", "--version"]),
        "c2rust": _command_version(["c2rust", "--version"]),
        "miri": _command_version(["cargo", "miri", "--version"]),
    }


def _preflight_checks(config: SafeMapConfig, modes) -> dict[str, dict[str, str]]:
    checks = {
        "python": _tool_check(["python", "--version"]),
        "clang": _tool_check(["clang", "--version"]),
        "cargo": _tool_check(["cargo", "--version"]),
    }
    if config.validation.run_clippy:
        checks["clippy"] = _tool_check(["cargo", "clippy", "--version"])
    if config.validation.run_miri:
        checks["miri"] = _tool_check(["cargo", "miri", "--version"])
    if any(mode.use_c2rust for mode in modes):
        checks["c2rust"] = _tool_check(["c2rust", "--version"])
    if any(mode.use_llm for mode in modes):
        value = os.getenv(config.llm.api_key_env)
        checks["llm_api_key"] = {
            "status": "available" if value else "missing",
            "detail": (
                f"{config.llm.api_key_env} is set"
                if value else _missing_llm_key_warning(config)
            ),
        }
    return checks


def _preflight_warnings(
    config: SafeMapConfig,
    modes,
    output: Path,
    checks: dict[str, dict[str, str]],
) -> list[str]:
    warnings = [
        item["detail"]
        for item in checks.values()
        if item["status"] not in {"available", "optional_unavailable"}
    ]
    if any(mode.use_llm for mode in modes) and checks.get(
        "llm_api_key", {}
    ).get("status") == "missing":
        warnings.append(
            "LLM modes will run without a usable API key and are expected to "
            "produce no final output unless a test client is injected."
        )
    if _has_existing_run_artifacts(output):
        warnings.append(
            f"{output} already contains SafeMAP run artifacts; use a fresh "
            "output directory when producing publication snapshots."
        )
    return warnings


def _tool_check(command: list[str]) -> dict[str, str]:
    version = _command_version(command)
    if version == "unavailable":
        return {
            "status": "missing",
            "detail": f"{command[0]} is unavailable",
        }
    if command[:2] == ["cargo", "miri"] and "not available" in version:
        return {
            "status": "missing",
            "detail": version,
        }
    return {"status": "available", "detail": version}


def _command_version(command: list[str]) -> str:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    output = (result.stdout or result.stderr).strip().splitlines()
    if not output:
        return "unavailable"
    return output[0]


def _missing_llm_key_warning(config: SafeMapConfig) -> str:
    return (
        f"Missing `{config.llm.api_key_env}` for LLM modes "
        f"({config.llm.provider}/{config.llm.model} at {config.llm.base_url})."
    )


def _has_existing_run_artifacts(output: Path) -> bool:
    if not output.exists():
        return False
    if (output / ".safemap" / "runs").exists():
        return True
    return any((child / ".safemap" / "runs").exists() for child in output.iterdir())


def write_artifact_metadata(output_path: Path) -> dict[str, object]:
    metadata = {
        **_artifact_metadata(),
        "tool_versions": _tool_versions(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return metadata


def _combined_summary_rows(
    inputs: list[tuple[str, Path | None, str]],
) -> list[str]:
    rows: list[str] = []
    for dataset, path, note in inputs:
        if path is None:
            continue
        csv_rows = _read_csv_if_exists(path)
        if not csv_rows:
            rows.append(f"| {dataset} | unavailable | 0 | 0 | 0 | 0.000 | 0 | {note} |")
            continue
        for mode in sorted({row.get("mode", "") for row in csv_rows}):
            mode_rows = [row for row in csv_rows if row.get("mode", "") == mode]
            accepted = sum(_int(row.get("fully_safe_accepted_units")) for row in mode_rows)
            eligible = sum(_int(row.get("eligible_units")) for row in mode_rows)
            differential = sum(
                1 for row in mode_rows
                if row.get("safemap_differential_status") == "passed"
            )
            target_total = sum(
                _target_count(row) for row in mode_rows
            )
            target_accepted = sum(
                _target_accepted_count(row) for row in mode_rows
            )
            rate = accepted / eligible if eligible else 0.0
            target_rate = (
                target_accepted / target_total if target_total else 0.0
            )
            rows.append(
                f"| {dataset} | {mode} | {len(mode_rows)} | {accepted} | "
                f"{eligible} | {rate:.3f} | {differential} | "
                f"{target_accepted} | {target_total} | {target_rate:.3f} | "
                f"{note} |"
            )
    return rows


def _read_csv_if_exists(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _validate_baseline_denominator(main_csv: Path, baseline_csv: Path) -> None:
    main_rows = _read_csv_if_exists(main_csv)
    baseline_rows = _read_csv_if_exists(baseline_csv)
    main_total = sum(_int(row.get("eligible_units")) for row in main_rows)
    baseline_total = sum(_int(row.get("eligible_units")) for row in baseline_rows)
    if main_total != baseline_total:
        raise ValueError(
            "C2Rust baseline eligible-unit denominator "
            f"{baseline_total} does not match main benchmark denominator "
            f"{main_total}. Rerun the baseline to recover complete metrics or "
            "set allow_denominator_mismatch=True and document the mismatch."
        )


def _int(value: object) -> int:
    try:
        return int(float(str(value or 0)))
    except ValueError:
        return 0


def _rust_loc(root: Path) -> int:
    return (
        sum(
            len(file.read_text().splitlines())
            for file in root.rglob("*.rs")
            if "target" not in file.relative_to(root).parts
        )
        if root.exists()
        else 0
    )


def _diagnostic_summary(errors: list[dict[str, object]]) -> str:
    parts = []
    for error in errors[:3]:
        location = ""
        if error.get("file"):
            location = str(error["file"])
            if error.get("line"):
                location += f":{error['line']}"
        message = str(error.get("message") or "").strip()
        level = str(error.get("level") or "diagnostic")
        parts.append(f"{level}: {message}" + (f" ({location})" if location else ""))
    return " | ".join(parts)


def _validation_check(validation: dict, name: str) -> dict:
    value = validation.get(name, {}) if validation else {}
    return value if isinstance(value, dict) else {}


def _validation_status_counts(validation: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not validation:
        return counts
    for name in ("compile", "tests", "clippy", "miri", "differential"):
        status = str(_validation_check(validation, name).get("status") or "")
        if status:
            counts[status] = counts.get(status, 0) + 1
    return counts


def _read_json_if_exists(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _idiom_success_counts(store, metrics: dict) -> dict[str, dict[str, int]]:
    accepted = set(metrics.get("fully_safe_accepted_unit_ids", []))
    counts: dict[str, dict[str, int]] = {}
    for plan_path in store.path("plans").glob("*.json"):
        plan = _read_json_if_exists(plan_path)
        if plan.get("status") != "planned":
            continue
        unit_id = plan.get("unit_id")
        pattern_names = {
            pattern.get("pattern") for pattern in plan.get("patterns", [])
        }
        for name in pattern_names:
            if not name or name == "unguided_rewrite":
                continue
            item = counts.setdefault(name, {"planned": 0, "accepted": 0})
            item["planned"] += 1
            if unit_id in accepted:
                item["accepted"] += 1
    return counts


def _primary_target_result(project: Path, store, metrics: dict) -> dict[str, object]:
    metadata = _read_json_if_exists(project / "expected.json")
    primary = metadata.get("primary_function")
    targets = _declared_targets(metadata)
    target_results = [
        _target_function_result(store, metrics, function)
        for function in targets
    ]
    target_accepted = sum(1 for result in target_results if result["accepted"])
    target_outcomes: dict[str, int] = {}
    for result in target_results:
        outcome = str(result["outcome"])
        target_outcomes[outcome] = target_outcomes.get(outcome, 0) + 1
    target_fields = {
        "target_functions": ",".join(targets),
        "target_count": len(targets),
        "target_fully_safe_accepted_units": target_accepted,
        "target_acceptance_rate": target_accepted / len(targets) if targets else "",
        "target_outcomes": json.dumps(target_outcomes, sort_keys=True),
    }
    if not primary:
        return {
            "primary_function": "",
            "primary_expected_eligibility": "",
            "primary_plan_status": "",
            "primary_eligible": "",
            "primary_fully_safe_accepted": "",
            "primary_outcome": "not_declared",
            **target_fields,
        }
    result = _target_function_result(store, metrics, primary)
    if not result["plan"]:
        return {
            "primary_function": primary,
            "primary_expected_eligibility": metadata.get("expected_eligibility", ""),
            "primary_plan_status": "missing",
            "primary_eligible": False,
            "primary_fully_safe_accepted": False,
            "primary_outcome": "missing_plan",
            **target_fields,
        }
    plan = result["plan"]
    return {
        "primary_function": primary,
        "primary_expected_eligibility": metadata.get("expected_eligibility", ""),
        "primary_plan_status": plan.get("status", ""),
        "primary_eligible": result["eligible"],
        "primary_fully_safe_accepted": result["accepted"],
        "primary_outcome": result["outcome"],
        **target_fields,
    }


def _failed_target_result(project: Path) -> dict[str, object]:
    metadata = _read_json_if_exists(project / "expected.json")
    primary = metadata.get("primary_function")
    targets = _declared_targets(metadata)
    target_outcomes = {"failed": len(targets)} if targets else {}
    return {
        "primary_function": primary or "",
        "primary_expected_eligibility": metadata.get("expected_eligibility", "")
        if primary else "",
        "primary_plan_status": "",
        "primary_eligible": "",
        "primary_fully_safe_accepted": False if primary else "",
        "primary_outcome": "failed" if primary else "not_declared",
        "target_functions": ",".join(targets),
        "target_count": len(targets),
        "target_fully_safe_accepted_units": 0,
        "target_acceptance_rate": 0.0 if targets else "",
        "target_outcomes": json.dumps(target_outcomes, sort_keys=True),
    }


def _declared_targets(metadata: dict) -> list[str]:
    primary = metadata.get("primary_function")
    if primary:
        return [str(primary)]
    expected_functions = metadata.get("expected_functions")
    if isinstance(expected_functions, dict):
        return sorted(str(name) for name in expected_functions)
    return []


def _target_function_result(store, metrics: dict, function: str) -> dict[str, object]:
    plan = _plan_for_function(store, function)
    if not plan:
        return {
            "plan": None,
            "accepted": False,
            "eligible": False,
            "outcome": "missing_plan",
        }
    accepted = plan.get("unit_id") in set(metrics.get("fully_safe_accepted_unit_ids", []))
    eligible = plan.get("eligibility") in {
        "safe_translatable",
        "safe_translatable_with_api_change",
    }
    if accepted:
        outcome = "accepted"
    elif plan.get("status") != "planned":
        outcome = str(plan.get("eligibility") or "rejected")
    else:
        outcome = "not_accepted"
    return {
        "plan": plan,
        "accepted": accepted,
        "eligible": eligible,
        "outcome": outcome,
    }


def _plan_for_function(store, function: str) -> dict | None:
    for plan_path in store.path("plans").glob("*.json"):
        plan = _read_json_if_exists(plan_path)
        if plan.get("function") == function:
            return plan
    return None


def _selected_modes(names: list[str] | None):
    if not names:
        return BASELINES
    by_name = {mode.name: mode for mode in BASELINES}
    unknown = sorted(set(names) - set(by_name))
    if unknown:
        raise ValueError(f"Unknown benchmark mode(s): {', '.join(unknown)}")
    return tuple(by_name[name] for name in names)


def _row_status(mode: str, metrics: dict, store) -> tuple[str, str]:
    if mode == "c2rust_only":
        return "completed", ""
    if metrics.get("safemap") is None and metrics.get("safemap_compile") is None:
        direct_error = _read_json_if_exists(store.path("logs/direct_llm_error.json"))
        return "no_final_output", direct_error.get("reason", "")
    return "completed", ""


def _mode_summary_rows(rows: list[dict]) -> list[str]:
    by_mode: dict[str, list[dict]] = {}
    for row in rows:
        by_mode.setdefault(row.get("mode", ""), []).append(row)
    output = []
    for mode, items in sorted(by_mode.items()):
        eligible = sum(_as_int(item.get("eligible_units")) for item in items)
        accepted = sum(_as_int(item.get("fully_safe_accepted_units")) for item in items)
        rate = accepted / eligible if eligible else 0.0
        statuses: dict[str, int] = {}
        for item in items:
            status = item.get("status", "")
            statuses[status] = statuses.get(status, 0) + 1
        status_text = ", ".join(
            f"`{name}`: {count}" for name, count in sorted(statuses.items())
        )
        output.append(
            f"| {mode} | {len(items)} | {status_text} | {accepted} | "
            f"{eligible} | {rate:.3f} |"
        )
    return output


def _primary_summary_rows(rows: list[dict]) -> list[str]:
    by_mode: dict[str, list[dict]] = {}
    for row in rows:
        if _target_count(row):
            by_mode.setdefault(row.get("mode", ""), []).append(row)
    output = []
    for mode, items in sorted(by_mode.items()):
        targets = sum(_target_count(item) for item in items)
        accepted = sum(
            _target_accepted_count(item) for item in items
        )
        outcomes: dict[str, int] = {}
        for item in items:
            for outcome, count in _target_outcomes(item).items():
                outcomes[outcome] = outcomes.get(outcome, 0) + count
        outcome_text = ", ".join(
            f"`{name}`: {count}" for name, count in sorted(outcomes.items())
        )
        rate = accepted / targets if targets else 0.0
        output.append(
            f"| {mode} | {targets} | {accepted} | {rate:.3f} | {outcome_text} |"
        )
    return output


def _idiom_summary_rows(rows: list[dict]) -> list[str]:
    aggregate: dict[tuple[str, str], dict[str, int]] = {}
    for row in rows:
        mode = row.get("mode", "")
        counts = _as_json_dict(row.get("idiom_success_counts"))
        for idiom, values in counts.items():
            key = (mode, idiom)
            item = aggregate.setdefault(key, {"planned": 0, "accepted": 0})
            item["planned"] += _as_int(values.get("planned"))
            item["accepted"] += _as_int(values.get("accepted"))
    output = []
    for (mode, idiom), values in sorted(aggregate.items()):
        planned = values["planned"]
        accepted = values["accepted"]
        rate = accepted / planned if planned else 0.0
        output.append(
            f"| {mode} | {idiom} | {planned} | {accepted} | {rate:.3f} |"
        )
    return output


def _failure_summary_rows(rows: list[dict]) -> list[str]:
    aggregate: dict[tuple[str, str], int] = {}
    for row in rows:
        mode = row.get("mode", "")
        counts = _as_json_dict(row.get("failure_categories"))
        for category, count in counts.items():
            key = (mode, category)
            aggregate[key] = aggregate.get(key, 0) + _as_int(count)
    return [
        f"| {mode} | {category} | {count} |"
        for (mode, category), count in sorted(aggregate.items())
    ]


def _validation_status_summary_rows(rows: list[dict]) -> list[str]:
    aggregate = _validation_status_summary(rows)
    return [
        f"| {mode} | {check} | {status} | {count} |"
        for (mode, check, status), count in sorted(aggregate.items())
    ]


def _validation_status_summary(rows: list[dict]) -> dict[tuple[str, str, str], int]:
    aggregate: dict[tuple[str, str, str], int] = {}
    for row in rows:
        mode = row.get("mode", "")
        per_check = _row_validation_statuses(row)
        if per_check:
            for check, status in per_check.items():
                if status:
                    key = (mode, check, status)
                    aggregate[key] = aggregate.get(key, 0) + 1
            continue
        counts = _as_json_dict(row.get("validation_status_counts"))
        for status, count in counts.items():
            key = (mode, "all", str(status))
            aggregate[key] = aggregate.get(key, 0) + _as_int(count)
    return aggregate


def _row_validation_statuses(row: dict) -> dict[str, str]:
    fields = {
        "cargo_check": "safemap_cargo_check_status",
        "cargo_test": "safemap_cargo_test_status",
        "clippy": "safemap_clippy_status",
        "miri": "miri_status",
        "differential": "safemap_differential_status",
    }
    return {
        check: str(row.get(field) or "")
        for check, field in fields.items()
        if row.get(field)
    }


def _latex_mode_summary(rows: list[dict]) -> str:
    by_mode: dict[str, list[dict]] = {}
    for row in rows:
        by_mode.setdefault(row.get("mode", ""), []).append(row)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Fully safe acceptance by evaluation mode.}",
        "\\label{tab:safemap-mode-summary}",
        "\\begin{tabular}{lrrrr}",
        "\\hline",
        "Mode & Rows & Accepted Units & Eligible Units & Acceptance Rate \\\\",
        "\\hline",
    ]
    for mode, items in sorted(by_mode.items()):
        eligible = sum(_as_int(item.get("eligible_units")) for item in items)
        accepted = sum(_as_int(item.get("fully_safe_accepted_units")) for item in items)
        rate = accepted / eligible if eligible else 0.0
        lines.append(
            f"{_latex_escape(mode)} & {len(items)} & {accepted} & "
            f"{eligible} & {rate:.3f} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    return "\n".join(lines)


def _latex_target_summary(rows: list[dict]) -> str:
    by_mode: dict[str, list[dict]] = {}
    for row in rows:
        if _target_count(row):
            by_mode.setdefault(row.get("mode", ""), []).append(row)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Declared target-function acceptance by evaluation mode.}",
        "\\label{tab:safemap-target-summary}",
        "\\begin{tabular}{lrrr}",
        "\\hline",
        "Mode & Target Functions & Accepted Targets & Acceptance Rate \\\\",
        "\\hline",
    ]
    for mode, items in sorted(by_mode.items()):
        targets = sum(_target_count(item) for item in items)
        accepted = sum(_target_accepted_count(item) for item in items)
        rate = accepted / targets if targets else 0.0
        lines.append(
            f"{_latex_escape(mode)} & {targets} & {accepted} & {rate:.3f} \\\\"
        )
    lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    return "\n".join(lines)


def _latex_failure_summary(rows: list[dict]) -> str:
    aggregate: dict[tuple[str, str], int] = {}
    for row in rows:
        mode = row.get("mode", "")
        counts = _as_json_dict(row.get("failure_categories"))
        for category, count in counts.items():
            key = (mode, category)
            aggregate[key] = aggregate.get(key, 0) + _as_int(count)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{SafeMAP failure categories by evaluation mode.}",
        "\\label{tab:safemap-failure-summary}",
        "\\begin{tabular}{llr}",
        "\\hline",
        "Mode & Category & Count \\\\",
        "\\hline",
    ]
    for (mode, category), count in sorted(aggregate.items()):
        lines.append(
            f"{_latex_escape(mode)} & {_latex_escape(category)} & {count} \\\\"
        )
    if not aggregate:
        lines.append("No failures & none & 0 \\\\")
    lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    return "\n".join(lines)


def _latex_validation_status_summary(rows: list[dict]) -> str:
    aggregate = _validation_status_summary(rows)
    lines = [
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Validation outcomes by evaluation mode and check.}",
        "\\label{tab:safemap-validation-statuses}",
        "\\begin{tabular}{lllr}",
        "\\hline",
        "Mode & Check & Status & Count \\\\",
        "\\hline",
    ]
    for (mode, check, status), count in sorted(aggregate.items()):
        lines.append(
            f"{_latex_escape(mode)} & {_latex_escape(check)} & "
            f"{_latex_escape(status)} & {count} \\\\"
        )
    if not aggregate:
        lines.append("No validation & none & none & 0 \\\\")
    lines.extend(["\\hline", "\\end{tabular}", "\\end{table}"])
    return "\n".join(lines)


def _latex_escape(value: object) -> str:
    text = str(value)
    replacements = {
        "\\": "\\textbackslash{}",
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def _as_json_dict(value) -> dict:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value:
        try:
            loaded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return {}


def _as_int(value) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def _target_count(row: dict) -> int:
    count = _as_int(row.get("target_count"))
    if count:
        return count
    return 1 if row.get("primary_function") else 0


def _target_accepted_count(row: dict) -> int:
    count = _as_int(row.get("target_fully_safe_accepted_units"))
    if count:
        return count
    return 1 if _as_bool(row.get("primary_fully_safe_accepted")) else 0


def _target_outcomes(row: dict) -> dict[str, int]:
    outcomes = _as_json_dict(row.get("target_outcomes"))
    if outcomes:
        return {str(name): _as_int(count) for name, count in outcomes.items()}
    outcome = row.get("primary_outcome")
    return {str(outcome): 1} if outcome else {}


def _as_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes"}
    return bool(value)
