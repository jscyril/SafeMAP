#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "research/reviewer_materials/review_form_template.html"
CODEBOOK = REPO_ROOT / "research/reviewer_materials/REVIEWER_CODEBOOK.md"
HANDOFF = REPO_ROOT / "research/reviewer_materials/REVIEWER_HANDOFF.md"
CONSENT = REPO_ROOT / "research/reviewer_materials/REVIEWER_CONSENT_AND_SCREENING.md"
PACKET_FILES = (CODEBOOK, HANDOFF, CONSENT)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_source(path: Path, corpus_root: Path) -> Path:
    resolved = path.resolve()
    try:
        return resolved.relative_to(corpus_root.resolve())
    except ValueError as error:
        raise ValueError(
            f"Characterization source is outside the pinned corpus: {resolved}"
        ) from error


def _source_excerpt(path: Path, start: int, end: int) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if start < 1 or end < start or end > len(lines):
        raise ValueError(
            f"Invalid source range {path}:{start}-{end} (file has {len(lines)} lines)"
        )
    return "\n".join(
        f"{number:5d}  {lines[number - 1]}"
        for number in range(start, end + 1)
    )


def build_packet(
    corpus_root: Path,
    characterization_path: Path,
    output: Path,
) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError(f"Refusing to replace existing reviewer packet: {output}")
    characterization = json.loads(
        characterization_path.read_text(encoding="utf-8")
    )
    functions = characterization.get("functions")
    if not isinstance(functions, list) or not functions:
        raise ValueError("Characterization contains no function inventory")

    stage = output.with_name(output.name + ".tmp")
    if stage.exists():
        raise FileExistsError(f"Temporary reviewer-packet path already exists: {stage}")
    stage.mkdir(parents=True)
    try:
        copied: list[dict[str, str]] = []
        for source in PACKET_FILES:
            destination = stage / source.name
            shutil.copy2(source, destination)
            copied.append({"path": destination.name, "sha256": _sha256(destination)})

        sources_destination = stage / "sources"
        shutil.copytree(corpus_root, sources_destination)
        source_files = sorted(path for path in sources_destination.rglob("*") if path.is_file())
        copied.extend(
            {
                "path": str(path.relative_to(stage)),
                "sha256": _sha256(path),
            }
            for path in source_files
        )

        form_functions = []
        for item in functions:
            if not isinstance(item, dict):
                raise ValueError("Characterization function inventory contains a non-object")
            source = Path(str(item["source_file"]))
            relative = _relative_source(source, corpus_root)
            start = int(item["start_line"])
            end = int(item["end_line"])
            form_functions.append({
                "project": str(item["project"]),
                "function": str(item["function"]),
                "source_file": str(relative),
                "start_line": start,
                "end_line": end,
                "packet_source_path": str(Path("sources") / relative),
                "source_excerpt": _source_excerpt(source, start, end),
            })

        inventory = {
            "schema_version": "safemap.reviewer_packet.v1",
            "packet_id": "conference-heldout-eligibility-v1",
            "generated_at_utc": datetime.now(timezone.utc)
            .replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "outcome_blind": True,
            "function_count": len(form_functions),
            "codebook_sha256": _sha256(CODEBOOK),
            "characterization_sha256": _sha256(characterization_path),
            "functions": form_functions,
        }
        inventory_path = stage / "function_inventory.json"
        inventory_path.write_text(
            json.dumps(inventory, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        inventory["packet_sha256"] = _sha256(inventory_path)
        inventory_path.write_text(
            json.dumps(inventory, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        template = TEMPLATE.read_text(encoding="utf-8")
        html = template.replace(
            "__PACKET_JSON__",
            json.dumps(inventory, ensure_ascii=True).replace("</", "<\\/"),
        )
        if "__PACKET_JSON__" in html:
            raise AssertionError("Reviewer form template placeholder was not replaced")
        form_path = stage / "review.html"
        form_path.write_text(html, encoding="utf-8")
        copied.extend([
            {"path": inventory_path.name, "sha256": _sha256(inventory_path)},
            {"path": form_path.name, "sha256": _sha256(form_path)},
        ])
        manifest = {
            **{key: inventory[key] for key in (
                "schema_version", "packet_id", "generated_at_utc",
                "outcome_blind", "function_count", "packet_sha256",
                "codebook_sha256", "characterization_sha256",
            )},
            "files": sorted(copied, key=lambda item: item["path"]),
            "prohibited_content": [
                "SafeMAP decisions", "migration plans", "generated Rust",
                "validation outcomes", "baseline outcomes", "aggregate outcomes",
            ],
        }
        manifest_path = stage / "packet_manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        stage.replace(output)
        return manifest
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build an outcome-blind local-browser eligibility review packet."
    )
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--characterization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_packet(
        args.corpus_root.resolve(),
        args.characterization.resolve(),
        args.output.resolve(),
    )
    print(
        f"built outcome-blind packet with {manifest['function_count']} functions "
        f"at {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
