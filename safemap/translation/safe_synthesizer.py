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
    if _is_boolean_int(function):
        return _boolean_int_function(body, signature)
    if _is_simple_return(function):
        return _simple_return_function(body, signature)
    if _is_simple_box_allocation(function):
        return _simple_box_allocation_function(function, signature)
    if _is_mutable_scalar_update(function):
        return _mutable_scalar_update_function(function, signature)
    if _is_direct_output_tuple(function):
        return _direct_output_tuple_function(function, signature)
    if _is_mutable_slice_increment(function):
        return _mutable_slice_increment_function(function, signature)
    if _is_error_code_output(function):
        return _result_output_function(function, signature)
    if _is_nullable_read(function):
        return _nullable_read_function(body, signature)
    if _is_c_string_length(function):
        return _c_string_length_function(function, signature)
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


def _is_simple_return(function: FunctionInfo) -> bool:
    return (
        function.name != "main"
        and function.return_type.strip() != "void"
        and not function.pointer_facts
        and not function.calls
        and re.search(r"\breturn\s+([^;]+);", function.body) is not None
    )


def _simple_return_function(body: str, signature: str) -> str | None:
    returned = re.search(r"\breturn\s+([^;]+);", body)
    if not returned:
        return None
    expr = _c_expr_to_rust(returned.group(1))
    if not re.fullmatch(
        r"[A-Za-z_]\w*(?:\s*[-+*/]\s*(?:[A-Za-z_]\w*|-?\d+))*|-?\d+",
        expr,
    ):
        return None
    return f"{signature} {{\n    {expr}\n}}"


def _is_boolean_int(function: FunctionInfo) -> bool:
    return any(item.idiom_type == "boolean_int" for item in function.idioms)


def _boolean_int_function(body: str, signature: str) -> str | None:
    returned = re.search(r"\breturn\s+([^;]+);", body)
    if not returned:
        return None
    expr = _c_expr_to_rust(returned.group(1))
    if not _is_supported_boolean_expr(expr):
        return None
    return f"{signature} {{\n    {expr}\n}}"


def _is_simple_box_allocation(function: FunctionInfo) -> bool:
    return (
        "*" in function.return_type
        and any(item.idiom_type == "manual_allocation" for item in function.idioms)
        and re.search(
            r"\*\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*|-?\d+)\s*;",
            function.body,
        )
        and re.search(r"\breturn\s+[A-Za-z_]\w*\s*;", function.body)
    )


def _simple_box_allocation_function(function: FunctionInfo, signature: str) -> str | None:
    assignment = re.search(
        r"\*\s*([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*|-?\d+)\s*;",
        function.body,
    )
    if assignment is None:
        return None
    value = assignment.group(2)
    return f"{signature} {{\n    Box::new({value})\n}}"


def _is_mutable_scalar_update(function: FunctionInfo) -> bool:
    return (
        function.return_type.strip() == "void"
        and any(item.usage_kind == "output_parameter" for item in function.pointer_facts)
        and _mutable_scalar_update(function.body) is not None
    )


def _mutable_scalar_update_function(function: FunctionInfo, signature: str) -> str | None:
    update = _mutable_scalar_update(function.body)
    if update is None:
        return None
    parameter, operator, amount = update
    return f"{signature} {{\n    *{parameter} {operator}= {amount};\n}}"


def _mutable_scalar_update(body: str) -> tuple[str, str, str] | None:
    assignment = re.search(
        r"\*\s*([A-Za-z_]\w*)\s*([+\-*/])=\s*([A-Za-z_]\w*|-?\d+)\s*;",
        body,
    )
    if assignment:
        return assignment.group(1), assignment.group(2), assignment.group(3)
    increment = re.search(
        r"(?:\+\+\s*\*\s*([A-Za-z_]\w*)|\*\s*([A-Za-z_]\w*)\s*\+\+)\s*;",
        body,
    )
    if increment:
        return increment.group(1) or increment.group(2), "+", "1"
    decrement = re.search(
        r"(?:--\s*\*\s*([A-Za-z_]\w*)|\*\s*([A-Za-z_]\w*)\s*--)\s*;",
        body,
    )
    if decrement:
        return decrement.group(1) or decrement.group(2), "-", "1"
    return None


def _is_direct_output_tuple(function: FunctionInfo) -> bool:
    return (
        function.return_type.strip() == "void"
        and any(item.usage_kind == "output_parameter" for item in function.pointer_facts)
        and bool(_direct_output_assignments(function))
    )


def _direct_output_tuple_function(function: FunctionInfo, signature: str) -> str | None:
    assignments = _direct_output_assignments(function)
    if not assignments:
        return None
    values = [_c_expr_to_rust(value) for _, value in assignments]
    if not all(_is_supported_expr(value) for value in values):
        return None
    returned = values[0] if len(values) == 1 else f"({', '.join(values)})"
    return f"{signature} {{\n    {returned}\n}}"


def _direct_output_assignments(function: FunctionInfo) -> list[tuple[str, str]]:
    output_parameters = [
        parameter.name for parameter in function.parameters
        if any(
            fact.variable == parameter.name and fact.usage_kind == "output_parameter"
            for fact in function.pointer_facts
        )
    ]
    assignments: list[tuple[str, str]] = []
    for parameter in output_parameters:
        match = re.search(
            rf"\*\s*{re.escape(parameter)}\s*=\s*([^;]+);",
            function.body,
        )
        if match is None:
            return []
        assignments.append((parameter, match.group(1)))
    return assignments


def _is_mutable_slice_increment(function: FunctionInfo) -> bool:
    return (
        any(
            item.usage_kind == "pointer_length_array"
            and not _is_const_pointer(item.pointer_type)
            for item in function.pointer_facts
        )
        and re.search(
            r"\b([A-Za-z_]\w*)\s*\[\s*[A-Za-z_]\w*\s*\]\s*\+=\s*(-?\d+)\s*;",
            function.body,
        )
        and function.return_type.strip() == "void"
    )


def _mutable_slice_increment_function(function: FunctionInfo, signature: str) -> str | None:
    assignment = re.search(
        r"\b([A-Za-z_]\w*)\s*\[\s*[A-Za-z_]\w*\s*\]\s*\+=\s*(-?\d+)\s*;",
        function.body,
    )
    if assignment is None:
        return None
    parameter = assignment.group(1)
    amount = assignment.group(2)
    return (
        f"{signature} {{\n"
        f"    for value in {parameter}.iter_mut() {{\n"
        f"        *value += {amount};\n"
        "    }\n"
        "}"
    )


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


def _is_c_string_length(function: FunctionInfo) -> bool:
    return (
        any(item.idiom_type == "c_string" for item in function.idioms)
        and function.return_type.strip() in {"int", "long", "short", "size_t"}
        and re.search(r"\breturn\s+(?:\([^)]*\)\s*)?strlen\s*\(", function.body)
        is not None
    )


def _c_string_length_function(function: FunctionInfo, signature: str) -> str | None:
    match = re.search(
        r"\breturn\s+(?:\([^)]*\)\s*)?strlen\s*\(\s*([A-Za-z_]\w*)\s*\)\s*;",
        function.body,
    )
    if match is None:
        return None
    parameter = match.group(1)
    cast = " as i32" if signature.endswith("-> i32") else ""
    return f"{signature} {{\n    {parameter}.len(){cast}\n}}"


def _c_expr_to_rust(expression: str) -> str:
    return re.sub(r"\s+", " ", expression.strip())


def _is_supported_expr(expression: str) -> bool:
    return re.fullmatch(
        r"[A-Za-z_]\w*(?:\s*[-+*/%]\s*(?:[A-Za-z_]\w*|-?\d+))*|-?\d+",
        expression,
    ) is not None


def _is_supported_boolean_expr(expression: str) -> bool:
    operand = r"(?:[A-Za-z_]\w*|-?\d+)(?:\s*[-+*/%]\s*(?:[A-Za-z_]\w*|-?\d+))*"
    return re.fullmatch(
        rf"{operand}\s*(?:==|!=|<=|>=|<|>)\s*{operand}",
        expression,
    ) is not None


def _is_const_pointer(pointer_type: str) -> bool:
    return bool(re.search(r"\bconst\b", pointer_type))
