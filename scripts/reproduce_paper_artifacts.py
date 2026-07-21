from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.benchmarks.benchmark_runner import write_artifact_metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate SafeMAP paper-facing evaluation artifacts."
    )
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument(
        "--llm-csv",
        default="reports/gemini_benchmark_results.csv",
        help="Optional LLM subset CSV to include when the file exists.",
    )
    parser.add_argument(
        "--strict-denominators",
        action="store_true",
        help="Fail combined evaluation when C2Rust and SafeMAP denominators differ.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without running them.",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir)
    llm_csv = Path(args.llm_csv)
    commands = [
        [
            sys.executable,
            "-m",
            "safemap.cli",
            "final-eval",
            "--benchmarks",
            "examples",
            "--output",
            str(reports_dir / "final"),
            "--mode",
            "safemap_full",
        ],
        [
            sys.executable,
            "-m",
            "safemap.cli",
            "final-eval",
            "--benchmarks",
            "case_studies",
            "--output",
            str(reports_dir / "case-studies"),
            "--mode",
            "safemap_full",
        ],
        [
            sys.executable,
            "-m",
            "safemap.cli",
            "final-eval",
            "--benchmarks",
            "examples",
            "--output",
            str(reports_dir / "c2rust-only"),
            "--mode",
            "c2rust_only",
        ],
    ]
    combined = [
        sys.executable,
        "-m",
        "safemap.cli",
        "combined-eval",
        "--output",
        str(reports_dir / "combined_evaluation.md"),
        "--main-csv",
        str(reports_dir / "final" / "benchmark_results.csv"),
        "--case-study-csv",
        str(reports_dir / "case-studies" / "benchmark_results.csv"),
        "--c2rust-csv",
        str(reports_dir / "c2rust-only" / "benchmark_results.csv"),
    ]
    if llm_csv.exists():
        combined.extend(["--llm-smoke-csv", str(llm_csv)])
    if not args.strict_denominators:
        combined.append("--allow-denominator-mismatch")
    commands.append(combined)

    command_lines = []
    for command in commands:
        command_lines.append(" ".join(command))
        print("+", " ".join(command), flush=True)
        if not args.dry_run:
            subprocess.run(command, check=True)

    metadata_path = reports_dir / "artifact_metadata.json"
    metadata = {} if args.dry_run else write_artifact_metadata(metadata_path)
    manifest = {
        "command_lines": command_lines,
        "reports_dir": str(reports_dir),
        "artifacts": {
            "safemap_microbenchmarks": str(
                reports_dir / "final" / "benchmark_results.csv"
            ),
            "case_studies": str(
                reports_dir / "case-studies" / "benchmark_results.csv"
            ),
            "c2rust_baseline": str(
                reports_dir / "c2rust-only" / "benchmark_results.csv"
            ),
            "combined_evaluation": str(reports_dir / "combined_evaluation.md"),
            "artifact_metadata": str(metadata_path),
        },
        "strict_denominators": args.strict_denominators,
        "llm_csv_included": llm_csv.exists(),
        "metadata": metadata,
    }
    manifest_path = reports_dir / "reproduction_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(f"reproduction manifest: {manifest_path}")


if __name__ == "__main__":
    main()
