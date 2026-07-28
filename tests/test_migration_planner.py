from safemap.models import (
    CAnalysis,
    DetectedIdiom,
    FunctionInfo,
    ParameterInfo,
    PointerFact,
    TranslationUnit,
)
from safemap.translation.migration_planner import create_migration_plans


def test_plan_contains_source_of_truth_fields() -> None:
    function = FunctionInfo(
        "sum", "int",
        [ParameterInfo("arr", "const int *", True, True), ParameterInfo("len", "int")],
        "for (int i = 0; i < len; i++) total += arr[i]; return total;",
        "sum.c", 1, 3,
        pointer_facts=[
            PointerFact("arr", "const int *", "pointer_length_array", "indexed", 0.9),
        ],
        idioms=[
            DetectedIdiom(
                "pointer_length_array", "sum.c:1", ["arr"],
                "Use &[T] or &mut [T]", 0.9, "arr is indexed with len",
            ),
        ],
    )
    unit = TranslationUnit("unit_0", "function", "sum", "sum", [], 1.0, "test")

    plan = create_migration_plans(CAnalysis(functions=[function]), [unit])[0]

    assert plan.eligibility == "safe_translatable_with_api_change"
    assert plan.status == "planned"
    assert plan.candidate_decision == "candidate_safe"
    assert plan.synthesis_support == "implemented_support"
    assert plan.synthesis_rule == "slice_sum"
    assert plan.original_signature == "int sum(const int * arr, int len)"
    assert plan.safety_constraints == [
        "no unsafe code",
        "no raw pointer public API",
        "compile with #![forbid(unsafe_code)]",
    ]
    assert plan.validation["compile"] is True


def test_internal_call_support_requires_dependency_grouping() -> None:
    helper = FunctionInfo(
        "square",
        "int",
        [ParameterInfo("value", "int")],
        "return value * value;",
        "calls.c",
        1,
        1,
    )
    caller = FunctionInfo(
        "composed",
        "int",
        [ParameterInfo("value", "int")],
        "return square(value) + 1;",
        "calls.c",
        2,
        2,
        calls=["square"],
    )
    analysis = CAnalysis(functions=[helper, caller])
    grouped = [
        TranslationUnit(
            "unit_0",
            "function",
            "square",
            "square",
            [],
            1.0,
            "dependency-ordered function",
        ),
        TranslationUnit(
            "unit_1",
            "function",
            "composed",
            "composed",
            ["unit_0"],
            1.0,
            "dependency-ordered function",
        ),
    ]
    independent = [
        TranslationUnit(
            unit.unit_id,
            unit.kind,
            unit.c_function,
            unit.rust_function,
            [],
            unit.priority,
            "dependency grouping disabled",
        )
        for unit in grouped
    ]

    grouped_plans = create_migration_plans(analysis, grouped)
    independent_plans = create_migration_plans(
        analysis,
        independent,
    )

    assert grouped_plans[1].synthesis_rule == "internal_call_return"
    assert grouped_plans[1].synthesis_support == "implemented_support"
    assert independent_plans[1].synthesis_rule is None
    assert independent_plans[1].synthesis_support == "not_implemented"
