from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from safemap.models import FunctionInfo, MigrationPlan, ParameterInfo
from safemap.validation.differential_tester import validate_c_oracle_sanitizers


pytestmark = pytest.mark.skipif(
    shutil.which("clang") is None,
    reason="clang is required for ASan/UBSan validation",
)


def _plan(function: str) -> MigrationPlan:
    return MigrationPlan(
        unit_id="unit_0",
        target_signature=f"pub fn {function}() -> i32",
        patterns=[],
        constraints=[],
        validation_requirements=[],
        function=function,
        status="planned",
        synthesis_support="implemented_support",
        synthesis_rule="scalar_return",
    )


def test_c_sanitizers_record_clean_oracle_execution(tmp_path: Path) -> None:
    source = tmp_path / "safe.c"
    source.write_text("int identity(int x) { return x; }\n", encoding="utf-8")
    function = FunctionInfo(
        "identity",
        "int",
        [ParameterInfo("x", "int")],
        "int identity(int x) { return x; }",
        str(source),
        1,
        1,
    )
    artifact = tmp_path / "sanitizers.json"

    result = validate_c_oracle_sanitizers(
        source,
        functions=[function],
        plans=[_plan("identity")],
        random_inputs=5,
        seed=7,
        artifact_path=artifact,
    )

    assert result.status == "passed"
    assert result.passed == 1
    assert artifact.is_file()
    assert '"sanitizers": [' in artifact.read_text(encoding="utf-8")


def test_c_sanitizers_reject_undefined_behavior_oracle(tmp_path: Path) -> None:
    source = tmp_path / "undefined.c"
    source.write_text(
        "int overflow(void) { int value = 2147483647; return value + 1; }\n",
        encoding="utf-8",
    )
    function = FunctionInfo(
        "overflow",
        "int",
        [],
        "int overflow(void) { int value = 2147483647; return value + 1; }",
        str(source),
        1,
        1,
    )

    result = validate_c_oracle_sanitizers(
        source,
        functions=[function],
        plans=[_plan("overflow")],
        random_inputs=1,
    )

    assert result.status == "failed"
    assert result.failed == 1
    assert "ASan/UBSan" in (result.reason or "")
