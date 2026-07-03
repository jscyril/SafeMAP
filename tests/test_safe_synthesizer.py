from pathlib import Path

from safemap.analysis.c_analyzer import _analyze_fallback
from safemap.analysis.dependency_graph import create_translation_units
from safemap.models import (
    DetectedIdiom,
    FunctionInfo,
    MigrationPlan,
    ParameterInfo,
    PatternMigration,
    PointerFact,
    ProjectInfo,
)
from safemap.process import run_command
from safemap.translation.migration_planner import create_migration_plans
from safemap.translation.safe_synthesizer import synthesize_safe_crate


def test_synthesizes_slice_sum_crate(tmp_path: Path) -> None:
    function = FunctionInfo(
        "sum_array", "int",
        [ParameterInfo("arr", "const int *", True, True), ParameterInfo("len", "int")],
        "int sum = 0; for (int i = 0; i < len; i++) sum += arr[i]; return sum;",
        "main.c", 1, 3,
        pointer_facts=[
            PointerFact("arr", "const int *", "pointer_length_array", "indexed", 0.9),
        ],
        idioms=[
            DetectedIdiom("pointer_length_array", "main.c:1", ["arr"], "&[T]", 0.9, ""),
        ],
    )
    plan = MigrationPlan(
        unit_id="unit_0",
        function="sum_array",
        target_signature="pub fn sum_array(arr: &[i32]) -> i32",
        patterns=[PatternMigration("pointer_length_array", "arr,len", "&[i32]", 0.9)],
        constraints=[],
        validation_requirements=[],
        status="planned",
    )

    generated = synthesize_safe_crate(
        ProjectInfo(project_name="demo"),
        [function],
        [plan],
        tmp_path,
    )

    assert generated == ["unit_0"]
    source = (tmp_path / "src" / "lib.rs").read_text(encoding="utf-8")
    assert "#![forbid(unsafe_code)]" in source
    assert "arr.iter().copied().sum()" in source


def test_synthesizes_simple_sum_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_sum", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn simple_sum(a: i32, b: i32) -> i32" in source
    assert "a + b" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_boolean_int_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("boolean_int", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn is_even(value: i32) -> bool" in source
    assert "value % 2 == 0" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_mutable_buffer_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("mutable_buffer", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn increment_all(arr: &mut [i32]) -> ()" in source
    assert "for value in arr.iter_mut()" in source
    assert "*value += 1;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_multiple_outputs_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("multiple_outputs", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn divmod_pair(value: i32, divisor: i32) -> (i32, i32)" in source
    assert "(value / divisor, value % divisor)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_simple_pointer_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_pointer", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn increment(value: &mut i32) -> ()" in source
    assert "*value += 1;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_string_length_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("string_length", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn string_length(text: &str) -> i32" in source
    assert "text.len() as i32" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_malloc_free_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("malloc_free", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn make_value(x: i32) -> Box<i32>" in source
    assert "Box::new(x)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def _synthesize_example(name: str, output: Path) -> tuple[list[str], str]:
    example = Path("examples") / name
    project = ProjectInfo(project_name=name, c_files=[str(example / "main.c")])
    analysis = _analyze_fallback(project)
    plans = create_migration_plans(analysis, create_translation_units(analysis))
    generated = synthesize_safe_crate(project, analysis.functions, plans, output)
    source = (output / "src" / "lib.rs").read_text(encoding="utf-8")
    return generated, source
