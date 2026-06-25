from safemap.analysis.idiom_detector import detect_idioms
from safemap.models import FunctionInfo, ParameterInfo, PointerFact


def test_detects_error_code_output_parameter() -> None:
    function = FunctionInfo(
        "parse", "int", [ParameterInfo("out", "int *", True)], "*out = 4; return 0;",
        "parse.c", 1, 1,
        pointer_facts=[PointerFact("out", "int *", "output_parameter", "write", 0.9)],
    )
    kinds = {item.idiom_type for item in detect_idioms(function)}
    assert {"output_parameter", "error_code_return"} <= kinds

