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
    assert [item.name for item in analysis.functions] == ["helper", "run"]
    assert analysis.functions[1].calls == ["helper"]
    assert analysis.functions[1].pointer_facts[0].usage_kind == "output_parameter"

