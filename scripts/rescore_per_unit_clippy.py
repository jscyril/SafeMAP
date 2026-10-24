#!/usr/bin/env python3
"""Amendment 3: re-score the frozen held-out outputs with per-unit Clippy.

For every archived run of the per-unit configurations (guided, deterministic,
one-shot and plain LLM), the saved Rust crate is copied and scored twice with
the current acceptance code: once with crate-level Clippy, which must reproduce
the archived result exactly, and once with `per_unit_clippy` on. No LLM is
called; the generated code is the code recorded in the run. Run directories
are never modified.

It also records why each guided first-run unit was screened out as needing
manual refactoring and how many plans return a pointer into caller-owned data
(refactor_reasons.json), which the result rows do not keep.

Usage: scripts/rescore_per_unit_clippy.py OUT_DIR
"""
from __future__ import annotations

import copy
import csv
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from safemap.analysis.rust_analyzer import analyze_rust_path  # noqa: E402
from safemap.artifacts import ArtifactStore  # noqa: E402
from safemap.config import load_config  # noqa: E402
from safemap.models import (  # noqa: E402
    CAnalysis, EligibilityResult, MigrationPlan, ProjectInfo, RunMetrics,
    TranslationUnit, from_dict,
)
from safemap.pipeline import (  # noqa: E402
    _apply_eligibility_metrics, _direct_unit_acceptance, _score_unit_crate,
)
from safemap.translation.unit_synthesis import UnitOutcome  # noqa: E402
from safemap.validation.validator import validate_project  # noqa: E402

HELDOUT = REPO / "reports/publication/v2/heldout"
STAGES = [
    "v2-llm", "ext/v2-llm", "rep2-orig/v2-llm", "rep2-ext/v2-llm",
    "rep3-orig/v2-llm", "rep3-ext/v2-llm", "v2-non-llm", "ext/v2-non-llm",
    "plain-orig", "plain-ext", "plain-rep2-orig", "plain-rep2-ext",
    "plain-rep3-orig", "plain-rep3-ext",
]
MODES = {"safemap_guided", "safemap_deterministic", "llm_only"}


def score(run: Path, work: Path, mode: str, per_unit: bool) -> RunMetrics:
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(run, work, ignore=shutil.ignore_patterns("target"))
    store = ArtifactStore(work)
    config = copy.deepcopy(CONFIG)
    config.validation.per_unit_clippy = per_unit
    load = lambda rel: json.loads((work / rel).read_text())
    project = from_dict(ProjectInfo, load("project.json"))
    analysis = from_dict(CAnalysis, load("analysis/c_analysis.json"))
    units = [from_dict(TranslationUnit, item) for item in load("analysis/translation_units.json")]
    eligibility = [from_dict(EligibilityResult, item) for item in load("analysis/eligibility.json")]
    final_root = work / "final/rust"
    if mode != "llm_only":
        plans = [from_dict(MigrationPlan, json.loads(p.read_text())) for p in sorted((work / "plans").glob("*.json"))]
        outcomes = [from_dict(UnitOutcome, item) for item in load("synthesis/summary.json")]
        return _score_unit_crate(project, analysis, units, plans, eligibility, store, config,
                                 None, final_root, outcomes)
    metrics = RunMetrics(project=project.project_name, total_units=len(units))
    _apply_eligibility_metrics(metrics, eligibility)
    if (final_root / "Cargo.toml").exists():
        validation = validate_project(final_root, config.validation)
        metrics.safemap = analyze_rust_path(final_root)
        _direct_unit_acceptance(project, analysis, units, store, config, metrics, validation, final_root)
    return metrics


def refactor_reasons(out: Path) -> None:
    counts: dict[str, int] = {}
    for stage in ("v2-llm", "ext/v2-llm"):
        for line in (HELDOUT / stage / "benchmark_results.rows.jsonl").read_text().splitlines():
            row = json.loads(line)["row"]
            if row["mode"] != "safemap_guided":
                continue
            for item in json.loads((Path(row["run_dir"]) / "analysis/eligibility.json").read_text()):
                if item["category"] == "requires_manual_refactor":
                    key = ("global_state" if any("mutable global state" in r for r in item["reasons"])
                           else "unresolved_pointer_ownership")
                    counts[key] = counts.get(key, 0) + 1
            for plan in (Path(row["run_dir"]) / "plans").glob("*.json"):
                issues = json.loads(plan.read_text()).get("signature_issues") or []
                if any("returned pointer aliases caller-owned data" in str(i) for i in issues):
                    counts["returned_alias"] = counts.get("returned_alias", 0) + 1
    (out / "refactor_reasons.json").write_text(json.dumps(counts, indent=2, sort_keys=True) + "\n")


def main() -> None:
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    refactor_reasons(out)
    results = []
    for stage in STAGES:
        for line in (HELDOUT / stage / "benchmark_results.rows.jsonl").read_text().splitlines():
            row = json.loads(line)["row"]
            if row["mode"] not in MODES:
                continue
            run = Path(row["run_dir"])
            work = out / "work" / run.name
            frozen = score(run, work, row["mode"], per_unit=False)
            archived = int(row["fully_safe_accepted_units"])
            if frozen.fully_safe_accepted_units != archived:
                raise SystemExit(f"{run}: re-scored {frozen.fully_safe_accepted_units}, archived {archived}")
            amended = frozen
            if any(status == "crate_validation_failed" for status in frozen.unit_outcomes.values()):
                amended = score(run, work, row["mode"], per_unit=True)
            result = {
                "stage": stage, "mode": row["mode"], "project": frozen.project, "run": run.name,
                "archived_accepted": archived,
                "per_unit_clippy_accepted": amended.fully_safe_accepted_units,
                "accepted_units": sorted(amended.fully_safe_accepted_unit_ids),
                "clippy_rejected_units": sorted(
                    unit for unit, status in amended.unit_outcomes.items() if status == "clippy_failed"),
                "outcomes": dict(sorted(amended.unit_outcomes.items())),
            }
            results.append(result)
            print(f"{stage:18} {row['mode']:22} {frozen.project:12} {archived:3} -> {result['per_unit_clippy_accepted']}",
                  flush=True)
            shutil.rmtree(work)
    (out / "rescore.json").write_text(json.dumps(results, indent=2) + "\n")
    with (out / "rescore.csv").open("w", newline="") as handle:
        fields = ["stage", "mode", "project", "run", "archived_accepted", "per_unit_clippy_accepted"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)


CONFIG = load_config(REPO / "research" / "resubmission_evaluation.yaml")

if __name__ == "__main__":
    main()
