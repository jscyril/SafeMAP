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
) -> list[dict]:
    projects = sorted({
        file.parent for file in benchmarks.rglob("*.c")
        if ".safemap" not in file.parts
    })
    rows = []
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    for project in projects:
        for mode in BASELINES:
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
                rows.append({
                    "project": project.name,
                    "mode": mode.name,
                    "loc_c": sum(
                        len(f.read_text().splitlines()) for f in project.rglob("*.c")
                    ),
                    "loc_rust_baseline": _rust_loc(store.path("baseline/rust")),
                    "loc_rust_safemap": _rust_loc(store.path("final/rust")),
                    "c2rust_compile": metrics.get("baseline_compile"),
                    "safemap_compile": metrics.get("safemap_compile"),
                    "c2rust_tests": "",
                    "safemap_tests": metrics.get("test_pass_rate"),
                    "c2rust_unsafe_blocks": baseline.get("unsafe_blocks"),
                    "safemap_unsafe_blocks": final.get("unsafe_blocks"),
                    "c2rust_raw_pointers": baseline.get("raw_pointer_types"),
                    "safemap_raw_pointers": final.get("raw_pointer_types"),
                    "clippy_warnings": "",
                    "miri_status": "",
                    "differential_pass_rate": metrics.get("differential_pass_rate"),
                    "repair_attempts": metrics.get("repair_attempts", 0),
                    "llm_calls": metrics.get("llm_calls", 0),
                    "status": "completed",
                })
            except Exception as error:
                rows.append({
                    "project": project.name, "mode": mode.name,
                    "status": "failed", "reason": str(error),
                })
    columns = [
        "project", "mode", "loc_c", "loc_rust_baseline", "loc_rust_safemap",
        "c2rust_compile", "safemap_compile", "c2rust_tests", "safemap_tests",
        "c2rust_unsafe_blocks", "safemap_unsafe_blocks", "c2rust_raw_pointers",
        "safemap_raw_pointers", "clippy_warnings", "miri_status",
        "differential_pass_rate", "repair_attempts", "llm_calls", "status", "reason",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary = [
        "# SafeMAP Benchmark Summary", "",
        "| Project | Mode | Status |", "|---|---|---|",
    ]
    summary.extend(
        f"| {row['project']} | {row['mode']} | {row['status']} |" for row in rows
    )
    output_csv.with_suffix(".md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    return rows


def _rust_loc(root: Path) -> int:
    return sum(len(file.read_text().splitlines()) for file in root.rglob("*.rs")) if root.exists() else 0
