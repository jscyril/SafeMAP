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
    assert plan.original_signature == "int sum(const int * arr, int len)"
    assert plan.safety_constraints == [
        "no unsafe code",
        "no raw pointer public API",
        "compile with #![forbid(unsafe_code)]",
    ]
    assert plan.validation["compile"] is True
