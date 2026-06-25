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
    "void": "()",
}


def rust_type(c_type: str) -> str:
    normalized = " ".join(c_type.replace("const", "").replace("*", "").split())
    return C_TO_RUST.get(normalized, re.sub(r"\W+", "_", normalized).strip("_") or "()")


def generate_signature(function: FunctionInfo) -> str:
    fact_by_name = {fact.variable: fact for fact in function.pointer_facts}
    output = []
    output_types = []
    has_error_code = any(item.idiom_type == "error_code_return" for item in function.idioms)
    for parameter in function.parameters:
        fact = fact_by_name.get(parameter.name)
        base = rust_type(parameter.c_type)
        if fact and fact.usage_kind == "pointer_length_array":
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{parameter.name}: {mutable}[{base}]")
        elif fact and fact.usage_kind == "output_parameter":
            if function.return_type.strip() == "void":
                output.append(f"{parameter.name}: &mut {base}")
            else:
                output_types.append(base)
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
    if "*" in function.return_type and any(
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
