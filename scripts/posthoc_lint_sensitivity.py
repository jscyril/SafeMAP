#!/usr/bin/env python3
"""Post-hoc sensitivity check (not part of the frozen protocol).

Re-scores one finished safemap_guided run with a single Clippy lint allowed,
using the frozen crate checks and per-unit differential harness unchanged.
The run directory is never modified; work happens in a copy.

Usage: scripts/posthoc_lint_sensitivity.py RUN_DIR LINT OUT_DIR
  e.g. ... .safemap/runs/<tinyexpr run> clippy::approx_constant /tmp/out
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from safemap.config import load_config  # noqa: E402
from safemap.models import CAnalysis, MigrationPlan, from_dict  # noqa: E402
from safemap.validation.unit_harness import validate_units  # noqa: E402
from safemap.validation.validator import validate_project  # noqa: E402


def main() -> None:
    run, lint, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    config = load_config(REPO / "research" / "resubmission_evaluation.yaml")
    project = json.loads((run / "project.json").read_text())
    analysis = from_dict(CAnalysis, json.loads((run / "analysis/c_analysis.json").read_text()))
    plans = [from_dict(MigrationPlan, json.loads(p.read_text())) for p in sorted((run / "plans").glob("*.json"))]
    compiled = [u["unit_id"] for u in json.loads((run / "synthesis/summary.json").read_text())
                if u["status"] == "compiled"]

    crate = out / "rust"
    shutil.copytree(run / "final/rust", crate, ignore=shutil.ignore_patterns("target"), dirs_exist_ok=True)
    lib = crate / "src/lib.rs"
    lib.write_text(f"#![allow({lint})]\n" + lib.read_text())

    validation = validate_project(crate, config.validation)
    crate_ok = validation.compile.status == "passed" and validation.clippy.status in {"passed", "skipped"}
    behaviors = validate_units(
        Path(project["c_files"][0]), crate, out / "units", analysis.functions, plans,
        analysis.structs, compiled, cases=config.validation.differential_test_inputs,
        seed=config.validation.seed,
    ) if crate_ok else {}
    result = {
        "run": str(run), "allowed_lint": lint, "compiled_units": len(compiled),
        "compile": validation.compile.status, "clippy": validation.clippy.status,
        "unit_status": {k: v.status for k, v in behaviors.items()},
        "passed": sum(v.status == "passed" for v in behaviors.values()),
    }
    (out / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("compiled_units", "compile", "clippy", "passed")}))


if __name__ == "__main__":
    main()
