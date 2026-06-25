from safemap.analysis.pointer_classifier import classify_pointers
from safemap.models import ParameterInfo


def test_classifies_pointer_length_and_output() -> None:
    params = [
        ParameterInfo("arr", "const int *", True, True),
        ParameterInfo("len", "int"),
        ParameterInfo("out", "int *", True, False),
    ]
    facts = classify_pointers(
        params,
        "for (int i=0; i<len; i++) total += arr[i]; *out = total;",
    )
    assert {(item.variable, item.usage_kind) for item in facts} == {
        ("arr", "pointer_length_array"),
        ("out", "output_parameter"),
    }


def test_classifies_nullable_pointer() -> None:
    facts = classify_pointers(
        [ParameterInfo("p", "int *", True, False)],
        "if (p == NULL) return -1; return *p;",
    )
    assert facts[0].usage_kind == "nullable_pointer"

