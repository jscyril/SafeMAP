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


def test_direct_llm_rejects_forbidden_constructs(tmp_path: Path) -> None:
    project = tmp_path / "unsafe_direct"
    project.mkdir()
    (project / "main.c").write_text("int main(void) { return 0; }\n")
    config = SafeMapConfig()
    config.translation.use_c2rust = False
    config.translation.use_llm = True
    client = StaticLLMClient(["unsafe fn main() {}"])

    store = run_pipeline(project, tmp_path / "results", config, client)

    assert store.read_json("logs/direct_llm_error.json")["reason"] == (
        "Response introduces forbidden unsafe Rust"
    )
    assert not store.path("final/rust/Cargo.toml").exists()


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
    assert "for _ in 0..5" in harness
