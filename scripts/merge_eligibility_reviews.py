#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from safemap.evaluation.eligibility_labels import HUMAN_LABELS


REVIEW_REQUIRED = {
    "project", "function", "source_file", "start_line", "end_line",
    "reviewer", "packet_sha256", "codebook_sha256", "label",
    "construct_tags", "confidence", "rationale", "external_sources",
}
FINAL_FIELDS = [
    "project", "function", "source_file", "start_line", "end_line",
    "reviewer", "packet_sha256", "codebook_sha256", "label",
    "construct_tags", "confidence", "rationale", "external_sources",
    "adjudicated_label",
]
ADJUDICATION_FIELDS = [
    "project", "function", "source_file", "start_line", "end_line",
    "reviewer_a_label", "reviewer_b_label", "adjudicated_label",
    "adjudication_rationale", "adjudicator",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _key(row: dict[str, Any]) -> tuple[str, str, str, int, int]:
    return (
        str(row["project"]).strip(),
        str(row["function"]).strip(),
        str(Path(str(row["source_file"]))),
        int(row["start_line"]),
        int(row["end_line"]),
    )


def _read_review(
    path: Path,
) -> tuple[
    str,
    str,
    str,
    dict[tuple[str, str, str, int, int], dict[str, str]],
]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError(f"Review contains no function rows: {path}")
    missing = REVIEW_REQUIRED - set(rows[0])
    if missing:
        raise ValueError(f"Review {path} is missing columns: {', '.join(sorted(missing))}")
    reviewers = {row["reviewer"].strip() for row in rows if row["reviewer"].strip()}
    if len(reviewers) != 1:
        raise ValueError(f"Review {path} must contain exactly one reviewer ID")
    reviewer = next(iter(reviewers))
    packet_hashes = {row["packet_sha256"].strip() for row in rows}
    codebook_hashes = {row["codebook_sha256"].strip() for row in rows}
    if len(packet_hashes) != 1 or not next(iter(packet_hashes)):
        raise ValueError(f"Review {path} must contain one non-empty packet hash")
    if len(codebook_hashes) != 1 or not next(iter(codebook_hashes)):
        raise ValueError(f"Review {path} must contain one non-empty codebook hash")
    indexed: dict[tuple[str, str, str, int, int], dict[str, str]] = {}
    for number, row in enumerate(rows, start=2):
        key = _key(row)
        if key in indexed:
            raise ValueError(f"Review {path} duplicates function {key}")
        if row["label"] not in HUMAN_LABELS:
            raise ValueError(f"Review {path} row {number} has invalid label {row['label']!r}")
        if row["confidence"].strip() not in {"1", "2", "3", "4", "5"}:
            raise ValueError(f"Review {path} row {number} has confidence outside 1-5")
        if len(row["rationale"].strip()) < 80:
            raise ValueError(f"Review {path} row {number} has a rationale shorter than 80 characters")
        if not row["construct_tags"].strip():
            raise ValueError(f"Review {path} row {number} has no material construct tag")
        indexed[key] = row
    return reviewer, next(iter(packet_hashes)), next(iter(codebook_hashes)), indexed


def _write_adjudication_template(
    path: Path,
    left_id: str,
    right_id: str,
    left: dict[tuple[str, str, str, int, int], dict[str, str]],
    right: dict[tuple[str, str, str, int, int], dict[str, str]],
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    disagreements = [key for key in sorted(left) if left[key]["label"] != right[key]["label"]]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ADJUDICATION_FIELDS)
        writer.writeheader()
        for key in disagreements:
            row = left[key]
            writer.writerow({
                "project": key[0], "function": key[1], "source_file": key[2],
                "start_line": key[3], "end_line": key[4],
                "reviewer_a_label": left[key]["label"],
                "reviewer_b_label": right[key]["label"],
                "adjudicated_label": "", "adjudication_rationale": "",
                "adjudicator": "",
            })
    return len(disagreements)


def _read_adjudication(
    path: Path,
) -> dict[tuple[str, str, str, int, int], dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return {}
    missing = set(ADJUDICATION_FIELDS) - set(rows[0])
    if missing:
        raise ValueError(f"Adjudication is missing columns: {', '.join(sorted(missing))}")
    indexed = {}
    for number, row in enumerate(rows, start=2):
        key = _key(row)
        if key in indexed:
            raise ValueError(f"Adjudication duplicates function {key}")
        if row["adjudicated_label"] not in HUMAN_LABELS:
            raise ValueError(f"Adjudication row {number} has invalid final label")
        if len(row["adjudication_rationale"].strip()) < 40:
            raise ValueError(f"Adjudication row {number} needs a rationale of at least 40 characters")
        if not row["adjudicator"].strip():
            raise ValueError(f"Adjudication row {number} has no adjudicator")
        indexed[key] = row
    return indexed


def merge_reviews(
    review_paths: list[Path],
    disagreement_path: Path,
    output_path: Path | None = None,
    adjudication_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    if len(review_paths) != 2:
        raise ValueError("Exactly two independent review files are required")
    first_id, first_packet, first_codebook, first = _read_review(review_paths[0])
    second_id, second_packet, second_codebook, second = _read_review(review_paths[1])
    if first_id == second_id:
        raise ValueError("The two review files must use distinct reviewer IDs")
    if first_packet != second_packet:
        raise ValueError("The two reviews were exported from different packets")
    if first_codebook != second_codebook:
        raise ValueError("The two reviews used different codebook versions")
    if set(first) != set(second):
        missing_first = sorted(set(second) - set(first))
        missing_second = sorted(set(first) - set(second))
        raise ValueError(
            "Review inventories differ; missing from first="
            f"{missing_first[:3]}, missing from second={missing_second[:3]}"
        )
    disagreement_count = _write_adjudication_template(
        disagreement_path, first_id, second_id, first, second
    )
    agreement_count = len(first) - disagreement_count

    result: dict[str, Any] = {
        "schema_version": "safemap.review_merge.v1",
        "reviewers": [first_id, second_id],
        "packet_sha256": first_packet,
        "codebook_sha256": first_codebook,
        "review_files": [
            {"path": str(path), "sha256": _sha256(path)} for path in review_paths
        ],
        "functions_double_labeled": len(first),
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "raw_agreement": agreement_count / len(first),
        "disagreement_template": str(disagreement_path),
        "status": "awaiting_adjudication",
    }
    if output_path is not None:
        adjudication = _read_adjudication(adjudication_path) if adjudication_path else {}
        disagreement_keys = {
            key for key in first if first[key]["label"] != second[key]["label"]
        }
        if set(adjudication) != disagreement_keys:
            raise ValueError(
                "Adjudication must contain every disagreement and no agreement rows"
            )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=FINAL_FIELDS)
            writer.writeheader()
            for key in sorted(first):
                final_label = (
                    adjudication[key]["adjudicated_label"]
                    if key in disagreement_keys else first[key]["label"]
                )
                for source in (first[key], second[key]):
                    writer.writerow({
                        field: source.get(field, "") for field in FINAL_FIELDS
                    } | {"source_file": key[2], "adjudicated_label": final_label})
        result.update({
            "status": "complete",
            "adjudication_file": str(adjudication_path) if adjudication_path else "",
            "adjudication_sha256": _sha256(adjudication_path) if adjudication_path else "",
            "combined_labels_file": str(output_path),
            "combined_labels_sha256": _sha256(output_path),
        })
    if manifest_path:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate, compare, adjudicate, and merge two independent reviews."
    )
    parser.add_argument("--review", action="append", type=Path, required=True)
    parser.add_argument("--disagreements", type=Path, required=True)
    parser.add_argument("--adjudication", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    if bool(args.adjudication) != bool(args.output):
        parser.error("--adjudication and --output must be supplied together")
    result = merge_reviews(
        [path.resolve() for path in args.review],
        args.disagreements.resolve(),
        args.output.resolve() if args.output else None,
        args.adjudication.resolve() if args.adjudication else None,
        args.manifest.resolve() if args.manifest else None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
