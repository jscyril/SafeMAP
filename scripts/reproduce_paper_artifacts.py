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
    "c2rust-only/benchmark_results.csv",
    "c2rust-only/benchmark_results.md",
    "c2rust-only/paper_tables.md",
    "c2rust-only/paper_tables.tex",
    "c2rust-only/manifest.json",
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
        "--llm-csv",
        help=(
            "Optional LLM subset CSV to include and copy into the publication "
            "snapshot. Omitted by default."
        ),
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

    reports_dir = Path(args.reports_dir) if args.reports_dir else _default_work_dir()
    snapshot_dir = Path(args.snapshot_dir)
    llm_csv = Path(args.llm_csv) if args.llm_csv else None
    if reports_dir.exists() and any(reports_dir.iterdir()):
        parser.error(
            f"working directory is not empty: {reports_dir}; choose a fresh "
            "--reports-dir to prevent stale artifacts"
        )
    if llm_csv is not None and not llm_csv.is_file():
        parser.error(f"LLM subset CSV does not exist: {llm_csv}")
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
    if llm_csv is not None:
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
    extra_artifacts: tuple[str, ...] = ()
    if not args.dry_run and llm_csv is not None:
        llm_snapshot = reports_dir / "llm-subset" / "benchmark_results.csv"
        llm_snapshot.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(llm_csv, llm_snapshot)
        extra_artifacts = ("llm-subset/benchmark_results.csv",)

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
            "c2rust_baseline": str(
                reports_dir / "c2rust-only" / "benchmark_results.csv"
            ),
            "combined_evaluation": str(reports_dir / "combined_evaluation.md"),
            "artifact_metadata": str(metadata_path),
        },
        "strict_denominators": args.strict_denominators,
        "llm_csv_included": llm_csv is not None,
        "llm_csv_source": str(llm_csv) if llm_csv is not None else None,
        "metadata": metadata,
    }
    manifest_path = reports_dir / "reproduction_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        published = publish_snapshot(
            reports_dir,
            snapshot_dir,
            extra_artifacts=extra_artifacts,
        )
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
