from safemap.metrics.report_generator import generate_markdown
from safemap.models import RunMetrics, RustMetrics


def test_report_contains_comparison_and_failures() -> None:
    report = generate_markdown(RunMetrics(
        project="demo",
        baseline=RustMetrics(unsafe_blocks=2, raw_pointer_types=3),
        safemap=RustMetrics(unsafe_blocks=1, raw_pointer_types=0),
        failed_units=[{"unit_id": "unit_1", "reason": "compile failure"}],
    ))
    assert "| Unsafe blocks | 2 | 1 | 50.00% |" in report
    assert "`unit_1`: compile failure" in report

