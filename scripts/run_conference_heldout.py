#!/usr/bin/env python3
"""Run and publish the frozen conference held-out evaluation.

The expensive LLM lane is deliberately separate from deterministic and C2Rust
lanes.  A completed stage is never reused as an output directory, so a quota
failure cannot silently trigger a second model request.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.benchmarks.benchmark_runner import (
    export_latex_tables,
    export_paper_tables,
)


DEFAULT_CONFIG = REPO_ROOT / "research" / "conference_evaluation.yaml"
DEFAULT_FREEZE = REPO_ROOT / "research" / "implementation_freeze.json"
DEFAULT_CORPUS = REPO_ROOT / "external_corpus" / "conference_heldout"
DEFAULT_WORK = REPO_ROOT / "reports" / ".reproduction" / "conference"
DEFAULT_SNAPSHOT = REPO_ROOT / "reports" / "publication" / "conference"

STAGE_MODES = {
    "non-llm": (
        "safemap_deterministic",
        "c2rust_only",
        "safemap_without_pointer_roles",
        "safemap_without_safe_signatures",
        "safemap_without_dependency_grouping",
        "safemap_without_idiom_plans",
        "safemap_without_validation_feedback",
    ),
    "llm": ("llm_only",),
}
DERIVED_FILES = (
    "benchmark_results.csv",
    "benchmark_results.md",
    "paper_tables.md",
    "paper_tables.tex",
    "manifest.json",
)
RUNTIME_OVERRIDES = ("SAFEMAP_MODEL", "SAFEMAP_BASE_URL")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _git_head() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def _load_and_verify_freeze(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing implementation freeze: {path}")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("status") != "frozen":
        raise ValueError("Implementation freeze status must be 'frozen'")
    if record.get("git_commit") != _git_head():
        raise ValueError(
            "Current commit differs from the implementation freeze; do not "
            "run the held-out evaluation on changed code"
        )
    return record


def _verify_inputs(
    freeze_path: Path,
    corpus: Path,
    config: Path,
    stage: str | None = None,
) -> dict[str, Any]:
    record = _load_and_verify_freeze(freeze_path)
    overrides = [name for name in RUNTIME_OVERRIDES if os.getenv(name)]
    if overrides:
        raise ValueError(
            "Unset runtime configuration override(s): " + ", ".join(overrides)
        )
    manifest_path = corpus / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Prepared held-out corpus is missing: {manifest_path}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("freeze_git_commit") != record["git_commit"]:
        raise ValueError("Held-out corpus was prepared for a different freeze")
    frozen_inputs = {
        item["path"]: item["sha256"] for item in record.get("frozen_inputs", [])
    }
    relative_config = str(config.resolve().relative_to(REPO_ROOT))
    expected_config_hash = frozen_inputs.get(relative_config)
    if not expected_config_hash or _sha256(config) != expected_config_hash:
        raise ValueError("Conference configuration does not match the freeze")
    if stage == "llm":
        key_name = _api_key_name(config)
        if not os.getenv(key_name):
            raise ValueError(
                f"{key_name} is not set. Export it in the process environment; "
                "do not place the key in a tracked file."
            )
    return record


def _api_key_name(config: Path) -> str:
    import yaml

    raw = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    return str(raw.get("llm", {}).get("api_key_env", "GEMINI_API_KEY"))


def _command(
    corpus: Path, output: Path, config: Path, modes: tuple[str, ...]
) -> list[str]:
    command = [
        sys.executable, "-m", "safemap.cli", "final-eval",
        "--benchmarks", str(corpus / "projects"),
        "--output", str(output),
        "--config", str(config),
    ]
    for mode in modes:
        command.extend(("--mode", mode))
    return command


def run_stage(
    stage: str,
    work_root: Path,
    corpus: Path,
    config: Path,
    freeze_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    if stage not in STAGE_MODES:
        raise ValueError(f"Unknown stage: {stage}")
    freeze = _verify_inputs(freeze_path, corpus, config, stage)
    output = work_root / stage
    if output.exists():
        raise FileExistsError(
            f"Refusing to reuse held-out stage directory: {output}"
        )
    command = _command(corpus, output, config, STAGE_MODES[stage])
    plan = {
        "schema_version": "safemap.heldout_stage.v1",
        "stage": stage,
        "modes": list(STAGE_MODES[stage]),
        "freeze_git_commit": freeze["git_commit"],
        "corpus_manifest_sha256": _sha256(corpus / "manifest.json"),
        "config_sha256": _sha256(config),
        "command": command,
        "llm_requests_per_project": 1 if stage == "llm" else 0,
        "automatic_retries": 0,
        "output": str(output),
    }
    if dry_run:
        return plan
    output.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    plan.update({
        "started_at_utc": started.replace(microsecond=0).isoformat()
        .replace("+00:00", "Z"),
        "completed_at_utc": datetime.now(timezone.utc).replace(microsecond=0)
        .isoformat().replace("+00:00", "Z"),
        "status": "complete",
    })
    (output / "stage_manifest.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return plan


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def merge_stage_results(stage_dirs: list[Path], output_csv: Path) -> int:
    fields: list[str] | None = None
    rows: list[dict[str, str]] = []
    for stage_dir in stage_dirs:
        path = stage_dir / "benchmark_results.csv"
        if not path.is_file():
            raise FileNotFoundError(f"Stage result is missing: {path}")
        current_fields, current_rows = _read_csv(path)
        if fields is None:
            fields = current_fields
        elif current_fields != fields:
            raise ValueError("Held-out stage CSV schemas differ")
        rows.extend(current_rows)
    if not fields:
        raise ValueError("Held-out stages contain no CSV schema")
    keys = [(row.get("project", ""), row.get("mode", "")) for row in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("Held-out stages duplicate a project/mode result")
    rows.sort(key=lambda row: (row.get("project", ""), row.get("mode", "")))
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def _copy_reproducible_tree(source: Path, destination: Path) -> list[dict[str, Any]]:
    copied: list[dict[str, Any]] = []
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        relative = path.relative_to(source)
        if "target" in relative.parts:
            continue
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied.append({
            "path": str(target.relative_to(destination.parents[1])),
            "sha256": _sha256(target),
            "bytes": target.stat().st_size,
        })
    return copied


def publish_snapshot(
    work_root: Path,
    snapshot: Path,
    corpus: Path,
    config: Path,
    freeze_path: Path,
) -> dict[str, Any]:
    freeze = _verify_inputs(freeze_path, corpus, config)
    if snapshot.exists():
        raise FileExistsError(f"Refusing to replace publication snapshot: {snapshot}")
    stage_dirs = [work_root / name for name in ("non-llm", "llm")]
    for path in stage_dirs:
        stage_manifest = path / "stage_manifest.json"
        if not stage_manifest.is_file():
            raise FileNotFoundError(f"Incomplete held-out stage: {stage_manifest}")
        stage_record = json.loads(stage_manifest.read_text(encoding="utf-8"))
        if stage_record.get("status") != "complete":
            raise ValueError(f"Held-out stage is not complete: {path.name}")
        if stage_record.get("freeze_git_commit") != freeze["git_commit"]:
            raise ValueError(f"Held-out stage used a different freeze: {path.name}")

    temporary = snapshot.with_name(snapshot.name + ".tmp")
    if temporary.exists():
        raise FileExistsError(f"Temporary snapshot path already exists: {temporary}")
    temporary.mkdir(parents=True)
    try:
        result_count = merge_stage_results(
            stage_dirs, temporary / "benchmark_results.csv"
        )
        export_paper_tables(
            temporary / "benchmark_results.csv", temporary / "paper_tables.md"
        )
        export_latex_tables(
            temporary / "benchmark_results.csv", temporary / "paper_tables.tex"
        )
        raw_files: list[dict[str, Any]] = []
        for stage_dir in stage_dirs:
            raw_files.extend(_copy_reproducible_tree(
                stage_dir, temporary / "raw" / stage_dir.name
            ))
        derived = []
        for name in ("benchmark_results.csv", "paper_tables.md", "paper_tables.tex"):
            path = temporary / name
            derived.append({
                "path": name, "sha256": _sha256(path), "bytes": path.stat().st_size,
            })
        manifest = {
            "schema_version": "safemap.heldout_publication.v1",
            "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0)
            .isoformat().replace("+00:00", "Z"),
            "freeze_git_commit": freeze["git_commit"],
            "freeze_record_sha256": _sha256(freeze_path),
            "corpus_manifest_sha256": _sha256(corpus / "manifest.json"),
            "config_sha256": _sha256(config),
            "result_rows": result_count,
            "stages": ["non-llm", "llm"],
            "excluded_build_directories": ["target"],
            "derived_artifacts": derived,
            "preserved_raw_artifacts": raw_files,
        }
        (temporary / "reproduction_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(snapshot)
        return manifest
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run or publish the frozen conference held-out evaluation."
    )
    parser.add_argument("--work-root", type=Path, default=DEFAULT_WORK)
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--freeze-record", type=Path, default=DEFAULT_FREEZE)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--stage", choices=sorted(STAGE_MODES), required=True)
    run_parser.add_argument("--dry-run", action="store_true")
    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    args = parser.parse_args()

    if args.command == "run":
        result = run_stage(
            args.stage, args.work_root.resolve(), args.corpus.resolve(),
            args.config.resolve(), args.freeze_record.resolve(), args.dry_run,
        )
    else:
        result = publish_snapshot(
            args.work_root.resolve(), args.snapshot.resolve(), args.corpus.resolve(),
            args.config.resolve(), args.freeze_record.resolve(),
        )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
