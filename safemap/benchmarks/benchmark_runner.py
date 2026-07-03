from __future__ import annotations

import csv
import copy
import json
from pathlib import Path

from ..config import SafeMapConfig
from ..llm.client import LLMClient
from ..pipeline import run_pipeline
from .baseline_runner import BASELINES


def run_benchmarks(
    benchmarks: Path,
    output_csv: Path,
    config: SafeMapConfig,
    client: LLMClient | None = None,
    modes: list[str] | None = None,
) -> list[dict]:
    selected = _selected_modes(modes)
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
                differential = validation.get("differential", {}) if validation else {}
                miri = validation.get("miri", {}) if validation else {}
                row_status, row_reason = _row_status(mode.name, metrics, store)
                idiom_success_counts = _idiom_success_counts(store, metrics)
                rows.append({
                    "project": project.name,
                    "mode": mode.name,
                    "run_dir": str(store.root),
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
                    "safemap_differential_status": differential.get("status"),
                    "c2rust_unsafe_blocks": baseline.get("unsafe_blocks"),
                    "safemap_unsafe_blocks": final.get("unsafe_blocks"),
                    "c2rust_raw_pointers": baseline.get("raw_pointer_types"),
                    "safemap_raw_pointers": final.get("raw_pointer_types"),
                    "clippy_warnings": "",
                    "miri_status": miri.get("status"),
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
                    "project": project.name, "mode": mode.name,
                    "status": "failed", "reason": str(error),
                })
    columns = [
        "project", "mode", "status", "reason", "run_dir", "loc_c",
        "total_units", "eligible_units", "fully_safe_accepted_units",
        "fully_safe_translation_unit_acceptance_rate", "eligibility_counts",
        "idiom_success_counts", "failure_categories", "loc_rust_baseline",
        "loc_rust_safemap", "c2rust_compile", "safemap_compile", "c2rust_tests",
        "safemap_tests", "safemap_differential_status", "c2rust_unsafe_blocks",
        "safemap_unsafe_blocks", "c2rust_raw_pointers", "safemap_raw_pointers",
        "clippy_warnings", "miri_status", "differential_pass_rate",
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
        "## Idiom Success",
        "",
        "| Mode | Idiom | Planned Units | Accepted Units | Acceptance Rate |",
        "|---|---|---:|---:|---:|",
        *_idiom_summary_rows(rows),
        "",
        "## Project Results",
        "",
        "| Project | Mode | Status | Accepted | Acceptance Rate | Differential |",
        "|---|---|---|---:|---:|---|",
    ]
    summary.extend(
        "| {project} | {mode} | {status} | {accepted} | {rate} | {diff} |".format(
            project=row.get("project", ""),
            mode=row.get("mode", ""),
            status=row.get("status", ""),
            accepted=row.get("fully_safe_accepted_units", ""),
            rate=row.get("fully_safe_translation_unit_acceptance_rate", ""),
            diff=row.get("safemap_differential_status", ""),
        )
        for row in rows
    )
    output_csv.with_suffix(".md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return rows


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
        "## Project Results",
        "",
        "| Project | Mode | Status | Accepted | Acceptance Rate | Differential |",
        "|---|---|---|---:|---:|---|",
    ]
    summary.extend(
        "| {project} | {mode} | {status} | {accepted} | {rate} | {diff} |".format(
            project=row.get("project", ""),
            mode=row.get("mode", ""),
            status=row.get("status", ""),
            accepted=row.get("fully_safe_accepted_units", ""),
            rate=row.get("fully_safe_translation_unit_acceptance_rate", ""),
            diff=row.get("safemap_differential_status", ""),
        )
        for row in rows
    )
    text = "\n".join(summary) + "\n"
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(text, encoding="utf-8")
    return text


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
    export_paper_tables(benchmark_csv, paper_tables)
    manifest = {
        "benchmarks": str(benchmarks),
        "output_dir": str(output_dir),
        "rows": len(rows),
        "modes": sorted({row.get("mode", "") for row in rows}),
        "artifacts": {
            "benchmark_csv": str(benchmark_csv),
            "benchmark_summary": str(benchmark_summary),
            "paper_tables": str(paper_tables),
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


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
