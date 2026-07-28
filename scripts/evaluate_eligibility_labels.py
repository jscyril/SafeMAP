#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.evaluation.eligibility_labels import write_eligibility_evaluation


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate two-reviewer held-out eligibility labels against frozen "
            "SafeMAP function decisions."
        )
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=Path("research/heldout_eligibility_labels.csv"),
    )
    parser.add_argument(
        "--decisions",
        type=Path,
        nargs="+",
        required=True,
        help="One function_decisions.json artifact per evaluated project.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("research/results/eligibility_evaluation.json"),
    )
    args = parser.parse_args()
    result = write_eligibility_evaluation(
        args.labels,
        args.decisions,
        args.output,
    )
    print(
        f"Wrote {args.output}: precision={result['eligibility_precision']}, "
        f"recall={result['eligibility_recall']}, "
        f"n={result['functions_scored']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
