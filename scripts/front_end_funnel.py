#!/usr/bin/env python3
"""Count units through SafeMAP's front end (no LLM, no compilation).

For each project: total units, screened candidates, planned units (a safe
signature exists), and harnessable units (the differential harness can drive
the planned interface). Used to measure v3 front-end changes on development
corpora before any translation run.

    python3 scripts/front_end_funnel.py external_corpus/resubmission_heldout/projects/*
"""
from __future__ import annotations

import collections
import json
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from safemap.analysis.c_analyzer import analyze_c_project
from safemap.analysis.dependency_graph import create_translation_units
from safemap.analysis.eligibility import classify_analysis
from safemap.artifacts import ArtifactStore
from safemap.ingestion.project_loader import ingest_project
from safemap.translation.migration_planner import create_migration_plans
from safemap.translation.signature_generator import projectable_struct_names
from safemap.validation.unit_harness import _spec


def funnel(project_dir: Path) -> dict:
    with tempfile.TemporaryDirectory() as work:
        store = ArtifactStore.create(Path(work), project_dir.name)
        project = ingest_project(project_dir, store)
        analysis = analyze_c_project(project)
    units = create_translation_units(analysis)
    eligibility = classify_analysis(analysis)
    plans = create_migration_plans(analysis, units)
    functions = {item.name: item for item in analysis.functions}
    structs = {item.name: item for item in analysis.structs}
    mappable = projectable_struct_names(analysis.structs)
    reasons = collections.Counter()
    for item in eligibility:
        if not item.eligible_for_safe_translation:
            reasons[re.sub(r":.*", "", item.reasons[0])] += 1
    planned = [plan for plan in plans if plan.status == "planned"]
    for plan in plans:
        if plan.status != "planned" and plan.eligibility in {
            "safe_translatable", "safe_translatable_with_api_change",
        }:
            reasons["planner: " + (plan.reason or "")[:70]] += 1
    harnessable = 0
    for plan in planned:
        spec, reason = _spec(plan, functions[plan.function], structs, mappable)
        if spec is None:
            reasons["harness: " + (reason or "")[:70]] += 1
        else:
            harnessable += 1
    return {
        "project": project_dir.name,
        "backend": analysis.analysis_backend,
        "units": len(units),
        "candidates": sum(item.eligible_for_safe_translation for item in eligibility),
        "planned": len(planned),
        "harnessable": harnessable,
        "reasons": reasons,
    }


def main(paths: list[str]) -> None:
    totals = collections.Counter()
    reasons = collections.Counter()
    print(f"{'project':<16}{'units':>7}{'cand':>7}{'plan':>7}{'harn':>7}")
    for path in paths:
        row = funnel(Path(path))
        print(f"{row['project']:<16}{row['units']:>7}{row['candidates']:>7}"
              f"{row['planned']:>7}{row['harnessable']:>7}  {row['backend']}")
        for key in ("units", "candidates", "planned", "harnessable"):
            totals[key] += row[key]
        reasons.update(row["reasons"])
    print(f"{'TOTAL':<16}{totals['units']:>7}{totals['candidates']:>7}"
          f"{totals['planned']:>7}{totals['harnessable']:>7}")
    print("\nTop refusal reasons:")
    for reason, count in reasons.most_common(20):
        print(f"{count:>5}  {reason}")
    if "--json" in sys.argv:
        print(json.dumps(dict(totals)))


if __name__ == "__main__":
    main([arg for arg in sys.argv[1:] if not arg.startswith("--")])
