from pathlib import Path

from safemap.models import (
    FunctionInfo,
    MigrationPlan,
    ParameterInfo,
    PointerFact,
    StructInfo,
)
from safemap.validation.harness_generator import generate_scalar_harness


def test_generates_scalar_harness_from_function_and_plan(tmp_path: Path) -> None:
    source = tmp_path / "main.c"
    source.write_text("int add(int a, int b) { return a + b; }\n")
    function = FunctionInfo(
        "add",
        "int",
        [ParameterInfo("a", "int"), ParameterInfo("b", "int")],
        "int add(int a, int b) { return a + b; }",
        str(source),
        1,
        1,
    )
    plan = MigrationPlan(
        unit_id="unit_0",
        target_signature="pub fn add(a: i32, b: i32) -> i32",
        patterns=[],
        constraints=[],
        validation_requirements=[],
        function="add",
        status="planned",
        synthesis_support="implemented_support",
        synthesis_rule="scalar_return",
    )

    harness = generate_scalar_harness(
        source,
        "generated",
        [function],
        [plan],
        cases=17,
        seed=42,
    )

    assert harness is not None
    assert harness.functions == ("add",)
    assert "for (int case_index = 0; case_index < 17; case_index++)" in harness.c_source
    assert "generated::add(arg_0, arg_1)" in harness.rust_source
    assert harness.seed == 42


def test_does_not_generate_harness_for_unimplemented_function(
    tmp_path: Path,
) -> None:
    source = tmp_path / "main.c"
    source.write_text("int add(int a, int b) { return a + b; }\n")
    function = FunctionInfo(
        "add",
        "int",
        [ParameterInfo("a", "int"), ParameterInfo("b", "int")],
        "int add(int a, int b) { return a + b; }",
        str(source),
        1,
        1,
    )
    plan = MigrationPlan(
        unit_id="unit_0",
        target_signature="pub fn add(a: i32, b: i32) -> i32",
        patterns=[],
        constraints=[],
        validation_requirements=[],
        function="add",
        status="planned",
        synthesis_support="not_implemented",
    )

    assert generate_scalar_harness(
        source,
        "generated",
        [function],
        [plan],
        cases=10,
        seed=0,
    ) is None


def test_generates_two_slice_reduction_harness(tmp_path: Path) -> None:
    source = tmp_path / "dot.c"
    source.write_text(
        "double dot(float *x, float *y, long n) { "
        "double total=0; for(long i=0;i<n;i++) total += x[i]*y[i]; "
        "return total; }\n",
        encoding="utf-8",
    )
    function = FunctionInfo(
        "dot",
        "double",
        [
            ParameterInfo("x", "float *", True),
            ParameterInfo("y", "float *", True),
            ParameterInfo("n", "long"),
        ],
        source.read_text(encoding="utf-8"),
        str(source),
        1,
        1,
        pointer_facts=[
            PointerFact("x", "float *", "pointer_length_array", "", 0.9),
            PointerFact("y", "float *", "pointer_length_array", "", 0.9),
        ],
    )
    plan = MigrationPlan(
        unit_id="unit_0",
        target_signature="pub fn dot(x: &[f32], y: &[f32]) -> f64",
        patterns=[],
        constraints=[],
        validation_requirements=[],
        function="dot",
        status="planned",
        synthesis_support="implemented_support",
        synthesis_rule="slice_dot_product",
    )

    harness = generate_scalar_harness(
        source,
        "generated",
        [function],
        [plan],
        cases=11,
        seed=3,
    )

    assert harness is not None
    assert "float left[8]" in harness.c_source
    assert "generated::dot(&left[..length], &right[..length])" in (
        harness.rust_source
    )


def test_generates_fixed_array_struct_and_entry_harnesses(
    tmp_path: Path,
) -> None:
    source = tmp_path / "composed.c"
    source.write_text(
        "struct Pair { int left; int right; };\n"
        "int sum4(const int values[4]);\n"
        "int pair_total(const struct Pair *pair);\n"
        "int main(void);\n",
        encoding="utf-8",
    )
    functions = [
        FunctionInfo(
            "sum4",
            "int",
            [
                ParameterInfo(
                    "values",
                    "const int *",
                    True,
                    True,
                    4,
                )
            ],
            "return values[0] + values[1] + values[2] + values[3];",
            str(source),
            2,
            2,
        ),
        FunctionInfo(
            "pair_total",
            "int",
            [
                ParameterInfo(
                    "pair",
                    "const struct Pair *",
                    True,
                    True,
                )
            ],
            "return pair->left + pair->right;",
            str(source),
            3,
            3,
        ),
        FunctionInfo(
            "main",
            "int",
            [],
            "return 3;",
            str(source),
            4,
            4,
        ),
    ]
    plans = [
        MigrationPlan(
            unit_id=f"unit_{index}",
            target_signature="",
            patterns=[],
            constraints=[],
            validation_requirements=[],
            function=function.name,
            synthesis_support="implemented_support",
            synthesis_rule=rule,
        )
        for index, (function, rule) in enumerate(zip(
            functions,
            (
                "fixed_array_sum",
                "struct_field_return",
                "internal_call_return",
            ),
            strict=True,
        ))
    ]
    structs = [
        StructInfo(
            "Pair",
            [
                {"name": "left", "type": "int"},
                {"name": "right", "type": "int"},
            ],
            str(source),
            1,
        )
    ]

    harness = generate_scalar_harness(
        source,
        "generated",
        functions,
        plans,
        structs,
        cases=9,
        seed=7,
    )

    assert harness is not None
    assert harness.functions == ("sum4", "pair_total", "main")
    assert "int values[4]" in harness.c_source
    assert "struct Pair value" in harness.c_source
    assert "safemap_original_main()" in harness.c_source
    assert "generated::sum4(&values)" in harness.rust_source
    assert "generated::Pair" in harness.rust_source
    assert "generated::main()" in harness.rust_source
