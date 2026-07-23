from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


CORPUS_ROOT = Path("external_corpus/llvm_test_suite_misc")
EXTERNAL_ARTIFACTS = (
    "benchmark_results.csv",
    "benchmark_results.md",
    "paper_tables.md",
    "paper_tables.tex",
    "manifest.json",
)


def _default_work_dir() -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path("reports/.reproduction") / f"external-{timestamp}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def publish_external_snapshot(source: Path, destination: Path) -> list[dict[str, str]]:
    missing = [name for name in EXTERNAL_ARTIFACTS if not (source / name).is_file()]
    if missing:
        raise FileNotFoundError(
            "Cannot publish incomplete external artifact set: " + ", ".join(missing)
        )
    allowed = {Path(name) for name in EXTERNAL_ARTIFACTS}
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
        raise FileExistsError(
            "External artifact directory contains unexpected files: "
            + ", ".join(str(path) for path in unexpected)
        )

    published = []
    for name in EXTERNAL_ARTIFACTS:
        source_path = source / name
        destination_path = destination / name
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination_path.with_name(destination_path.name + ".tmp")
        shutil.copy2(source_path, temporary)
        temporary.replace(destination_path)
        published.append({
            "path": str(destination_path),
            "sha256": _sha256(destination_path),
        })
    return published


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reproduce the pinned SafeMAP external-corpus evaluation."
    )
    parser.add_argument("--reports-dir", type=Path)
    parser.add_argument(
        "--snapshot-dir", type=Path, default=Path("reports/external-corpus")
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    reports_dir = args.reports_dir or _default_work_dir()
    if reports_dir.exists() and any(reports_dir.iterdir()):
        parser.error(f"working directory is not empty: {reports_dir}")
    corpus_manifest = CORPUS_ROOT / "manifest.json"
    if not corpus_manifest.is_file():
        parser.error(
            f"external corpus is missing: {corpus_manifest}; run "
            "scripts/prepare_external_corpus.py first"
        )

    command = [
        sys.executable,
        "-m",
        "safemap.cli",
        "final-eval",
        "--benchmarks",
        str(CORPUS_ROOT / "projects"),
        "--output",
        str(reports_dir),
        "--mode",
        "safemap_deterministic",
    ]
    print("+", " ".join(command), flush=True)
    if args.dry_run:
        print(f"external snapshot: {args.snapshot_dir} (dry run; not written)")
        return

    subprocess.run(command, check=True)
    published = publish_external_snapshot(reports_dir, args.snapshot_dir)
    reproduction_manifest = {
        "command_line": " ".join(command),
        "corpus_manifest": str(corpus_manifest),
        "corpus_manifest_sha256": _sha256(corpus_manifest),
        "published_artifacts": published,
        "snapshot_dir": str(args.snapshot_dir),
        "working_reports_dir": str(reports_dir),
    }
    destination_manifest = args.snapshot_dir / "reproduction_manifest.json"
    destination_manifest.write_text(
        json.dumps(reproduction_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"external snapshot: {args.snapshot_dir}")


if __name__ == "__main__":
    main()
