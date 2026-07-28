#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.evaluation.corpus_characterization import write_characterization


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Export per-project and per-function C corpus distributions."
        )
    )
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()
    result = write_characterization(
        args.corpus_root,
        args.output_json,
        args.output_csv,
    )
    print(
        f"Wrote {result['function_count']} functions from "
        f"{result['project_count']} projects"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
