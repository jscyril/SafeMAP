from __future__ import annotations

import csv
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from ..analysis.c_analyzer import analyze_c_project
from ..analysis.complexity_metrics import cyclomatic_complexity
from ..models import ProjectInfo


def characterize_corpus(root: Path) -> dict[str, Any]:
    projects = _project_directories(root)
    function_rows: list[dict[str, Any]] = []
    project_rows: list[dict[str, Any]] = []
    for project in projects:
        c_files = sorted(project.rglob("*.c"))
        analysis = analyze_c_project(ProjectInfo(
            project_name=project.name,
            root=str(project.resolve()),
            input_path=str(project.resolve()),
            c_files=[str(path.resolve()) for path in c_files],
        ))
        source_loc = sum(_physical_loc(path) for path in c_files)
        rows = [
            _function_row(project.name, function, analysis.analysis_backend)
            for function in analysis.functions
        ]
        function_rows.extend(rows)
        parameters = sum(row["parameter_count"] for row in rows)
        pointer_parameters = sum(
            row["pointer_parameter_count"] for row in rows
        )
        project_rows.append({
            "project": project.name,
            "source_files": len(c_files),
            "source_loc": source_loc,
            "functions": len(rows),
            "parameters": parameters,
            "pointer_parameters": pointer_parameters,
            "pointer_density": (
                pointer_parameters / parameters if parameters else 0.0
            ),
            "complexity_total": sum(
                row["cyclomatic_complexity"] for row in rows
            ),
            "analysis_backend": analysis.analysis_backend,
            "analysis_backend_reason": analysis.analysis_backend_reason,
        })
    construct_counts = Counter(
        tag
        for row in function_rows
        for tag in row["construct_tags"]
    )
    return {
        "schema_version": "safemap.corpus_characterization.v1",
        "corpus_root": str(root.resolve()),
        "project_count": len(project_rows),
        "source_file_count": sum(
            row["source_files"] for row in project_rows
        ),
        "source_loc": sum(row["source_loc"] for row in project_rows),
        "function_count": len(function_rows),
        "project_distribution": project_rows,
        "function_distributions": {
            "function_loc": _distribution(
                [row["function_loc"] for row in function_rows]
            ),
            "cyclomatic_complexity": _distribution([
                row["cyclomatic_complexity"] for row in function_rows
            ]),
            "parameter_count": _distribution([
                row["parameter_count"] for row in function_rows
            ]),
            "pointer_parameter_count": _distribution([
                row["pointer_parameter_count"] for row in function_rows
            ]),
            "pointer_density": _distribution([
                row["pointer_density"] for row in function_rows
            ]),
        },
        "construct_distribution": dict(sorted(construct_counts.items())),
        "analysis_backend_distribution": dict(sorted(Counter(
            row["analysis_backend"] for row in function_rows
        ).items())),
        "functions": function_rows,
    }


def write_characterization(
    root: Path,
    output_json: Path,
    output_csv: Path,
) -> dict[str, Any]:
    result = characterize_corpus(root)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fields = [
        "project", "function", "source_file", "start_line", "end_line",
        "function_loc", "cyclomatic_complexity", "parameter_count",
        "pointer_parameter_count", "pointer_density", "return_type",
        "construct_tags", "analysis_backend",
    ]
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in result["functions"]:
            writer.writerow({
                **row,
                "construct_tags": ";".join(row["construct_tags"]),
            })
    return result


def _project_directories(root: Path) -> list[Path]:
    project_root = root / "projects" if (root / "projects").is_dir() else root
    projects = sorted({
        path.parent
        for path in project_root.rglob("*.c")
    })
    if not projects:
        raise ValueError(f"No C projects found under {root}")
    return projects


def _function_row(project: str, function, backend: str) -> dict[str, Any]:
    parameter_count = len(function.parameters)
    pointer_count = sum(
        parameter.is_pointer for parameter in function.parameters
    )
    return {
        "project": project,
        "function": function.name,
        "source_file": function.file,
        "start_line": function.start_line,
        "end_line": function.end_line,
        "function_loc": max(1, function.end_line - function.start_line + 1),
        "cyclomatic_complexity": cyclomatic_complexity(function.body),
        "parameter_count": parameter_count,
        "pointer_parameter_count": pointer_count,
        "pointer_density": (
            pointer_count / parameter_count if parameter_count else 0.0
        ),
        "return_type": function.return_type,
        "construct_tags": _construct_tags(function),
        "analysis_backend": backend,
    }


def _construct_tags(function) -> list[str]:
    body = function.body
    tags = set()
    if any(parameter.is_pointer for parameter in function.parameters):
        tags.add("pointer_parameter")
    if re.search(r"\b(?:for|while|do)\b", body):
        tags.add("loop")
    if re.search(r"\[[^\]]*\]", body):
        tags.add("array_access")
    if re.search(r"(?:<<|>>|(?<!&)&(?!&)|(?<!\|)\|(?!\|)|\^|~)", body):
        tags.add("bit_operation")
    if re.search(r"\b(?:float|double|long double)\b", body):
        tags.add("floating_point")
    if re.search(r"\bstruct\b|->|\.[A-Za-z_]\w*", body):
        tags.add("struct_or_field_access")
    if function.calls:
        tags.add("function_call")
    if function.name == "main":
        tags.add("entry_point")
    if re.search(r"\b(?:if|switch|\?)\b", body):
        tags.add("branch")
    return sorted(tags or {"straight_line_scalar"})


def _distribution(values: list[int | float]) -> dict[str, Any]:
    if not values:
        return {
            "count": 0, "minimum": None, "median": None,
            "mean": None, "maximum": None, "values": [],
        }
    return {
        "count": len(values),
        "minimum": min(values),
        "median": statistics.median(values),
        "mean": statistics.fmean(values),
        "maximum": max(values),
        "values": values,
    }


def _physical_loc(path: Path) -> int:
    return len(
        path.read_text(encoding="utf-8", errors="replace").splitlines()
    )
