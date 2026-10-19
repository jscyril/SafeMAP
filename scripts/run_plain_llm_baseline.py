#!/usr/bin/env python3
"""Plain one-shot LLM baseline (protocol amendment 2).

Runs the frozen `llm_only` configuration, except that the prompt omits the
planned signatures and struct definitions: the model gets only the C sources
(the frozen code's own no-interface prompt). Scoring is unchanged: functions
are tested through the planned interfaces, so one with another signature is
`interface_mismatch`.

Usage: scripts/run_plain_llm_baseline.py CORPUS_DIR OUTPUT_DIR
Re-running the same command resumes from the checkpoint.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

FREEZE = "62cf430"
REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "research" / "resubmission_evaluation.yaml"
FROZEN_PATHS = ("safemap", "research/resubmission_evaluation.yaml")


def check_frozen() -> None:
    # The evaluated code must be byte-identical to the freeze, committed or not.
    for args in (["diff", "--quiet", FREEZE, "--"], ["diff", "--quiet", "HEAD", "--"]):
        if subprocess.run(["git", *args, *FROZEN_PATHS], cwd=REPO).returncode != 0:
            sys.exit(f"safemap/ or the config differs from freeze {FREEZE}; refusing to run")


def main() -> None:
    corpus, output = (Path(arg).resolve() for arg in sys.argv[1:3])
    check_frozen()
    sys.path.insert(0, str(REPO))
    import safemap.pipeline as pipeline
    from safemap import cli

    original = pipeline._direct_llm_translation

    def without_interfaces(project, final_root, client, store, llm_config, contract=None, structs=None):
        return original(project, final_root, client, store, llm_config, None, None)

    pipeline._direct_llm_translation = without_interfaces
    sys.argv = ["safemap", "final-eval", "--benchmarks", str(corpus / "projects"),
                "--output", str(output), "--config", str(CONFIG), "--mode", "llm_only"]
    cli.main()


if __name__ == "__main__":
    main()
