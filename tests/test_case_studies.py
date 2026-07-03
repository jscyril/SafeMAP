import json
from pathlib import Path

from safemap.analysis.c_analyzer import _analyze_fallback
from safemap.analysis.dependency_graph import create_translation_units
from safemap.analysis.eligibility import classify_analysis
from safemap.models import ProjectInfo
from safemap.translation.migration_planner import create_migration_plans


CASE_STUDIES = Path("case_studies")


def test_case_study_metadata_matches_analysis_and_plans() -> None:
    for case_study in sorted(CASE_STUDIES.iterdir()):
        if not case_study.is_dir():
            continue
        metadata = json.loads(
            (case_study / "expected.json").read_text(encoding="utf-8")
        )
        analysis = _analyze_fallback(ProjectInfo(c_files=[str(case_study / "main.c")]))
        units = create_translation_units(analysis)
        eligibility = classify_analysis(analysis)
        plans = create_migration_plans(analysis, units)

        for function, expected in metadata["expected_functions"].items():
            result = _by_function(eligibility, function)
            plan = _by_function(plans, function)

            assert result.category == expected["expected_eligibility"], function
            assert plan.status == expected["expected_plan_status"], function
            assert sorted(pattern.pattern for pattern in plan.patterns) == sorted(
                expected.get("expected_patterns", [])
            ), function


def _by_function(items, function: str):
    for item in items:
        if item.function == function:
            return item
    raise AssertionError(f"{function} not found in {[item.function for item in items]}")
