from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from safemap.evaluation.eligibility_labels import evaluate_eligibility_labels


FIELDS = [
    "project", "function", "source_file", "start_line", "end_line",
    "reviewer", "label", "construct_tags", "confidence", "rationale",
    "adjudicated_label",
]


def _write_labels(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _label(
    function: str,
    line: int,
    reviewer: str,
    label: str,
    adjudicated: str,
    tags: str = "scalar",
) -> dict[str, object]:
    return {
        "project": "demo",
        "function": function,
        "source_file": "demo.c",
        "start_line": line,
        "end_line": line + 2,
        "reviewer": reviewer,
        "label": label,
        "construct_tags": tags,
        "confidence": "high",
        "rationale": "synthetic test",
        "adjudicated_label": adjudicated,
    }


def _write_decisions(path: Path) -> None:
    path.write_text(json.dumps([
        {
            "project": "demo", "function": "true_positive",
            "source_file": "/source/demo.c", "start_line": 1,
            "candidate_decision": "candidate_safe",
            "analysis_backend": "libclang",
        },
        {
            "project": "demo", "function": "false_positive",
            "source_file": "/source/demo.c", "start_line": 10,
            "candidate_decision": "candidate_safe",
            "analysis_backend": "regex_fallback",
        },
        {
            "project": "demo", "function": "false_negative",
            "source_file": "/source/demo.c", "start_line": 20,
            "candidate_decision": "manual_refactor_required",
            "analysis_backend": "libclang",
        },
        {
            "project": "demo", "function": "unknown",
            "source_file": "/source/demo.c", "start_line": 30,
            "candidate_decision": "unknown",
            "analysis_backend": "libclang",
        },
    ]) + "\n", encoding="utf-8")


def test_evaluator_reports_precision_recall_errors_and_backends(
    tmp_path: Path,
) -> None:
    labels = tmp_path / "labels.csv"
    decisions = tmp_path / "decisions.json"
    rows = []
    cases = [
        ("true_positive", 1, "candidate_safe", "scalar"),
        ("false_positive", 10, "unsafe_required", "pointer,call"),
        ("false_negative", 20, "candidate_safe", "pointer"),
        ("unknown", 30, "unknown", "macro"),
    ]
    for function, line, adjudicated, tags in cases:
        rows.append(_label(
            function, line, "reviewer_a", adjudicated, adjudicated, tags
        ))
        second_label = (
            "manual_refactor_required"
            if function == "false_positive"
            else adjudicated
        )
        rows.append(_label(
            function, line, "reviewer_b", second_label, adjudicated, tags
        ))
    _write_labels(labels, rows)
    _write_decisions(decisions)

    result = evaluate_eligibility_labels(labels, [decisions])

    assert result["functions_labeled"] == 4
    assert result["functions_scored"] == 3
    assert result["eligibility_precision"] == 0.5
    assert result["eligibility_recall"] == 0.5
    assert result["confusion_matrix"] == {
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 1,
        "true_negative": 0,
    }
    assert result["false_positives"][0]["function"] == "false_positive"
    assert result["false_negatives"][0]["function"] == "false_negative"
    assert result["by_analysis_backend"]["regex_fallback"]["functions"] == 1
    assert result["by_construct"]["pointer"]["system_human_disagreements"] == 2
    assert result["reviewer_agreement"]["disagreements_by_construct"] == {
        "call": 1,
        "pointer": 1,
    }


def test_evaluator_requires_two_labels_for_every_function(
    tmp_path: Path,
) -> None:
    labels = tmp_path / "labels.csv"
    decisions = tmp_path / "decisions.json"
    _write_labels(labels, [
        _label("true_positive", 1, "reviewer_a", "candidate_safe",
               "candidate_safe"),
        _label("true_positive", 1, "reviewer_b", "candidate_safe",
               "candidate_safe"),
        _label("false_positive", 10, "reviewer_a", "unsafe_required",
               "unsafe_required"),
    ])
    _write_decisions(decisions)

    with pytest.raises(ValueError, match="Both reviewers"):
        evaluate_eligibility_labels(labels, [decisions])
