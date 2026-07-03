from __future__ import annotations

import re

from ..models import FunctionInfo

C_TO_RUST = {
    "int": "i32",
    "unsigned int": "u32",
    "long": "i64",
    "unsigned long": "u64",
    "short": "i16",
    "unsigned short": "u16",
    "char": "i8",
    "unsigned char": "u8",
    "float": "f32",
    "double": "f64",
    "size_t": "usize",
    "void": "()",
}


def rust_type(c_type: str) -> str:
    normalized = " ".join(c_type.replace("const", "").replace("*", "").split())
    return C_TO_RUST.get(normalized, re.sub(r"\W+", "_", normalized).strip("_") or "()")


def generate_signature(function: FunctionInfo) -> str:
    fact_by_name = {fact.variable: fact for fact in function.pointer_facts}
    c_string_parameters = {
        variable
        for idiom in function.idioms
        if idiom.idiom_type == "c_string"
        for variable in idiom.variables
    }
    output = []
    output_types = []
    has_error_code = any(item.idiom_type == "error_code_return" for item in function.idioms)
    has_boolean_int = any(item.idiom_type == "boolean_int" for item in function.idioms)
    for parameter in function.parameters:
        fact = fact_by_name.get(parameter.name)
        base = rust_type(parameter.c_type)
        if parameter.name in c_string_parameters and parameter.is_const:
            output.append(f"{parameter.name}: &str")
        elif fact and fact.usage_kind == "pointer_length_array":
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{parameter.name}: {mutable}[{base}]")
        elif fact and fact.usage_kind == "output_parameter":
            if function.return_type.strip() != "void" or _is_direct_output(parameter.name, function):
                output_types.append(base)
            else:
                output.append(f"{parameter.name}: &mut {base}")
        elif fact and fact.usage_kind == "nullable_pointer":
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{parameter.name}: Option<{mutable}{base}>")
        elif parameter.is_pointer:
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{parameter.name}: {mutable}{base}")
        elif _is_consumed_length(parameter.name, function):
            continue
        else:
            output.append(f"{parameter.name}: {base}")
    return_type = rust_type(function.return_type)
    if has_boolean_int and function.return_type.strip() in {
        "int", "unsigned int", "long", "short",
    }:
        return_type = "bool"
    if "*" in function.return_type and _is_vec_allocation(function):
        return_type = f"Vec<{rust_type(function.return_type)}>"
    elif "*" in function.return_type and any(
        item.idiom_type == "manual_allocation" for item in function.idioms
    ):
        return_type = f"Box<{rust_type(function.return_type)}>"
    if output_types:
        migrated = output_types[0] if len(output_types) == 1 else f"({', '.join(output_types)})"
        return_type = f"Result<{migrated}, i32>" if has_error_code else migrated
    elif has_error_code:
        return_type = f"Result<{return_type}, i32>"
    return f"pub fn {function.name}({', '.join(output)}) -> {return_type}"


def _is_consumed_length(name: str, function: FunctionInfo) -> bool:
    if not re.search(r"(?:len|length|size|count|n)$", name, re.I):
        return False
    return any(
        fact.usage_kind == "pointer_length_array" for fact in function.pointer_facts
    )


def _is_direct_output(name: str, function: FunctionInfo) -> bool:
    escaped = re.escape(name)
    return (
        re.search(rf"\*\s*{escaped}\s*=", function.body) is not None
        and re.search(rf"\*\s*{escaped}\s*(?:[+\-*/]=|\+\+|--)", function.body) is None
    )


def _is_vec_allocation(function: FunctionInfo) -> bool:
    return (
        "*" in function.return_type
        and any(item.idiom_type == "manual_allocation" for item in function.idioms)
        and re.search(r"\b(?:malloc|calloc)\s*\([^;]*(?:len|length|size|count|n)\b", function.body)
        is not None
        and re.search(r"\b[A-Za-z_]\w*\s*\[\s*[A-Za-z_]\w*\s*\]\s*=", function.body)
        is not None
    )
