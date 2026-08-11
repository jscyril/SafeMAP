from pathlib import Path

from safemap.config import SafeMapConfig
from safemap.llm.client import StaticLLMClient
from safemap.pipeline import run_pipeline


def test_partial_pipeline_records_missing_c2rust(tmp_path: Path) -> None:
    project = tmp_path / "partial"
    project.mkdir()
    (project / "main.c").write_text("int main(void) { return 0; }\n")
    config = SafeMapConfig()
    config.translation.use_llm = False

    store = run_pipeline(project, tmp_path / "results", config)

    assert store.path("analysis/c_analysis.json").exists()
    assert store.path("plans/unit_0.json").exists()
    assert store.read_json("logs/c2rust.json")["status"] in {
        "passed", "failed", "unsupported"
    }
    assert store.path("reports/report.md").exists()


def test_direct_llm_pipeline_compiles_and_compares(tmp_path: Path) -> None:
    project = tmp_path / "direct"
    project.mkdir()
    (project / "main.c").write_text(
        '#include <stdio.h>\nint main(void) { printf("4\\n"); return 0; }\n'
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = True
    config.validation.run_clippy = False
    client = StaticLLMClient(['fn main() { println!("4"); }'])

    store = run_pipeline(project, tmp_path / "results", config, client)
    metrics = store.read_json("reports/metrics.json")

    assert metrics["safemap_compile"] is True
    assert metrics["differential_pass_rate"] == 1.0
    assert metrics["llm_calls"] == 1
    assert store.path("final/rust/src/main.rs").exists()
    call = store.read_json("logs/direct_llm_call.json")
    assert call["baseline"] == "direct_llm_c_to_safe_rust"
    assert call["status"] == "completed"
    assert call["temperature"] == config.llm.temperature
    assert call["response_model"] == "static"
    assert call["retry_index"] == 0
    assert call["response_path"] == "responses/direct_translation.txt"


def test_direct_llm_rejects_forbidden_constructs(tmp_path: Path) -> None:
    project = tmp_path / "unsafe_direct"
    project.mkdir()
    (project / "main.c").write_text(
        "#include <stdlib.h>\n"
        "int main(void) { return abs(0); }\n"
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = True
    client = StaticLLMClient(["unsafe fn main() {}"])

    store = run_pipeline(project, tmp_path / "results", config, client)

    assert store.read_json("logs/direct_llm_error.json")["reason"] == (
        "Response introduces forbidden unsafe Rust"
    )
    assert not store.path("final/rust/Cargo.toml").exists()
    call = store.read_json("logs/direct_llm_call.json")
    assert call["status"] == "rejected"
    assert call["response_path"] == "responses/direct_translation.txt"


def test_pipeline_only_accepts_units_present_in_final_rust(tmp_path: Path) -> None:
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(Path("examples/malloc_free"), tmp_path / "results", config)
    metrics = store.read_json("reports/metrics.json")

    assert metrics["safemap_compile"] is True
    assert metrics["eligible_units"] == 2
    assert metrics["fully_safe_accepted_units"] == 1
    assert metrics["fully_safe_accepted_unit_ids"] == ["unit_0"]


def test_pipeline_runs_library_differential_harness(tmp_path: Path) -> None:
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(Path("examples/simple_sum"), tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "passed"
    assert metrics["differential_pass_rate"] == 1.0


def test_generic_scalar_differential_is_counted_as_passed(
    tmp_path: Path,
) -> None:
    project = tmp_path / "external_shape"
    project.mkdir()
    (project / "main.c").write_text(
        "double sqr(double value) { return value * value; }\n"
        "int main(void) { return (int)sqr(2.0); }\n",
        encoding="utf-8",
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(project, tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "passed"
    assert metrics["fully_safe_accepted_units"] == 1
    assert metrics["differential_pass_units"] == 1
    assert metrics["behaviorally_validated_units"] == 1


def test_behavioral_acceptance_requires_a_passed_c_sanitizer_oracle(
    tmp_path: Path,
) -> None:
    project = tmp_path / "sanitizer_required"
    project.mkdir()
    (project / "main.c").write_text(
        "double sqr(double value) { return value * value; }\n"
        "int main(void) { return (int)sqr(2.0); }\n",
        encoding="utf-8",
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False
    config.validation.run_c_sanitizers = False

    store = run_pipeline(project, tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "passed"
    assert validation["c_sanitizers"]["status"] == "skipped"
    assert metrics["policy_safe_units"] == 1
    assert metrics["behaviorally_validated_units"] == 0
    assert metrics["fully_safe_accepted_units"] == 0


def test_pipeline_matches_llvm_reference_output_with_reviewed_harness(
    tmp_path: Path,
) -> None:
    project = tmp_path / "oracle"
    project.mkdir()
    (project / "oracle.c").write_text(
        '#include <stdio.h>\n'
        "int add(int a, int b) { return a + b; }\n"
        'int main(void) { printf("%d\\n", add(2, 3)); return 0; }\n',
        encoding="utf-8",
    )
    (project / "oracle.reference_output").write_text(
        "5\nexit 0\n",
        encoding="utf-8",
    )
    (project / "oracle.safemap_harness.rs").write_text(
        "#![forbid(unsafe_code)]\n"
        "use safemap_generated::add;\n"
        'fn main() { println!("{}", add(2, 3)); }\n',
        encoding="utf-8",
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(project, tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "passed"
    assert validation["differential"]["reason"] == (
        "Matched LLVM reference output oracle.reference_output"
    )
    assert metrics["fully_safe_accepted_units"] == 1
    assert metrics["differential_pass_units"] == 1


def test_reference_output_allows_generated_function_level_harness(
    tmp_path: Path,
) -> None:
    project = tmp_path / "missing_harness"
    project.mkdir()
    (project / "main.c").write_text(
        "double sqr(double value) { return value * value; }\n"
        "int main(void) { return (int)sqr(2.0); }\n",
        encoding="utf-8",
    )
    (project / "main.reference_output").write_text(
        "exit 4\n",
        encoding="utf-8",
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(project, tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "passed"
    assert metrics["fully_safe_accepted_units"] == 1
    cases = store.read_json("validation/differential_cases.json")
    assert cases["generator"]["functions"] == ["sqr"]


def test_reference_output_mismatch_rejects_generated_unit(
    tmp_path: Path,
) -> None:
    project = tmp_path / "oracle_mismatch"
    project.mkdir()
    (project / "oracle.c").write_text(
        '#include <stdio.h>\n'
        "int add(int a, int b) { return a + b; }\n"
        'int main(void) { printf("%d\\n", add(2, 3)); return 0; }\n',
        encoding="utf-8",
    )
    (project / "oracle.reference_output").write_text(
        "5\nexit 0\n",
        encoding="utf-8",
    )
    (project / "oracle.safemap_harness.rs").write_text(
        "#![forbid(unsafe_code)]\n"
        "use safemap_generated::add;\n"
        'fn main() { println!("{}", add(2, 4)); }\n',
        encoding="utf-8",
    )
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(project, tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    metrics = store.read_json("reports/metrics.json")

    assert validation["differential"]["status"] == "failed"
    assert "stdout differs at line 1" in validation["differential"]["reason"]
    assert metrics["fully_safe_accepted_units"] == 0


def test_pipeline_uses_randomized_library_differential_cases(tmp_path: Path) -> None:
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False
    config.validation.differential_test_inputs = 5

    store = run_pipeline(Path("examples/simple_sum"), tmp_path / "results", config)
    validation = store.read_json("validation/results.json")
    harness = store.path(
        "final/rust/target/safemap-differential-harness/src/main.rs"
    ).read_text(encoding="utf-8")

    assert validation["differential"]["status"] == "passed"
    assert "for _case_index in 0..5" in harness
    cases = store.read_json("validation/differential_cases.json")
    assert cases["seed"] == 0
    assert cases["generator"]["name"] == "lcg32-small-scalars-v1"
    assert cases["generator"]["cases_per_function"] == 5


def test_pipeline_records_function_level_conference_decisions(
    tmp_path: Path,
) -> None:
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = False
    config.validation.run_clippy = False

    store = run_pipeline(Path("examples/simple_sum"), tmp_path / "results", config)
    decisions = store.read_json("analysis/function_decisions.json")

    assert decisions
    decision = next(item for item in decisions if item["function"] == "simple_sum")
    assert decision["project"] == "simple_sum"
    assert decision["source_file"].endswith("main.c")
    assert decision["start_line"] > 0
    assert decision["analysis_backend"] in {"libclang", "regex_fallback"}
    assert decision["candidate_decision"] == "candidate_safe"
    assert decision["synthesis_support"] == "implemented_support"
