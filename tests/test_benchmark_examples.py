import json
from pathlib import Path

from safemap.analysis.c_analyzer import _analyze_fallback
from safemap.analysis.dependency_graph import create_translation_units
from safemap.analysis.eligibility import classify_analysis
from safemap.models import ProjectInfo
from safemap.translation.migration_planner import create_migration_plans


EXAMPLES = Path("examples")

RECOMMENDED_BENCHMARKS = {
    "simple_sum",
    "simple_subtract",
    "simple_multiply",
    "simple_divide",
    "simple_modulo",
    "boolean_int",
    "boolean_negative",
    "boolean_nonzero",
    "boolean_greater_equal",
    "boolean_less_equal",
    "pointer_length_array",
    "array_max",
    "array_total",
    "mutable_buffer",
    "mutable_buffer_decrement",
    "mutable_buffer_add_two",
    "mutable_buffer_subtract_two",
    "multiple_outputs",
    "min_max_outputs",
    "sum_diff_outputs",
    "output_square",
    "output_double",
    "output_parameter",
    "nullable_pointer",
    "nullable_pointer_zero",
    "error_code",
    "error_code_product",
    "malloc_free",
    "malloc_free_constant",
    "malloc_vec",
    "string_length",
    "string_length_size_t",
    "string_length_long",
    "simple_pointer_double",
    "unsupported_union",
    "unsupported_function_pointer",
    "unsupported_volatile",
    "unsupported_inline_asm",
}


def test_recommended_benchmark_dataset_is_present() -> None:
    existing = {path.name for path in EXAMPLES.iterdir() if path.is_dir()}

    assert RECOMMENDED_BENCHMARKS.issubset(existing)


def test_benchmark_examples_have_expected_metadata() -> None:
    for example in sorted(EXAMPLES.iterdir()):
        if not example.is_dir():
            continue
        expected = example / "expected.json"
        assert expected.exists(), f"{example} is missing expected.json"
        metadata = json.loads(expected.read_text(encoding="utf-8"))
        assert metadata["primary_function"]
        assert metadata["expected_eligibility"]
        assert metadata["expected_plan_status"] in {"planned", "rejected"}
        assert isinstance(metadata.get("expected_patterns", []), list)
        if metadata["expected_eligibility"] != "unsupported":
            assert (example / "expected.rs").exists()


def test_benchmark_expected_eligibility_and_plans_match_analysis() -> None:
    for example in sorted(EXAMPLES.iterdir()):
        if not example.is_dir():
            continue
        metadata = json.loads((example / "expected.json").read_text(encoding="utf-8"))
        analysis = _analyze_fallback(ProjectInfo(c_files=[str(example / "main.c")]))
        units = create_translation_units(analysis)
        eligibility = classify_analysis(analysis)
        plans = create_migration_plans(analysis, units)

        primary = metadata["primary_function"]
        result = _by_function(eligibility, primary)
        plan = _by_function(plans, primary)

        assert result.category == metadata["expected_eligibility"], primary
        assert plan.status == metadata["expected_plan_status"], primary
        assert sorted(pattern.pattern for pattern in plan.patterns) == sorted(
            metadata.get("expected_patterns", [])
        ), primary
        expected_unsupported = sorted(metadata.get("expected_unsupported_features", []))
        if expected_unsupported:
            assert sorted(result.unsupported_features) == expected_unsupported


def _by_function(items, function: str):
    for item in items:
        if item.function == function:
            return item
    raise AssertionError(f"{function} not found in {[item.function for item in items]}")
