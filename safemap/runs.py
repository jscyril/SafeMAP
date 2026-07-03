from __future__ import annotations

import json
from pathlib import Path


def run_directories(output: Path) -> list[Path]:
    roots = [_runs_root(output)]
    if output.exists():
        roots.extend(
            _runs_root(child) for child in output.iterdir() if child.is_dir()
        )
    runs = [
        path
        for root in roots
        if root.exists()
        for path in root.iterdir()
        if path.is_dir()
    ]
    return sorted(runs)


def latest_run(output: Path) -> Path | None:
    runs = run_directories(output)
    return runs[-1] if runs else None


def summarize_runs(output: Path) -> list[dict[str, object]]:
    summaries = []
    for run in run_directories(output):
        metrics = _read_json(run / "reports" / "metrics.json")
        status = _read_json(run / "run_status.json")
        validation = _read_json(run / "validation" / "results.json")
        differential = validation.get("differential", {}) if validation else {}
        summaries.append({
            "run_dir": str(run),
            "project": metrics.get("project", _project_from_run_name(run)),
            "status": status.get("status", "unknown"),
            "baseline_status": status.get("baseline_status"),
            "total_units": metrics.get("total_units"),
            "eligible_units": metrics.get("eligible_units"),
            "fully_safe_accepted_units": metrics.get("fully_safe_accepted_units"),
            "fully_safe_translation_unit_acceptance_rate": metrics.get(
                "fully_safe_translation_unit_acceptance_rate"
            ),
            "safemap_compile": metrics.get("safemap_compile"),
            "differential_status": differential.get("status"),
        })
    return summaries


def _runs_root(output: Path) -> Path:
    return output / ".safemap" / "runs"


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _project_from_run_name(run: Path) -> str:
    parts = run.name.split("-", 2)
    return parts[1] if len(parts) >= 2 else run.name
