from pathlib import Path

from safemap.analysis.c_analyzer import analyze_c_project
from safemap.analysis.dependency_graph import create_translation_units
from safemap.artifacts import ArtifactStore
from safemap.ingestion.project_loader import ingest_project
from safemap.llm.client import StaticLLMClient
from safemap.models import FunctionInfo, ParameterInfo, PointerFact, StructInfo
from safemap.translation.migration_planner import create_migration_plans
from safemap.translation.safe_synthesizer import detect_synthesis_rule
from safemap.translation.signature_generator import plan_signature, projection_issue
from safemap.translation.unit_synthesis import synthesize_units
from safemap.validation.unit_harness import validate_units

C_SOURCE = """
#include <stddef.h>
struct counter { int count; int step; char *label; };

int clamp_add(int a, int b) {
    int total = a + b;
    if (total > 50) return 50;
    return total;
}

int counter_next(struct counter *c) {
    if (!c) return -1;
    c->count += c->step;
    return c->count;
}

int uses_label(struct counter *c) {
    return c->label != NULL;
}
"""

CORRECT_CLAMP = """pub fn clamp_add(a: i32, b: i32) -> i32 {
    let total = a + b;
    if total > 50 { 50 } else { total }
}"""

# Boundary off-by-one (51 instead of 50): needs constant-mined inputs.
WRONG_CLAMP = """pub fn clamp_add(a: i32, b: i32) -> i32 {
    let total = a + b;
    if total > 51 { 50 } else { total }
}"""

COUNTER_NEXT = """pub fn counter_next(c: Option<&mut counter>) -> Result<i32, i32> {
    match c {
        None => Err(-1),
        Some(c) => { c.count += c.step; Ok(c.count) }
    }
}"""


def _plan(tmp_path: Path, source: str = C_SOURCE):
    project_dir = tmp_path / "proj"
    project_dir.mkdir(parents=True)
    (project_dir / "lib.c").write_text(source, encoding="utf-8")
    store = ArtifactStore.create(tmp_path / "out", "proj")
    project = ingest_project(project_dir, store)
    analysis = analyze_c_project(project)
    units = create_translation_units(analysis)
    plans = create_migration_plans(analysis, units)
    return project, analysis, units, plans, store


def _run(tmp_path: Path, responses: dict[str, str], source: str = C_SOURCE):
    project, analysis, units, plans, store = _plan(tmp_path, source)
    crate = store.path("final/rust")
    outcomes = synthesize_units(
        analysis, units, plans, crate, store,
        project_name="proj", source_files=project.c_files,
        client=StaticLLMClient(responses), max_repair_attempts=0,
    )
    compiled = [item.unit_id for item in outcomes if item.status == "compiled"]
    behavior = validate_units(
        Path(project.c_files[0]), crate, store.path("validation/units"),
        analysis.functions, plans, analysis.structs, compiled, cases=200, seed=3,
    )
    by_function = {item.function: item for item in outcomes}
    return by_function, {item.function: item for item in behavior.values()}, plans


def test_correct_translation_is_accepted_and_wrong_one_rejected(tmp_path: Path) -> None:
    good, good_behavior, _ = _run(tmp_path / "good", {
        "int clamp_add": CORRECT_CLAMP, "int counter_next": COUNTER_NEXT,
    })
    assert good["clamp_add"].status == "compiled"
    assert good_behavior["clamp_add"].status == "passed"
    # Scalar-field projection: the pointer field `label` is never touched.
    assert good_behavior["counter_next"].status == "passed"

    bad, bad_behavior, _ = _run(tmp_path / "bad", {
        "int clamp_add": WRONG_CLAMP, "int counter_next": COUNTER_NEXT,
    })
    assert bad["clamp_add"].status == "compiled"
    assert bad_behavior["clamp_add"].status == "failed"
    assert bad_behavior["clamp_add"].first_mismatch is not None
    # One unit's behavioral failure does not affect the other unit.
    assert bad_behavior["counter_next"].status == "passed"


def test_out_of_bounds_c_read_is_undefined_and_main_is_the_original(tmp_path: Path) -> None:
    source = """
int first(const int *arr, int len) { return arr[0] + len - len; }
int main(void) { return 7; }
"""
    outcomes, behavior, plans = _run(tmp_path, {
        "int first": "pub fn first(arr: &[i32]) -> i32 { arr[0] }",
        "int main": "pub fn main() -> i32 { 7 }",
    }, source)
    assert {plan.function: plan.target_signature for plan in plans}["first"] == "pub fn first(arr: &[i32]) -> i32"
    # Reading arr[0] of an empty slice is UB in C: excluded, not a mismatch.
    assert behavior["first"].status == "passed", behavior["first"].reason
    assert behavior["first"].undefined_cases > 0
    assert behavior["main"].status == "passed", behavior["main"].reason


def test_signature_mismatch_and_unsafe_are_not_admitted(tmp_path: Path) -> None:
    outcomes, _, _ = _run(tmp_path, {
        "int clamp_add": "pub fn clamp_add(a: i64, b: i64) -> i64 { a + b }",
        "int counter_next": "pub fn counter_next(c: Option<&mut counter>) -> Result<i32, i32> { unsafe { Ok(0) } }",
    })
    assert outcomes["clamp_add"].status == "compile_failed"
    assert "Signature mismatch" in outcomes["clamp_add"].reason
    assert outcomes["counter_next"].status == "rejected_policy"


def test_pointer_field_access_blocks_projection(tmp_path: Path) -> None:
    _, _, _, plans, _ = _plan(tmp_path)
    by_function = {plan.function: plan for plan in plans}
    assert by_function["counter_next"].status == "planned"
    assert by_function["counter_next"].target_signature == (
        "pub fn counter_next(c: Option<&mut counter>) -> Result<i32, i32>"
    )
    assert by_function["uses_label"].status == "rejected"
    assert any("non-scalar field `label`" in item for item in by_function["uses_label"].signature_issues)


def test_projection_follows_bare_arguments_into_callees() -> None:
    struct = StructInfo("s", [{"name": "x", "type": "int"}, {"name": "p", "type": "char *"}], "a.c", 1)
    reader = FunctionInfo("read_x", "int", [ParameterInfo("v", "struct s *", True)],
                          "int read_x(struct s *v) { return v->x; }", "a.c", 1, 1)
    leaker = FunctionInfo("read_p", "int", [ParameterInfo("v", "struct s *", True)],
                          "int read_p(struct s *v) { return v->p[0]; }", "a.c", 1, 1)
    caller = FunctionInfo("outer", "int", [ParameterInfo("w", "struct s *", True)],
                          "int outer(struct s *w) { assert(w && \"x\"); if (w) return read_x(w); return 0; }",
                          "a.c", 1, 1)
    bad_caller = FunctionInfo("outer2", "int", [ParameterInfo("w", "struct s *", True)],
                              "int outer2(struct s *w) { return read_p(w); }", "a.c", 1, 1)
    functions = {item.name: item for item in (reader, leaker, caller, bad_caller)}
    assert projection_issue(caller, "w", struct, functions) is None
    assert "read_p" in projection_issue(bad_caller, "w", struct, functions)


def test_planner_rejects_types_it_cannot_map() -> None:
    function = FunctionInfo(
        "copy", "void *",
        [ParameterInfo("dst", "void *", True), ParameterInfo("fp", "FILE *", True)],
        "void *copy(void *dst, FILE *fp) { return dst; }", "a.c", 1, 1,
        pointer_facts=[PointerFact("dst", "void *", "nullable_pointer", "", 0.9)],
    )
    _, issues = plan_signature(function, structs=[])
    assert any("opaque pointee `void`" in item for item in issues)
    assert any("FILE" in item for item in issues)
    assert any(item.startswith("return:") for item in issues)


def test_nullable_rule_requires_exact_shape() -> None:
    function = FunctionInfo(
        "first_or", "int", [ParameterInfo("p", "const int *", True, True)],
        "int first_or(const int *p) { if (p == NULL) return 0; int x = p[1]; return x * 2; }",
        "a.c", 1, 1,
        pointer_facts=[PointerFact("p", "const int *", "nullable_pointer", "", 0.9)],
    )
    from safemap.models import MigrationPlan
    plan = MigrationPlan("unit_0", "pub fn first_or(p: Option<&i32>) -> i32", [], [], [])
    # The old rule emitted `Some(v) => *v` for any nullable-pointer function.
    assert detect_synthesis_rule(function, plan) is None


def test_provider_outage_aborts_instead_of_scoring_failure(tmp_path: Path) -> None:
    import pytest
    from safemap.llm.client import LLMClient, ProviderUnavailable

    class Down(LLMClient):
        def generate(self, prompt, system_prompt=None):
            raise ProviderUnavailable("HTTP 503")

    project, analysis, units, plans, store = _plan(tmp_path)
    with pytest.raises(ProviderUnavailable):
        synthesize_units(
            analysis, units, plans, store.path("final/rust"), store,
            project_name="proj", source_files=project.c_files, client=Down(),
        )
