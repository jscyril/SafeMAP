from safemap.analysis.rust_analyzer import analyze_rust_source
from safemap.metrics.report_generator import percentage_reduction


def test_counts_rust_safety_constructs() -> None:
    metrics = analyze_rust_source(
        "extern \"C\" { fn c(); }\n"
        "unsafe fn f(p: *mut i32) { unsafe { *p = 1; } }\n"
    )
    assert metrics.unsafe_blocks == 1
    assert metrics.unsafe_functions == 1
    assert metrics.raw_pointer_types == 1
    assert metrics.raw_pointer_dereferences == 1
    assert metrics.extern_c_blocks == 1


def test_percentage_reduction_handles_zero() -> None:
    assert percentage_reduction(10, 4) == 60.0
    assert percentage_reduction(0, 0) is None

