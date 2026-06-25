from __future__ import annotations

import re
from pathlib import Path

from ..models import FunctionInfo, MigrationPlan, ProjectInfo


def synthesize_safe_crate(
    project: ProjectInfo,
    functions: list[FunctionInfo],
    plans: list[MigrationPlan],
    output: Path,
) -> list[str]:
    plan_by_function = {plan.function: plan for plan in plans if plan.status == "planned"}
    rendered: list[str] = []
    generated: list[str] = []
    for function in functions:
        plan = plan_by_function.get(function.name)
        if plan is None:
            continue
        body = _synthesize_function(function, plan)
        if body is None:
            continue
        rendered.append(body)
        generated.append(plan.unit_id)
    if not rendered:
        return []
    source_dir = output / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "lib.rs").write_text(
        "#![forbid(unsafe_code)]\n\n" + "\n\n".join(rendered) + "\n",
        encoding="utf-8",
    )
    (output / "Cargo.toml").write_text(
        "[package]\n"
        f'name = "{project.project_name.replace("-", "_")}"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n",
        encoding="utf-8",
    )
    return generated


def _synthesize_function(function: FunctionInfo, plan: MigrationPlan) -> str | None:
    signature = plan.target_signature
    body = function.body
    if _is_error_code_output(function):
        return _result_output_function(function, signature)
    if _is_nullable_read(function):
        return _nullable_read_function(body, signature)
    if _is_slice_sum(function):
        return f"{signature} {{\n    arr.iter().copied().sum()\n}}"
    if _is_slice_max(function):
        return (
            f"{signature} {{\n"
            "    if arr.is_empty() {\n"
            "        return Err(-1);\n"
            "    }\n"
            "    Ok(arr.iter().copied().max().unwrap())\n"
            "}"
        )
    return None


def _is_error_code_output(function: FunctionInfo) -> bool:
    return (
        function.return_type.strip() in {"int", "long", "short"}
        and any(item.usage_kind == "output_parameter" for item in function.pointer_facts)
        and any(item.idiom_type == "error_code_return" for item in function.idioms)
    )


def _result_output_function(function: FunctionInfo, signature: str) -> str | None:
    body = function.body
    if re.search(r"\bif\s*\(\s*([A-Za-z_]\w*)\s*==\s*0\s*\)\s*return\s*(-?\d+)\s*;", body):
        divisor = re.search(
            r"\bif\s*\(\s*([A-Za-z_]\w*)\s*==\s*0\s*\)\s*return\s*(-?\d+)\s*;",
            body,
        )
        assignment = re.search(r"\*\s*[A-Za-z_]\w*\s*=\s*([^;]+);", body)
        if divisor and assignment:
            expr = _c_expr_to_rust(assignment.group(1))
            return (
                f"{signature} {{\n"
                f"    if {divisor.group(1)} == 0 {{\n"
                f"        return Err({divisor.group(2)});\n"
                "    }\n"
                f"    Ok({expr})\n"
                "}"
            )
    if _is_slice_max(function):
        return (
            f"{signature} {{\n"
            "    if arr.is_empty() {\n"
            "        return Err(-1);\n"
            "    }\n"
            "    Ok(arr.iter().copied().max().unwrap())\n"
            "}"
        )
    assignment = re.search(r"\*\s*[A-Za-z_]\w*\s*=\s*([^;]+);", body)
    if assignment:
        return f"{signature} {{\n    Ok({_c_expr_to_rust(assignment.group(1))})\n}}"
    return None


def _is_nullable_read(function: FunctionInfo) -> bool:
    return any(item.usage_kind == "nullable_pointer" for item in function.pointer_facts)


def _nullable_read_function(body: str, signature: str) -> str:
    null_return = re.search(r"\bif\s*\([^)]*(?:NULL|0)[^)]*\)\s*return\s*(-?\d+)\s*;", body)
    fallback = null_return.group(1) if null_return else "0"
    parameter = signature.split("(", 1)[1].split(":", 1)[0].strip()
    if "Result<" in signature:
        return (
            f"{signature} {{\n"
            f"    match {parameter} {{\n"
            "        Some(value) => Ok(*value),\n"
            f"        None => Err({fallback}),\n"
            "    }\n"
            "}"
        )
    return (
        f"{signature} {{\n"
        f"    match {parameter} {{\n"
        "        Some(value) => *value,\n"
        f"        None => {fallback},\n"
        "    }\n"
        "}"
    )


def _is_slice_sum(function: FunctionInfo) -> bool:
    return (
        any(item.usage_kind == "pointer_length_array" for item in function.pointer_facts)
        and re.search(r"\b(?:sum|total)\s*\+=\s*[A-Za-z_]\w*\s*\[", function.body)
        and not any(item.usage_kind == "output_parameter" for item in function.pointer_facts)
    )


def _is_slice_max(function: FunctionInfo) -> bool:
    return (
        any(item.usage_kind == "pointer_length_array" for item in function.pointer_facts)
        and re.search(r"\bmax\b", function.body)
    )


def _c_expr_to_rust(expression: str) -> str:
    return re.sub(r"\s+", " ", expression.strip())
