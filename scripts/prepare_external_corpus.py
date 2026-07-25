from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


UPSTREAM_REPOSITORY = "https://github.com/llvm/llvm-test-suite.git"
UPSTREAM_COMMIT = "6cdc54e005552e3444fa7402cd18a6e4b6db195d"
UPSTREAM_SUBDIR = Path("SingleSource/Benchmarks/Misc")
MAX_SOURCE_LINES = 100
ARCHITECTURE_GATED_SOURCES = {"aarch64-init-cpu-features.c"}
EXPECTED_SELECTION = {
    "dt.c",
    "fp-convert.c",
    "lowercase.c",
    "mandel-2.c",
    "mandel.c",
    "matmul_f64_4x4.c",
    "perlin.c",
    "pi.c",
    "revertBits.c",
    "salsa20.c",
}
VALIDATION_HARNESS_ROOT = (
    Path(__file__).resolve().parents[1] / "external_corpus" / "validation_harnesses"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_count(path: Path) -> int:
    return len(path.read_bytes().splitlines())


def selected_sources(source_dir: Path) -> list[Path]:
    selected = []
    for source in sorted(source_dir.glob("*.c")):
        reference = source.with_suffix(".reference_output")
        if source.name in ARCHITECTURE_GATED_SOURCES:
            continue
        if not reference.is_file():
            continue
        if _line_count(source) <= MAX_SOURCE_LINES:
            selected.append(source)
    return selected


def _verify_checkout(source_tree: Path) -> None:
    if not (source_tree / ".git").exists():
        raise ValueError(
            f"{source_tree} is not a Git checkout; an exact checkout is required "
            "to verify corpus provenance"
        )
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=source_tree,
        check=True,
        capture_output=True,
        text=True,
    )
    actual = result.stdout.strip()
    if actual != UPSTREAM_COMMIT:
        raise ValueError(
            f"LLVM test-suite checkout is at {actual}, expected {UPSTREAM_COMMIT}"
        )
    status = subprocess.run(
        ["git", "status", "--short", "--", str(UPSTREAM_SUBDIR), "LICENSE.TXT"],
        cwd=source_tree,
        check=True,
        capture_output=True,
        text=True,
    )
    if status.stdout.strip():
        raise ValueError("LLVM source checkout has local changes in selected paths")


def prepare_corpus(source_tree: Path, output: Path) -> dict[str, object]:
    source_tree = source_tree.resolve()
    output = output.resolve()
    _verify_checkout(source_tree)
    source_dir = source_tree / UPSTREAM_SUBDIR
    if not source_dir.is_dir():
        raise FileNotFoundError(f"Missing sparse-checkout directory: {source_dir}")

    selected = selected_sources(source_dir)
    selected_names = {path.name for path in selected}
    if selected_names != EXPECTED_SELECTION:
        raise ValueError(
            "Pinned checkout does not match the reviewed selection: "
            f"selected={sorted(selected_names)} expected={sorted(EXPECTED_SELECTION)}"
        )

    excluded = []
    for source in sorted(source_dir.glob("*.c")):
        reference = source.with_suffix(".reference_output")
        if source.name in ARCHITECTURE_GATED_SOURCES:
            reason = "architecture_gated"
        elif not reference.is_file():
            reason = "missing_reference_output"
        elif _line_count(source) > MAX_SOURCE_LINES:
            reason = "over_line_limit"
        else:
            continue
        excluded.append({
            "source": source.name,
            "lines": _line_count(source),
            "reason": reason,
        })

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="safemap-external-corpus-", dir=output.parent
    ) as temporary:
        stage = Path(temporary) / output.name
        projects = stage / "projects"
        licenses = stage / "LICENSES"
        validation_harnesses = stage / "validation_harnesses"
        projects.mkdir(parents=True)
        licenses.mkdir(parents=True)

        root_license = source_tree / "LICENSE.TXT"
        directory_license = source_dir / "LICENSE.TXT"
        shutil.copyfile(root_license, licenses / "LLVM-test-suite-LICENSE.txt")
        shutil.copyfile(directory_license, licenses / "Misc-LICENSE.txt")

        entries = []
        for source in selected:
            project_name = source.stem.replace("-", "_")
            project = projects / project_name
            project.mkdir()
            destination_source = project / source.name
            source_reference = source.with_suffix(".reference_output")
            destination_reference = project / source_reference.name
            shutil.copyfile(source, destination_source)
            shutil.copyfile(source_reference, destination_reference)
            metadata = {
                "license": "NCSA",
                "project": project_name,
                "reference_output": source_reference.name,
                "source": source.name,
                "upstream_commit": UPSTREAM_COMMIT,
                "upstream_path": str(UPSTREAM_SUBDIR / source.name),
            }
            harness = VALIDATION_HARNESS_ROOT / f"{project_name}.rs"
            if harness.is_file():
                validation_harnesses.mkdir(exist_ok=True)
                destination_harness = validation_harnesses / harness.name
                shutil.copyfile(harness, destination_harness)
                metadata.update({
                    "validation_harness": (
                        f"validation_harnesses/{harness.name}"
                    ),
                    "validation_harness_sha256": _sha256(harness),
                })
            (project / "source_metadata.json").write_text(
                json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            entries.append({
                **metadata,
                "lines": _line_count(source),
                "reference_output_sha256": _sha256(source_reference),
                "source_sha256": _sha256(source),
            })

        manifest = {
            "corpus_schema_version": "safemap.external_corpus.v2",
            "license": "NCSA",
            "license_files": [
                "LICENSES/LLVM-test-suite-LICENSE.txt",
                "LICENSES/Misc-LICENSE.txt",
            ],
            "selection": {
                "architecture_gated_sources_excluded": sorted(
                    ARCHITECTURE_GATED_SOURCES
                ),
                "has_matching_default_reference_output": True,
                "maximum_physical_source_lines": MAX_SOURCE_LINES,
                "outcome_blind": True,
                "upstream_scope": str(UPSTREAM_SUBDIR),
            },
            "excluded_sources": excluded,
            "projects": entries,
            "upstream_commit": UPSTREAM_COMMIT,
            "upstream_repository": UPSTREAM_REPOSITORY,
        }
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if output.exists():
            shutil.rmtree(output)
        stage.replace(output)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build SafeMAP's pinned, outcome-blind LLVM external corpus from "
            "an exact upstream Git checkout."
        )
    )
    parser.add_argument(
        "--source-tree",
        required=True,
        type=Path,
        help="LLVM test-suite checkout at the commit pinned in this script.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("external_corpus/llvm_test_suite_misc"),
    )
    args = parser.parse_args()
    manifest = prepare_corpus(args.source_tree, args.output)
    print(
        f"prepared {len(manifest['projects'])} projects at "
        f"{args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
