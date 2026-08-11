from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from scripts.build_eligibility_reviewer_packet import build_packet
from scripts.merge_eligibility_reviews import merge_reviews


def test_reviewer_packet_contains_source_but_no_outcomes(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    project = corpus / "projects" / "demo"
    project.mkdir(parents=True)
    source = project / "demo.c"
    source.write_text("int add(int a, int b) {\n  return a + b;\n}\n", encoding="utf-8")
    (project / "LICENSE").write_text("test license\n", encoding="utf-8")
    characterization = tmp_path / "characterization.json"
    characterization.write_text(json.dumps({"functions": [{
        "project": "demo", "function": "add", "source_file": str(source),
        "start_line": 1, "end_line": 3,
    }]}), encoding="utf-8")
    output = tmp_path / "packet"

    manifest = build_packet(corpus, characterization, output)

    assert manifest["outcome_blind"] is True
    assert manifest["function_count"] == 1
    html = (output / "review.html").read_text(encoding="utf-8")
    assert "return a + b" in html
    assert "candidate_safe" in html
    assert "generated Rust" in html
    assert not (output / "function_decisions.json").exists()
    assert (output / "sources/projects/demo/LICENSE").is_file()


REVIEW_FIELDS = [
    "project", "function", "source_file", "start_line", "end_line",
    "reviewer", "packet_sha256", "codebook_sha256", "label",
    "construct_tags", "confidence", "rationale", "external_sources",
]


def _write_review(path: Path, reviewer: str, label: str) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerow({
            "project": "demo", "function": "add", "source_file": "demo.c",
            "start_line": 1, "end_line": 3, "reviewer": reviewer,
            "packet_sha256": "packet-hash", "codebook_sha256": "codebook-hash",
            "label": label, "construct_tags": "array_or_slice", "confidence": 4,
            "rationale": "The function has a direct local representation in safe Rust "
                         "and no ownership, aliasing, foreign-call, or lifetime obstacle.",
            "external_sources": "none",
        })


def test_merge_reviews_requires_adjudication_for_disagreement(tmp_path: Path) -> None:
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    _write_review(first, "reviewer_a", "candidate_safe")
    _write_review(second, "reviewer_b", "manual_refactor_required")
    disagreements = tmp_path / "disagreements.csv"

    result = merge_reviews([first, second], disagreements)

    assert result["disagreement_count"] == 1
    rows = list(csv.DictReader(disagreements.open(encoding="utf-8")))
    assert rows[0]["reviewer_a_label"] == "candidate_safe"
    assert rows[0]["reviewer_b_label"] == "manual_refactor_required"


def test_merge_reviews_rejects_same_reviewer(tmp_path: Path) -> None:
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    _write_review(first, "same", "candidate_safe")
    _write_review(second, "same", "candidate_safe")

    with pytest.raises(ValueError, match="distinct reviewer"):
        merge_reviews([first, second], tmp_path / "disagreements.csv")


def test_merge_reviews_rejects_different_packet_hashes(tmp_path: Path) -> None:
    first = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    _write_review(first, "reviewer_a", "candidate_safe")
    _write_review(second, "reviewer_b", "candidate_safe")
    text = second.read_text(encoding="utf-8").replace(
        "packet-hash", "different-packet-hash"
    )
    second.write_text(text, encoding="utf-8")

    with pytest.raises(ValueError, match="different packets"):
        merge_reviews([first, second], tmp_path / "disagreements.csv")
