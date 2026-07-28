from pathlib import Path

from safemap.analysis.c_analyzer import _analyze_fallback
from safemap.models import ProjectInfo


def test_fallback_extracts_function_and_calls(tmp_path: Path) -> None:
    source = tmp_path / "sample.c"
    source.write_text(
        "int helper(int x) { return x + 1; }\n"
        "int run(int *out) { *out = helper(2); return 0; }\n"
    )
    analysis = _analyze_fallback(ProjectInfo(c_files=[str(source)]))
    assert analysis.analysis_backend == "regex_fallback"
    assert [item.name for item in analysis.functions] == ["helper", "run"]
    assert analysis.functions[1].calls == ["helper"]
    assert analysis.functions[1].pointer_facts[0].usage_kind == "output_parameter"


def test_fallback_records_fixed_parameter_array_extent(
    tmp_path: Path,
) -> None:
    source = tmp_path / "fixed.c"
    source.write_text(
        "int sum4(const int values[4]) {\n"
        "  int sum = 0;\n"
        "  for (int i = 0; i < 4; ++i) sum += values[i];\n"
        "  return sum;\n"
        "}\n",
        encoding="utf-8",
    )

    analysis = _analyze_fallback(
        ProjectInfo(project_name="fixed", c_files=[str(source)])
    )

    parameter = analysis.functions[0].parameters[0]
    assert parameter.array_length == 4
    assert analysis.functions[0].pointer_facts[0].usage_kind == "fixed_size_array"
