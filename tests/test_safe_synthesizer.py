from pathlib import Path

from safemap.models import (
    DetectedIdiom,
    FunctionInfo,
    MigrationPlan,
    ParameterInfo,
    PatternMigration,
    PointerFact,
    ProjectInfo,
)
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
