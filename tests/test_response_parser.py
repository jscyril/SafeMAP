import pytest

from safemap.llm.response_parser import parse_function_response
from safemap.llm.response_parser import reject_forbidden_constructs


def test_accepts_single_fenced_function() -> None:
    result = parse_function_response(
        "```rust\npub fn sum(values: &[i32]) -> i32 { values.iter().sum() }\n```",
        "sum",
    )
    assert result.startswith("pub fn sum")


def test_rejects_prose() -> None:
    with pytest.raises(ValueError, match="exactly one function"):
        parse_function_response("Here it is:\nfn f() {}", "f")


def test_rejects_forbidden_constructs_in_direct_source() -> None:
    with pytest.raises(ValueError, match="placeholder code"):
        reject_forbidden_constructs("pub fn f() { todo!() }")
