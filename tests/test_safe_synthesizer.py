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


def test_synthesizes_simple_multiply_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_multiply", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn multiply(a: i32, b: i32) -> i32" in source
    assert "a * b" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_simple_modulo_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_modulo", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn remainder_value(a: i32, b: i32) -> i32" in source
    assert "a % b" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_boolean_int_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("boolean_int", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn is_even(value: i32) -> bool" in source
    assert "value % 2 == 0" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_boolean_nonzero_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("boolean_nonzero", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn is_nonzero(value: i32) -> bool" in source
    assert "value != 0" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_boolean_greater_equal_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("boolean_greater_equal", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn is_at_least(value: i32, threshold: i32) -> bool" in source
    assert "value >= threshold" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_mutable_buffer_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("mutable_buffer", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn increment_all(arr: &mut [i32]) -> ()" in source
    assert "for value in arr.iter_mut()" in source
    assert "*value += 1;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_array_max_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("array_max", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn array_max(arr: &[i32]) -> i32" in source
    assert "arr.iter().copied().max().unwrap()" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_array_total_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("array_total", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn total_array(arr: &[i32]) -> i32" in source
    assert "arr.iter().copied().sum()" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_mutable_buffer_decrement_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("mutable_buffer_decrement", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn decrement_all(arr: &mut [i32]) -> ()" in source
    assert "*value += -1;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_multiple_outputs_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("multiple_outputs", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn divmod_pair(value: i32, divisor: i32) -> (i32, i32)" in source
    assert "(value / divisor, value % divisor)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_min_max_outputs_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("min_max_outputs", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn min_max_pair(a: i32, b: i32) -> (i32, i32)" in source
    assert "(a.min(b), a.max(b))" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_sum_diff_outputs_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("sum_diff_outputs", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn sum_diff_pair(a: i32, b: i32) -> (i32, i32)" in source
    assert "(a + b, a - b)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_simple_pointer_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_pointer", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn increment(value: &mut i32) -> ()" in source
    assert "*value += 1;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_simple_pointer_decrement_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("simple_pointer_decrement", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn decrement(value: &mut i32) -> ()" in source
    assert "*value -= 2;" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_string_length_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("string_length", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn string_length(text: &str) -> i32" in source
    assert "text.len() as i32" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_string_length_size_t_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("string_length_size_t", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn byte_len(text: &str) -> usize" in source
    assert "text.len()" in source
    assert "as i32" not in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_string_length_long_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("string_length_long", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn string_length_long(text: &str) -> i64" in source
    assert "text.len() as i64" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_nullable_pointer_zero_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("nullable_pointer_zero", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn read_or_zero(p: Option<&i32>) -> i32" in source
    assert "None => 0" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_malloc_free_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("malloc_free", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn make_value(x: i32) -> Box<i32>" in source
    assert "Box::new(x)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_malloc_free_constant_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("malloc_free_constant", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn make_answer() -> Box<i32>" in source
    assert "Box::new(42)" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def test_synthesizes_malloc_vec_example(tmp_path: Path) -> None:
    generated, source = _synthesize_example("malloc_vec", tmp_path)

    assert generated == ["unit_0"]
    assert "pub fn make_sequence(len: i32) -> Vec<i32>" in source
    assert "(0..len).map(|value| value as i32).collect()" in source
    assert run_command(["cargo", "check", "--quiet"], tmp_path).status == "passed"


def _synthesize_example(name: str, output: Path) -> tuple[list[str], str]:
    example = Path("examples") / name
    project = ProjectInfo(project_name=name, c_files=[str(example / "main.c")])
    analysis = _analyze_fallback(project)
    plans = create_migration_plans(analysis, create_translation_units(analysis))
    generated = synthesize_safe_crate(project, analysis.functions, plans, output)
    source = (output / "src" / "lib.rs").read_text(encoding="utf-8")
    return generated, source
