from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.benchmarks.benchmark_runner import write_artifact_metadata


PUBLICATION_ARTIFACTS = (
    "final/benchmark_results.csv",
    "final/benchmark_results.md",
    "final/paper_tables.md",
    "final/paper_tables.tex",
    "final/manifest.json",
    "case-studies/benchmark_results.csv",
    "case-studies/benchmark_results.md",
    "case-studies/paper_tables.md",
    "case-studies/paper_tables.tex",
    "case-studies/manifest.json",
    "external-corpus/benchmark_results.csv",
    "external-corpus/benchmark_results.md",
    "external-corpus/paper_tables.md",
    "external-corpus/paper_tables.tex",
    "external-corpus/manifest.json",
    "c2rust-only/benchmark_results.csv",
    "c2rust-only/benchmark_results.md",
    "c2rust-only/paper_tables.md",
    "c2rust-only/paper_tables.tex",
    "c2rust-only/manifest.json",
    "ablation/benchmark_results.csv",
    "ablation/benchmark_results.md",
    "ablation/paper_tables.md",
    "ablation/paper_tables.tex",
    "ablation/manifest.json",
    "combined_evaluation.md",
    "artifact_metadata.json",
)


def _default_work_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("reports/.reproduction") / timestamp


def publish_snapshot(
    source: Path,
    destination: Path,
    extra_artifacts: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    artifact_names = (*PUBLICATION_ARTIFACTS, *extra_artifacts)
    missing = [name for name in artifact_names if not (source / name).is_file()]
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Cannot publish incomplete artifact set: {joined}")

    allowed = {Path(name) for name in artifact_names}
    allowed.add(Path("reproduction_manifest.json"))
    unexpected = (
        sorted(
            path.relative_to(destination)
            for path in destination.rglob("*")
            if path.is_file() and path.relative_to(destination) not in allowed
        )
        if destination.exists()
        else []
    )
    if unexpected:
        joined = ", ".join(str(path) for path in unexpected)
        raise FileExistsError(
            f"Publication directory contains unexpected files: {joined}"
        )

    published: list[dict[str, str]] = []
    for name in artifact_names:
        source_path = source / name
        destination_path = destination / name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = destination_path.with_name(destination_path.name + ".tmp")
        shutil.copy2(source_path, temporary_path)
        temporary_path.replace(destination_path)
        published.append({
            "path": str(destination_path),
            "sha256": hashlib.sha256(destination_path.read_bytes()).hexdigest(),
        })
    return published


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate SafeMAP paper-facing evaluation artifacts."
    )
    parser.add_argument(
        "--reports-dir",
        help=(
            "Fresh working directory for the long evaluation. Defaults to a "
            "timestamped directory under reports/.reproduction/."
        ),
    )
    parser.add_argument(
        "--snapshot-dir",
        default="reports/publication",
        help="Destination for the clean, paper-facing artifact snapshot.",
    )
    parser.add_argument(
        "--allow-denominator-mismatch",
        action="store_true",
        help=(
            "Publish unequal C2Rust and SafeMAP denominators. This is disabled "
            "by default and should be used only with an explicit explanation."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without running them.",
    )
    args = parser.parse_args()

    reports_dir = Path(args.reports_dir) if args.reports_dir else _default_work_dir()
    snapshot_dir = Path(args.snapshot_dir)
    if reports_dir.exists() and any(reports_dir.iterdir()):
        parser.error(
            f"working directory is not empty: {reports_dir}; choose a fresh "
            "--reports-dir to prevent stale artifacts"
        )
    commands = [
        [
            sys.executable,
            "-m",
            "safemap.cli",
            "final-eval",
            "--benchmarks",
            "external_corpus/llvm_test_suite_misc/projects",
            "--output",
            str(reports_dir / "external-corpus"),
            "--mode",
            "safemap_deterministic",
        ],
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
            "safemap_deterministic",
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
            "safemap_deterministic",
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
        [
            sys.executable,
            "-m",
            "safemap.cli",
            "final-eval",
            "--benchmarks",
            "examples",
            "--output",
            str(reports_dir / "ablation"),
            "--mode",
            "safemap_deterministic",
            "--mode",
            "safemap_without_pointer_roles",
            "--mode",
            "safemap_without_safe_signatures",
            "--mode",
            "safemap_without_dependency_grouping",
            "--mode",
            "safemap_without_idiom_plans",
            "--mode",
            "safemap_without_validation_feedback",
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
        "--external-csv",
        str(reports_dir / "external-corpus" / "benchmark_results.csv"),
        "--c2rust-csv",
        str(reports_dir / "c2rust-only" / "benchmark_results.csv"),
        "--ablation-csv",
        str(reports_dir / "ablation" / "benchmark_results.csv"),
    ]
    if args.allow_denominator_mismatch:
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
        "working_reports_dir": str(reports_dir),
        "snapshot_dir": str(snapshot_dir),
        "artifacts": {
            "safemap_microbenchmarks": str(
                reports_dir / "final" / "benchmark_results.csv"
            ),
            "case_studies": str(
                reports_dir / "case-studies" / "benchmark_results.csv"
            ),
            "external_corpus": str(
                reports_dir / "external-corpus" / "benchmark_results.csv"
            ),
            "c2rust_baseline": str(
                reports_dir / "c2rust-only" / "benchmark_results.csv"
            ),
            "static_guidance_ablation": str(
                reports_dir / "ablation" / "benchmark_results.csv"
            ),
            "combined_evaluation": str(reports_dir / "combined_evaluation.md"),
            "artifact_metadata": str(metadata_path),
        },
        "allow_denominator_mismatch": args.allow_denominator_mismatch,
        "metadata": metadata,
    }
    manifest_path = reports_dir / "reproduction_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        published = publish_snapshot(reports_dir, snapshot_dir)
        snapshot_manifest = snapshot_dir / "reproduction_manifest.json"
        snapshot_manifest.write_text(
            json.dumps(
                {**manifest, "published_artifacts": published},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"publication snapshot: {snapshot_dir}")
    else:
        print(f"publication snapshot: {snapshot_dir} (dry run; not written)")
    print(f"reproduction manifest: {manifest_path}")


if __name__ == "__main__":
    main()
