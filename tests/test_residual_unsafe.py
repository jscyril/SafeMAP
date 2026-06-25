from pathlib import Path

from safemap.metrics.residual_unsafe import classify_residual_unsafe


def test_classifies_pointer_arithmetic(tmp_path: Path) -> None:
    source = tmp_path / "lib.rs"
    source.write_text(
        "fn item(p: *const i32) -> i32 { unsafe { *p.add(1) } }\n"
    )
    results = classify_residual_unsafe(source)
    assert results[0]["category"] == "pointer_arithmetic"
    assert results[0]["start_line"] == 1

