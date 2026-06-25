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
    assert store.path("final/rust/src/main.rs").exists()
