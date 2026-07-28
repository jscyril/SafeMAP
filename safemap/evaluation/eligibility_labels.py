from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HUMAN_LABELS = {
    "candidate_safe",
    "manual_refactor_required",
    "unsafe_required",
    "unknown",
}


def evaluate_eligibility_labels(
    labels_path: Path,
    decision_paths: list[Path],
) -> dict[str, Any]:
    """Compare outcome-blind human labels with frozen SafeMAP decisions."""
    label_rows = _read_labels(labels_path)
    decisions = _read_decisions(decision_paths)
    reviewer_metrics = _reviewer_agreement(label_rows)
    adjudicated = _adjudicated_rows(label_rows)
    matched = _match_decisions(adjudicated, decisions)

    scored = [
        item for item in matched
        if item["adjudicated_label"] != "unknown"
    ]
    unknown = [
        item for item in matched
        if item["adjudicated_label"] == "unknown"
    ]
    tp = sum(
        item["candidate_decision"] == "candidate_safe"
        and item["adjudicated_label"] == "candidate_safe"
        for item in scored
    )
    fp_rows = [
        item for item in scored
        if item["candidate_decision"] == "candidate_safe"
        and item["adjudicated_label"] != "candidate_safe"
    ]
    fn_rows = [
        item for item in scored
        if item["candidate_decision"] != "candidate_safe"
        and item["adjudicated_label"] == "candidate_safe"
    ]
    tn = len(scored) - tp - len(fp_rows) - len(fn_rows)

    return {
        "schema_version": "safemap.eligibility_evaluation.v1",
        "labels_file": str(labels_path),
        "labels_sha256": _sha256(labels_path),
        "decision_files": [
            {"path": str(path), "sha256": _sha256(path)}
            for path in decision_paths
        ],
        "functions_labeled": len(adjudicated),
        "functions_scored": len(scored),
        "adjudicated_unknown": len(unknown),
        "reviewer_agreement": reviewer_metrics,
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": len(fp_rows),
            "false_negative": len(fn_rows),
            "true_negative": tn,
        },
        "eligibility_precision": _ratio(tp, tp + len(fp_rows)),
        "eligibility_recall": _ratio(tp, tp + len(fn_rows)),
        "false_positives": fp_rows,
        "false_negatives": fn_rows,
        "unknown_cases": unknown,
        "by_construct": _construct_metrics(matched),
        "by_analysis_backend": _backend_metrics(scored),
    }


def write_eligibility_evaluation(
    labels_path: Path,
    decision_paths: list[Path],
    output_path: Path,
) -> dict[str, Any]:
    result = evaluate_eligibility_labels(labels_path, decision_paths)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result


def _read_labels(path: Path) -> list[dict[str, Any]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Eligibility label file contains no labeled functions")
    required = {
        "project", "function", "source_file", "start_line", "end_line",
        "reviewer", "label", "construct_tags", "confidence", "rationale",
        "adjudicated_label",
    }
    missing = required - set(rows[0])
    if missing:
        raise ValueError(
            "Eligibility label file is missing columns: "
            + ", ".join(sorted(missing))
        )
    for row_number, row in enumerate(rows, start=2):
        if row["label"] not in HUMAN_LABELS:
            raise ValueError(
                f"Row {row_number} has invalid label {row['label']!r}"
            )
        adjudicated = row["adjudicated_label"].strip()
        if adjudicated and adjudicated not in HUMAN_LABELS:
            raise ValueError(
                f"Row {row_number} has invalid adjudicated label "
                f"{adjudicated!r}"
            )
        if not row["reviewer"].strip():
            raise ValueError(f"Row {row_number} has no reviewer")
        try:
            row["start_line"] = int(row["start_line"])
            row["end_line"] = int(row["end_line"])
        except ValueError as error:
            raise ValueError(
                f"Row {row_number} has non-integer source lines"
            ) from error
        row["construct_tags"] = sorted({
            tag.strip()
            for tag in row["construct_tags"].replace(";", ",").split(",")
            if tag.strip()
        })
    return rows


def _read_decisions(paths: list[Path]) -> list[dict[str, Any]]:
    if not paths:
        raise ValueError("At least one function_decisions.json file is required")
    decisions: list[dict[str, Any]] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"{path} does not contain a decision list")
        for decision in payload:
            if not isinstance(decision, dict):
                raise ValueError(f"{path} contains a non-object decision")
            decisions.append(decision)
    return decisions


def _function_key(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return (
        str(row.get("project", "")),
        str(row.get("function", "")),
        Path(str(row.get("source_file", ""))).name,
        int(row.get("start_line", 0)),
    )


def _reviewer_agreement(rows: list[dict[str, Any]]) -> dict[str, Any]:
    reviewers = sorted({row["reviewer"] for row in rows})
    if len(reviewers) != 2:
        raise ValueError(
            "Conference eligibility evaluation requires exactly two named "
            f"reviewers; found {len(reviewers)}"
        )
    by_function: dict[tuple[str, str, str, int], dict[str, str]] = defaultdict(dict)
    construct_tags: dict[tuple[str, str, str, int], set[str]] = defaultdict(set)
    for row in rows:
        key = _function_key(row)
        if row["reviewer"] in by_function[key]:
            raise ValueError(
                f"Duplicate label by {row['reviewer']} for {_format_key(key)}"
            )
        by_function[key][row["reviewer"]] = row["label"]
        construct_tags[key].update(row["construct_tags"])
    incomplete = [
        _format_key(key)
        for key, labels in by_function.items()
        if set(labels) != set(reviewers)
    ]
    if incomplete:
        raise ValueError(
            "Both reviewers must label every function; incomplete: "
            + ", ".join(incomplete)
        )

    pairs = [
        (labels[reviewers[0]], labels[reviewers[1]])
        for labels in by_function.values()
    ]
    observed = _ratio(sum(left == right for left, right in pairs), len(pairs))
    left_counts = Counter(left for left, _ in pairs)
    right_counts = Counter(right for _, right in pairs)
    expected = sum(
        (left_counts[label] / len(pairs))
        * (right_counts[label] / len(pairs))
        for label in HUMAN_LABELS
    )
    kappa = None
    if observed is not None and expected != 1.0:
        kappa = (observed - expected) / (1.0 - expected)

    disagreements = []
    disagreements_by_construct: Counter[str] = Counter()
    for key, labels in by_function.items():
        if labels[reviewers[0]] == labels[reviewers[1]]:
            continue
        tags = sorted(construct_tags[key]) or ["untagged"]
        disagreements_by_construct.update(tags)
        disagreements.append({
            "project": key[0],
            "function": key[1],
            "source_file": key[2],
            "start_line": key[3],
            reviewers[0]: labels[reviewers[0]],
            reviewers[1]: labels[reviewers[1]],
            "construct_tags": tags,
        })
    return {
        "reviewers": reviewers,
        "functions_double_labeled": len(pairs),
        "raw_agreement": observed,
        "cohen_kappa": kappa,
        "disagreement_count": len(disagreements),
        "disagreements_by_construct": dict(
            sorted(disagreements_by_construct.items())
        ),
        "disagreements": disagreements,
    }


def _adjudicated_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[_function_key(row)].append(row)
    result = []
    for key, items in grouped.items():
        labels = {
            item["adjudicated_label"].strip()
            for item in items
            if item["adjudicated_label"].strip()
        }
        if len(labels) != 1:
            raise ValueError(
                "Exactly one shared adjudicated label is required for "
                f"{_format_key(key)}; found {sorted(labels)}"
            )
        tags = sorted({
            tag for item in items for tag in item["construct_tags"]
        })
        result.append({
            "project": key[0],
            "function": key[1],
            "source_file": key[2],
            "start_line": key[3],
            "end_line": items[0]["end_line"],
            "construct_tags": tags or ["untagged"],
            "adjudicated_label": next(iter(labels)),
        })
    return sorted(
        result,
        key=lambda item: (
            item["project"], item["source_file"],
            item["start_line"], item["function"],
        ),
    )


def _match_decisions(
    labels: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, str, int], list[dict[str, Any]]] = defaultdict(list)
    for decision in decisions:
        by_key[_function_key(decision)].append(decision)
    duplicates = [
        _format_key(key) for key, values in by_key.items() if len(values) > 1
    ]
    if duplicates:
        raise ValueError(
            "Duplicate SafeMAP decisions for: " + ", ".join(duplicates)
        )
    matched = []
    for label in labels:
        key = _function_key(label)
        if key not in by_key:
            raise ValueError(
                f"No SafeMAP decision matches labeled function {_format_key(key)}"
            )
        decision = by_key[key][0]
        matched.append({
            **label,
            "candidate_decision": decision.get(
                "candidate_decision", "unknown"
            ),
            "analysis_backend": decision.get(
                "analysis_backend", "unknown"
            ),
            "candidate_reasons": decision.get("candidate_reasons", []),
        })
    return matched


def _construct_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tagged: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for tag in row["construct_tags"]:
            tagged[tag].append(row)
    result = {}
    for tag, items in sorted(tagged.items()):
        scored = [
            item for item in items
            if item["adjudicated_label"] != "unknown"
        ]
        tp = sum(
            item["candidate_decision"] == "candidate_safe"
            and item["adjudicated_label"] == "candidate_safe"
            for item in scored
        )
        predicted_positive = sum(
            item["candidate_decision"] == "candidate_safe"
            for item in scored
        )
        actual_positive = sum(
            item["adjudicated_label"] == "candidate_safe"
            for item in scored
        )
        result[tag] = {
            "functions": len(items),
            "scored": len(scored),
            "precision": _ratio(tp, predicted_positive),
            "recall": _ratio(tp, actual_positive),
            "system_human_disagreements": sum(
                item["candidate_decision"] != item["adjudicated_label"]
                for item in items
            ),
        }
    return result


def _backend_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["analysis_backend"]].append(row)
    result = {}
    for backend, items in sorted(grouped.items()):
        tp = sum(
            item["candidate_decision"] == "candidate_safe"
            and item["adjudicated_label"] == "candidate_safe"
            for item in items
        )
        fp = sum(
            item["candidate_decision"] == "candidate_safe"
            and item["adjudicated_label"] != "candidate_safe"
            for item in items
        )
        fn = sum(
            item["candidate_decision"] != "candidate_safe"
            and item["adjudicated_label"] == "candidate_safe"
            for item in items
        )
        result[backend] = {
            "functions": len(items),
            "candidate_safe_decisions": tp + fp,
            "precision": _ratio(tp, tp + fp),
            "recall": _ratio(tp, tp + fn),
        }
    return result


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _format_key(key: tuple[str, str, str, int]) -> str:
    return f"{key[0]}:{key[2]}:{key[3]}:{key[1]}"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
