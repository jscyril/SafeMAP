from safemap.analysis.eligibility import classify_function
from safemap.models import FunctionInfo, ParameterInfo, PointerFact


def test_classifies_supported_slice_idiom_as_api_change() -> None:
    function = FunctionInfo(
        "sum", "int",
        [ParameterInfo("arr", "const int *", True, True), ParameterInfo("len", "int")],
        "int total = 0; for (int i = 0; i < len; i++) total += arr[i]; return total;",
        "sum.c", 1, 1,
        pointer_facts=[
            PointerFact("arr", "const int *", "pointer_length_array", "indexed", 0.9),
        ],
    )
    function.idioms = []

    result = classify_function(function, "unit_0")

    assert result.category == "safe_translatable"
    assert result.candidate_decision == "candidate_safe"
    assert result.eligible_for_safe_translation is True
    assert result.pointer_roles["arr"] == ["array_pointer"]


def test_rejects_union_as_unsupported() -> None:
    function = FunctionInfo(
        "read_bits", "int", [],
        "union bits { int i; float f; }; return 0;",
        "bits.c", 1, 1,
    )

    result = classify_function(function, "unit_0")

    assert result.category == "unsupported"
    assert result.candidate_decision == "unknown"
    assert "union_usage" in result.unsupported_features
    assert result.eligible_for_safe_translation is False


def test_read_only_indexed_pointers_do_not_create_false_alias_conflict() -> None:
    function = FunctionInfo(
        "dot",
        "double",
        [
            ParameterInfo("left", "float *", True),
            ParameterInfo("right", "float *", True),
            ParameterInfo("length", "long"),
        ],
        (
            "for (long i=0; i<length; i++) "
            "total += left[i] * right[i]; return total;"
        ),
        "dot.c",
        1,
        1,
        pointer_facts=[
            PointerFact(
                "left", "float *", "pointer_length_array", "", 0.9
            ),
            PointerFact(
                "right", "float *", "pointer_length_array", "", 0.9
            ),
        ],
    )

    result = classify_function(function, "unit_0")

    assert result.candidate_decision == "candidate_safe"
