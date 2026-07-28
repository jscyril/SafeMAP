from __future__ import annotations

import re
from pathlib import Path

from ..models import FunctionInfo, MigrationPlan, ProjectInfo, StructInfo
from .signature_generator import rust_identifier, rust_type


def synthesize_safe_crate(
    project: ProjectInfo,
    functions: list[FunctionInfo],
    plans: list[MigrationPlan],
    output: Path,
    *,
    structs: list[StructInfo] | None = None,
) -> list[str]:
    plan_by_function = {
        plan.function: plan
        for plan in plans
        if plan.status == "planned"
        and not (
            plan.patterns
            and all(
                pattern.pattern == "unguided_rewrite"
                for pattern in plan.patterns
            )
        )
    }
    rendered: list[str] = []
    rendered_functions: list[FunctionInfo] = []
    generated: list[str] = []
    for function in functions:
        plan = plan_by_function.get(function.name)
        if plan is None:
            continue
        body = _synthesize_function(function, plan)
        if body is None:
            continue
        rendered.append(body)
        rendered_functions.append(function)
        generated.append(plan.unit_id)
    if not rendered:
        return []
    source_dir = output / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    rendered_structs = _render_used_structs(
        structs or [],
        rendered_functions,
    )
    sections = [*rendered_structs, *rendered]
    (source_dir / "lib.rs").write_text(
        "#![forbid(unsafe_code)]\n\n" + "\n\n".join(sections) + "\n",
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


def detect_synthesis_rule(
    function: FunctionInfo,
    plan: MigrationPlan,
) -> str | None:
    candidate = _synthesize_with_rule(function, plan)
    return candidate[0] if candidate is not None else None


def _synthesize_function(function: FunctionInfo, plan: MigrationPlan) -> str | None:
    if plan.synthesis_support == "not_implemented":
        return None
    candidate = _synthesize_with_rule(function, plan)
    return candidate[1] if candidate is not None else None


def _synthesize_with_rule(
    function: FunctionInfo,
    plan: MigrationPlan,
) -> tuple[str, str] | None:
    signature = plan.target_signature
    body = function.body
    if _is_bit_reverse(function):
        parameter = function.parameters[0].name
        return (
            "bit_reverse",
            f"{signature} {{\n    {parameter}.reverse_bits()\n}}",
        )
    if _is_boolean_int(function):
        rendered = _boolean_int_function(body, signature)
        return ("boolean_integer", rendered) if rendered is not None else None
    if _is_simple_return(function):
        rendered = _simple_return_function(function, signature)
        return ("scalar_return", rendered) if rendered is not None else None
    if _is_internal_call_return(function, plan):
        rendered = _simple_return_function(function, signature)
        return (
            "internal_call_return",
            rendered,
        ) if rendered is not None else None
    if _is_struct_field_return(function):
        rendered = _struct_field_return_function(function, signature)
        return (
            "struct_field_return",
            rendered,
        ) if rendered is not None else None
    if _is_simple_vec_allocation(function):
        rendered = _simple_vec_allocation_function(function, signature)
        return ("vector_allocation", rendered) if rendered is not None else None
    if _is_simple_box_allocation(function):
        rendered = _simple_box_allocation_function(function, signature)
        return ("box_allocation", rendered) if rendered is not None else None
    if _is_mutable_scalar_update(function):
        rendered = _mutable_scalar_update_function(function, signature)
        return ("mutable_scalar_update", rendered) if rendered is not None else None
    if _is_direct_output_tuple(function):
        rendered = _direct_output_tuple_function(function, signature)
        return ("output_tuple", rendered) if rendered is not None else None
    if _is_mutable_slice_increment(function):
        rendered = _mutable_slice_increment_function(function, signature)
        return ("mutable_slice_update", rendered) if rendered is not None else None
    if _is_error_code_output(function):
        rendered = _result_output_function(function, signature)
        return ("result_output", rendered) if rendered is not None else None
    if _is_nullable_read(function):
        return ("nullable_read", _nullable_read_function(body, signature))
    if _is_c_string_length(function):
        rendered = _c_string_length_function(function, signature)
        return ("c_string_length", rendered) if rendered is not None else None
    if _is_slice_dot_product(function):
        rendered = _slice_dot_product_function(function, signature)
        return (
            "slice_dot_product",
            rendered,
        ) if rendered is not None else None
    if _is_slice_sum(function):
        parameter = _array_parameter(function)
        if parameter is None:
            return None
        return (
            (
                "fixed_array_sum"
                if parameter.array_length is not None
                else "slice_sum"
            ),
            f"{signature} {{\n"
            f"    {parameter.name}.iter().copied().sum()\n"
            "}",
        )
    if _is_slice_max(function):
        parameter = _array_parameter(function)
        if parameter is None:
            return None
        if "Result<" not in signature:
            return (
                (
                    "fixed_array_max"
                    if parameter.array_length is not None
                    else "slice_max"
                ),
                f"{signature} {{\n"
                f"    {parameter.name}.iter().copied().max().unwrap()\n"
                "}",
            )
        return ("slice_max_result",
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
        function.return_type.strip() != "void"
        and not function.pointer_facts
        and not function.calls
        and re.search(r"\breturn\s+([^;]+);", function.body) is not None
    )


def _is_internal_call_return(
    function: FunctionInfo,
    plan: MigrationPlan,
) -> bool:
    return (
        function.return_type.strip() != "void"
        and not function.pointer_facts
        and bool(function.calls)
        and set(function.calls) == set(plan.internal_calls)
        and re.search(r"\breturn\s+([^;]+);", function.body) is not None
    )


def _is_struct_field_return(function: FunctionInfo) -> bool:
    return (
        function.return_type.strip() != "void"
        and any(
            idiom.idiom_type == "struct_pointer"
            for idiom in function.idioms
        )
        and not function.calls
        and re.search(r"\breturn\s+([^;]+);", function.body) is not None
    )


def _struct_field_return_function(
    function: FunctionInfo,
    signature: str,
) -> str | None:
    returned = re.search(r"\breturn\s+([^;]+);", function.body)
    if returned is None:
        return None
    expression = _c_expr_to_rust(returned.group(1))
    if not _is_arithmetic_expression(expression):
        return None
    return f"{signature} {{\n    {expression}\n}}"


def _simple_return_function(
    function: FunctionInfo,
    signature: str,
) -> str | None:
    returned = re.search(r"\breturn\s+([^;]+);", function.body)
    if not returned:
        return None
    expr = _c_expr_to_rust(returned.group(1))
    if not _is_arithmetic_expression(expr):
        return None
    if function.return_type.strip() in {"float", "double", "long double"}:
        expr = re.sub(
            r"(?<![A-Za-z0-9_.])(-?\d+)(?![A-Za-z0-9_.])",
            r"\1.0",
            expr,
        )
    return f"{signature} {{\n    {expr}\n}}"


def _is_bit_reverse(function: FunctionInfo) -> bool:
    if (
        len(function.parameters) != 1
        or function.parameters[0].is_pointer
        or "unsigned" not in function.return_type
    ):
        return False
    parameter = re.escape(function.parameters[0].name)
    body = function.body
    return (
        len(re.findall(rf"\b{parameter}\s*=", body)) >= 3
        and all(mask in body.lower() for mask in ("0x55", "0x33", "0x0f"))
        and ">>" in body
        and "<<" in body
        and re.search(rf"\breturn\s+[^;]*\b{parameter}\b[^;]*;", body)
        is not None
    )


def _is_arithmetic_expression(expression: str) -> bool:
    identifier = r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*"
    number = r"(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?"
    token = rf"(?:{identifier}|{number}|[-+*/%,()]|\s+)"
    return re.fullmatch(rf"(?:{token})+", expression) is not None


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


def _is_simple_vec_allocation(function: FunctionInfo) -> bool:
    return (
        "*" in function.return_type
        and any(item.idiom_type == "manual_allocation" for item in function.idioms)
        and re.search(r"\b(?:malloc|calloc)\s*\([^;]*(?:len|length|size|count|n)\b", function.body)
        is not None
        and re.search(
            r"\b([A-Za-z_]\w*)\s*\[\s*([A-Za-z_]\w*)\s*\]\s*=\s*\2\s*;",
            function.body,
        )
        and re.search(r"\breturn\s+[A-Za-z_]\w*\s*;", function.body)
    )


def _simple_vec_allocation_function(function: FunctionInfo, signature: str) -> str | None:
    if "Vec<" not in signature:
        return None
    length = _length_parameter(function)
    if length is None:
        return None
    return (
        f"{signature} {{\n"
        f"    let len = {length}.max(0) as usize;\n"
        "    (0..len).map(|value| value as i32).collect()\n"
        "}"
    )


def _length_parameter(function: FunctionInfo) -> str | None:
    for parameter in function.parameters:
        if (
            not parameter.is_pointer
            and re.search(r"(?:len|length|size|count|n)$", parameter.name, re.I)
        ):
            return parameter.name
    return None


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
        any(
            item.usage_kind in {"pointer_length_array", "fixed_size_array"}
            for item in function.pointer_facts
        )
        and re.search(r"\b(?:sum|total)\s*\+=\s*[A-Za-z_]\w*\s*\[", function.body)
        and not any(item.usage_kind == "output_parameter" for item in function.pointer_facts)
    )


def _is_slice_dot_product(function: FunctionInfo) -> bool:
    arrays = {
        item.variable
        for item in function.pointer_facts
        if item.usage_kind == "pointer_length_array"
    }
    if len(arrays) != 2:
        return False
    cast = r"(?:\(\s*(?:double|float)\s*\)\s*)?"
    names = "|".join(re.escape(name) for name in sorted(arrays))
    indexed = rf"(?:{names})\s*\[\s*[A-Za-z_]\w*\s*\]"
    return re.search(
        rf"\b([A-Za-z_]\w*)\s*\+=\s*{cast}{indexed}\s*\*\s*"
        rf"{cast}{indexed}\s*;",
        function.body,
    ) is not None


def _slice_dot_product_function(
    function: FunctionInfo,
    signature: str,
) -> str | None:
    arrays = [
        parameter
        for parameter in function.parameters
        if any(
            fact.variable == parameter.name
            and fact.usage_kind == "pointer_length_array"
            for fact in function.pointer_facts
        )
    ]
    if len(arrays) != 2:
        return None
    left, right = arrays
    left_cast = " as f64" if "float" in left.c_type and "double" not in left.c_type else ""
    right_cast = " as f64" if "float" in right.c_type and "double" not in right.c_type else ""
    return (
        f"{signature} {{\n"
        f"    {left.name}.iter().zip({right.name}.iter())\n"
        f"        .map(|(&left, &right)| "
        f"(left{left_cast}) * (right{right_cast}))\n"
        "        .fold(0.0_f64, |accumulator, value| accumulator + value)\n"
        "}"
    )


def _is_slice_max(function: FunctionInfo) -> bool:
    return (
        any(
            item.usage_kind in {"pointer_length_array", "fixed_size_array"}
            for item in function.pointer_facts
        )
        and re.search(r"\bmax\b", function.body)
    )


def _array_parameter(function: FunctionInfo):
    for parameter in function.parameters:
        if any(
            fact.variable == parameter.name
            and fact.usage_kind in {
                "pointer_length_array",
                "fixed_size_array",
            }
            for fact in function.pointer_facts
        ):
            return parameter
    return None


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
    cast = ""
    if signature.endswith("-> i32"):
        cast = " as i32"
    elif signature.endswith("-> i64"):
        cast = " as i64"
    return f"{signature} {{\n    {parameter}.len(){cast}\n}}"


def _c_expr_to_rust(expression: str) -> str:
    compact = re.sub(r"\s+", " ", expression.strip())
    compact = compact.replace("->", ".")
    compact = re.sub(
        r"\(\s*(?:unsigned\s+)?(?:char|short|int|long|float|double)"
        r"(?:\s+long|\s+int)?\s*\)\s*",
        "",
        compact,
    )
    for keyword in (
        "as", "break", "const", "continue", "crate", "else", "enum",
        "extern", "false", "fn", "for", "if", "impl", "in", "let",
        "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
        "self", "static", "struct", "super", "trait", "true", "type",
        "unsafe", "use", "where", "while", "async", "await", "dyn",
    ):
        compact = re.sub(
            rf"\b{keyword}\b(?=\s*\()",
            rust_identifier(keyword),
            compact,
        )
    compact = re.sub(
        r"(?i)(?<=\d)(?:ull|llu|ll|ul|lu|u|l|f)\b",
        "",
        compact,
    )
    ternary = re.fullmatch(
        r"([A-Za-z_]\w*)\s*([<>])\s*([A-Za-z_]\w*)\s*\?\s*([A-Za-z_]\w*)\s*:\s*([A-Za-z_]\w*)",
        compact,
    )
    if ternary:
        left, operator, right, when_true, when_false = ternary.groups()
        if operator == "<" and when_true == left and when_false == right:
            return f"{left}.min({right})"
        if operator == "<" and when_true == right and when_false == left:
            return f"{left}.max({right})"
        if operator == ">" and when_true == left and when_false == right:
            return f"{left}.max({right})"
        if operator == ">" and when_true == right and when_false == left:
            return f"{left}.min({right})"
    return compact


def _render_used_structs(
    structs: list[StructInfo],
    functions: list[FunctionInfo],
) -> list[str]:
    used = {
        match.group(1)
        for function in functions
        for parameter in function.parameters
        for match in [
            re.search(r"\bstruct\s+([A-Za-z_]\w*)", parameter.c_type)
        ]
        if match is not None
    }
    by_name = {item.name: item for item in structs}
    rendered = []
    for name in sorted(used):
        item = by_name.get(name)
        if item is None:
            continue
        fields = []
        for field in item.fields:
            field_type = rust_type(field["type"])
            if not field_type or "*" in field["type"] or "[" in field["type"]:
                fields = []
                break
            fields.append(f"    pub {rust_identifier(field['name'])}: {field_type},")
        if not fields:
            continue
        rendered.append(
            "#[derive(Clone, Copy, Debug, PartialEq)]\n"
            f"pub struct {name} {{\n"
            + "\n".join(fields)
            + "\n}"
        )
    return rendered


def _is_supported_expr(expression: str) -> bool:
    return re.fullmatch(
        r"[A-Za-z_]\w*(?:\s*[-+*/%]\s*(?:[A-Za-z_]\w*|-?\d+))*|-?\d+|[A-Za-z_]\w*\.(?:min|max)\([A-Za-z_]\w*\)",
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
