from safemap.models import DetectedIdiom, FunctionInfo, ParameterInfo, PointerFact
from safemap.translation.signature_generator import generate_signature


def test_generates_slice_result_signature() -> None:
    function = FunctionInfo(
        "get_max", "int",
        [
            ParameterInfo("arr", "const int *", True, True),
            ParameterInfo("len", "int"),
            ParameterInfo("out", "int *", True),
        ],
        "", "x.c", 1, 1,
        pointer_facts=[
            PointerFact("arr", "const int *", "pointer_length_array", "", 0.9),
            PointerFact("out", "int *", "output_parameter", "", 0.9),
        ],
        idioms=[DetectedIdiom(
            "error_code_return", "x.c:1", ["out"], "Result", 0.9, ""
        )],
    )
    assert generate_signature(function) == (
        "pub fn get_max(arr: &[i32]) -> Result<i32, i32>"
    )


def test_void_write_stays_mutable_borrow() -> None:
    function = FunctionInfo(
        "increment", "void", [ParameterInfo("value", "int *", True)],
        "", "x.c", 1, 1,
        pointer_facts=[
            PointerFact("value", "int *", "output_parameter", "", 0.9),
        ],
    )
    assert generate_signature(function) == "pub fn increment(value: &mut i32) -> ()"


def test_manual_allocation_returns_box() -> None:
    function = FunctionInfo(
        "make_value", "int *", [ParameterInfo("value", "int")],
        "", "x.c", 1, 1,
        idioms=[DetectedIdiom(
            "manual_allocation", "x.c:1", [], "Box", 0.9, ""
        )],
    )
    assert generate_signature(function) == "pub fn make_value(value: i32) -> Box<i32>"


def test_nullable_sentinel_returns_result() -> None:
    function = FunctionInfo(
        "read_value", "int", [ParameterInfo("value", "const int *", True, True)],
        "", "x.c", 1, 1,
        pointer_facts=[
            PointerFact("value", "const int *", "nullable_pointer", "", 0.9),
        ],
        idioms=[DetectedIdiom(
            "error_code_return", "x.c:1", [], "Result", 0.9, ""
        )],
    )
    assert generate_signature(function) == (
        "pub fn read_value(value: Option<&i32>) -> Result<i32, i32>"
    )
