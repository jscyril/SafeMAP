from __future__ import annotations

import re

from ..models import FunctionInfo

C_TO_RUST = {
    "int": "i32",
    "unsigned int": "u32",
    "long": "i64",
    "unsigned long": "u64",
    "long long": "i64",
    "long long int": "i64",
    "unsigned long long": "u64",
    "unsigned long long int": "u64",
    "short": "i16",
    "unsigned short": "u16",
    "char": "i8",
    "unsigned char": "u8",
    "float": "f32",
    "double": "f64",
    "size_t": "usize",
    "void": "()",
    "_Bool": "bool",
    "bool": "bool",
    "signed char": "i8",
    "short int": "i16",
    "unsigned short int": "u16",
    "long int": "i64",
    "unsigned long int": "u64",
    "long unsigned int": "u64",
    "unsigned": "u32",
}

SCALAR_RUST_TYPES = {
    "i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64", "usize",
    "f32", "f64", "bool",
}

# Pointee types that have no safe, behaviorally testable Rust counterpart in
# the planner's type vocabulary. A unit whose interface needs one is rejected
# at planning time instead of receiving a fabricated signature.
OPAQUE_POINTEES = {"void", "FILE", "struct _IO_FILE", "_IO_FILE"}

RUST_KEYWORDS = {
    "as", "break", "const", "continue", "crate", "else", "enum", "extern",
    "false", "fn", "for", "if", "impl", "in", "let", "loop", "match",
    "mod", "move", "mut", "pub", "ref", "return", "self", "Self",
    "static", "struct", "super", "trait", "true", "type", "unsafe", "use",
    "where", "while", "async", "await", "dyn", "abstract", "become", "box",
    "do", "final", "macro", "override", "priv", "typeof", "unsized",
    "virtual", "yield", "try",
}


QUALIFIERS = re.compile(r"\b(?:const|restrict|__restrict__|__restrict|volatile)\b")


def rust_type(c_type: str) -> str:
    normalized = " ".join(QUALIFIERS.sub(" ", c_type).replace("*", "").split())
    struct_match = re.fullmatch(r"struct\s+([A-Za-z_]\w*)", normalized)
    if struct_match:
        return struct_match.group(1)
    return C_TO_RUST.get(normalized, re.sub(r"\W+", "_", normalized).strip("_") or "()")


def split_pointer(c_type: str) -> tuple[str, int, bool]:
    """Return (base type, pointer depth, pointee is const) for a C type."""
    depth = c_type.count("*")
    head = c_type.split("*", 1)[0]
    base_const = bool(re.search(r"\bconst\b", head))
    base = " ".join(QUALIFIERS.sub(" ", head).split())
    return base, depth, base_const


def is_char_type(base: str) -> bool:
    return base in {"char", "signed char", "unsigned char"}


def struct_name(base: str) -> str | None:
    match = re.fullmatch(r"struct\s+([A-Za-z_]\w*)", base)
    return match.group(1) if match else None


def mappable_struct_names(structs) -> set[str]:
    """Structs whose every field maps to a scalar or fixed scalar array."""
    names = set()
    for item in structs or []:
        if item.fields and all(
            _field_is_scalar(field["type"]) for field in item.fields
        ):
            names.add(item.name)
    return names


def projectable_struct_names(structs) -> set[str]:
    """Structs with at least one scalar field (pointer fields are projected out)."""
    return {
        item.name for item in structs or []
        if any(_field_is_scalar(field["type"]) for field in item.fields)
    }


def projection_issue(
    function: FunctionInfo,
    parameter: str,
    struct,
    functions: dict[str, FunctionInfo] | None = None,
    _seen: frozenset = frozenset(),
) -> str | None:
    """Why `parameter` cannot be passed as a scalar-field projection of `struct`.

    The projection is sound for this unit only if every use of the pointer is
    a scalar-field access, a NULL/truth test, or a bare argument to another
    project function whose matching parameter is itself projection-safe. The
    pointer is never stored, compared with another pointer, or used to take a
    field address.
    """
    scalar_fields = {
        field["name"] for field in struct.fields if _field_is_scalar(field["type"])
    }
    opening = function.body.find("{")
    body = function.body[opening:] if opening >= 0 else function.body
    body = re.sub(r"/\*.*?\*/", " ", body, flags=re.DOTALL)
    body = re.sub(r"//[^\n]*", " ", body)
    body = re.sub(r'"(?:\\.|[^"\\])*"', '""', body)
    name = re.escape(parameter)
    for match in re.finditer(rf"(?<![\w.]){name}\b", body):
        before = body[:match.start()].rstrip()
        after = body[match.end():]
        if before.endswith("->") or before.endswith("."):
            continue
        access = re.match(r"\s*->\s*(\w+)", after)
        if access:
            if access.group(1) not in scalar_fields:
                return f"accesses non-scalar field `{access.group(1)}` of `{struct.name}`"
            if before.endswith("&"):
                return f"takes the address of field `{access.group(1)}`"
            continue
        if re.match(r"\s*(?:==|!=)\s*(?:NULL|0)\b", after) or re.search(
            r"(?:\bNULL|\b0)\s*(?:==|!=)\s*$", before
        ):
            continue
        if before.endswith("!") and not before.endswith("!="):
            continue
        call = _enclosing_call(body, match.start())
        bare_argument = re.match(r"\s*[,)]", after) is not None
        truth_context = re.match(r"\s*(?:\)|&&|\|\||\?)", after) and (
            re.search(r"(?:&&|\|\||\?|\(|!)\s*$", before)
        )
        if truth_context and (call is None or call[0] in {"if", "while", "assert"}):
            continue
        if call and bare_argument and functions and call[0] in functions:
            issue = _callee_projection_issue(
                functions[call[0]], call[1], struct, functions, _seen | {function.name},
            )
            if issue is None:
                continue
            return f"passes `{parameter}` to `{call[0]}`, which {issue}"
        return f"pointer `{parameter}` escapes (passed, stored, or compared)"
    return None


def _enclosing_call(body: str, position: int) -> tuple[str, int] | None:
    """(callee, argument index) of the call whose parentheses contain position."""
    depth, commas = 0, 0
    for index in range(position - 1, -1, -1):
        char = body[index]
        if char in ")]":
            depth += 1
        elif char in "([":
            if depth == 0:
                if char == "[":
                    return None
                callee = re.search(r"(\w+)\s*$", body[:index])
                return (callee.group(1), commas) if callee else None
            depth -= 1
        elif char == "," and depth == 0:
            commas += 1
        elif char in ";{}" and depth == 0:
            return None
    return None


def _callee_projection_issue(callee, index, struct, functions, seen) -> str | None:
    if callee.name in seen:
        return None
    if index >= len(callee.parameters):
        return "is variadic or takes fewer parameters"
    parameter = callee.parameters[index]
    base, depth, _ = split_pointer(parameter.c_type)
    if depth != 1 or struct_name(base) != struct.name:
        return f"does not take `{struct.name} *` at that position"
    return projection_issue(callee, parameter.name, struct, functions, seen)


def struct_field_rust_type(c_type: str) -> str | None:
    array = re.fullmatch(r"(.+?)\s*\[(\d+)\]", c_type.strip())
    if array:
        element = _scalar(array.group(1))
        if element is None:
            return None
        if element == "i8":
            element = "u8"
        return f"[{element}; {array.group(2)}]"
    if "*" in c_type:
        return None
    return _scalar(c_type)


def _field_is_scalar(c_type: str) -> bool:
    return struct_field_rust_type(c_type) is not None


def _scalar(c_type: str) -> str | None:
    base = " ".join(QUALIFIERS.sub(" ", c_type).split())
    if base.startswith("enum "):
        return "i32"
    mapped = C_TO_RUST.get(base)
    return mapped if mapped in SCALAR_RUST_TYPES else None


def rust_identifier(name: str) -> str:
    return f"r#{name}" if name in RUST_KEYWORDS else name


def generate_signature(
    function: FunctionInfo,
    use_safe_signatures: bool = True,
    structs=None,
) -> str:
    return plan_signature(function, use_safe_signatures, structs)[0]


def plan_signature(
    function: FunctionInfo,
    use_safe_signatures: bool = True,
    structs=None,
    functions: dict[str, FunctionInfo] | None = None,
) -> tuple[str, list[str]]:
    """Plan a safe Rust signature and report every type it cannot map.

    An issue means the planner has no safe, harnessable Rust type for that
    part of the interface; callers must reject the unit rather than use the
    returned (best-effort) signature.
    """
    if not use_safe_signatures:
        return generate_raw_signature(function), []
    known_structs = (
        mappable_struct_names(structs) if structs is not None else None
    )
    projectable = projectable_struct_names(structs) if structs is not None else set()
    struct_by_name = {item.name: item for item in structs or []}
    issues: list[str] = []
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
        pointee, depth, _ = split_pointer(parameter.c_type)
        if parameter.array_length is not None:
            depth = max(depth, 1)
        base = rust_type(parameter.c_type)
        kind = fact.usage_kind if fact else None
        if depth > 1:
            issues.append(f"{rust_identifier(parameter.name)}: pointer-to-pointer has no planned safe type")
        elif depth == 1 and pointee in OPAQUE_POINTEES:
            issues.append(f"{rust_identifier(parameter.name)}: opaque pointee `{pointee}` has no planned safe type")
        elif depth == 1 and kind not in {"pointer_length_array", "fixed_size_array"}:
            issue = _pointee_issue(pointee, known_structs, parameter, c_string_parameters, kind)
            name = struct_name(pointee)
            if issue and name in projectable:
                issue = projection_issue(
                    function, parameter.name, struct_by_name[name], functions,
                )
            if issue:
                issues.append(f"{rust_identifier(parameter.name)}: {issue}")
        elif depth == 0:
            issue = _value_issue(pointee, known_structs)
            if issue:
                issues.append(f"{rust_identifier(parameter.name)}: {issue}")
        string_like = (
            depth == 1
            and is_char_type(pointee)
            and parameter.is_const
            and kind not in {"pointer_length_array", "fixed_size_array"}
        )
        if (parameter.name in c_string_parameters and parameter.is_const) or (
            string_like and kind != "nullable_pointer"
        ):
            output.append(f"{rust_identifier(parameter.name)}: &str")
        elif string_like and kind == "nullable_pointer":
            output.append(f"{rust_identifier(parameter.name)}: Option<&str>")
        elif kind == "pointer_length_array":
            mutable = "&mut " if _indexed_parameter_is_written(
                function.body, parameter.name
            ) else "&"
            element = "u8" if is_char_type(pointee) else base
            output.append(f"{rust_identifier(parameter.name)}: {mutable}[{element}]")
        elif kind == "fixed_size_array":
            mutable = "&mut " if _indexed_parameter_is_written(
                function.body, parameter.name
            ) else "&"
            output.append(
                f"{rust_identifier(parameter.name)}: {mutable}[{base}; {parameter.array_length}]"
            )
        elif kind == "output_parameter":
            if function.return_type.strip() != "void" or _is_direct_output(parameter.name, function):
                output_types.append(base)
            else:
                output.append(f"{rust_identifier(parameter.name)}: &mut {base}")
        elif kind == "nullable_pointer":
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{rust_identifier(parameter.name)}: Option<{mutable}{base}>")
        elif parameter.is_pointer:
            mutable = "&mut " if not parameter.is_const else "&"
            output.append(f"{rust_identifier(parameter.name)}: {mutable}{base}")
        elif _is_consumed_length(parameter.name, function):
            continue
        else:
            output.append(f"{rust_identifier(parameter.name)}: {base}")
    return_type, return_issue = _return_type(function, known_structs)
    if return_issue:
        issues.append(f"return: {return_issue}")
    if has_boolean_int and function.return_type.strip() in {
        "int", "unsigned int", "long", "short",
    }:
        return_type = "bool"
    if output_types:
        migrated = output_types[0] if len(output_types) == 1 else f"({', '.join(output_types)})"
        if has_error_code:
            return_type = f"Result<{migrated}, i32>"
        elif function.return_type.strip() != "void":
            # Keep the C return value: dropping it silently loses behavior.
            return_type = f"({return_type}, {', '.join(output_types)})"
        else:
            return_type = migrated
    elif has_error_code and _is_integer_c_type(function.return_type):
        return_type = f"Result<{return_type}, i32>"
    signature = (
        f"pub fn {rust_identifier(function.name)}"
        f"({', '.join(output)}) -> {return_type}"
    )
    return signature, issues


def _pointee_issue(pointee, known_structs, parameter, c_string_parameters, kind) -> str | None:
    if is_char_type(pointee):
        if parameter.is_const or parameter.name in c_string_parameters:
            return None
        if kind == "output_parameter":
            return None
        return "mutable C string without a length has no planned safe type"
    return _value_issue(pointee, known_structs)


def _value_issue(base: str, known_structs) -> str | None:
    if base.startswith("enum ") or _scalar(base) is not None or base == "void":
        return None
    name = struct_name(base)
    if name is not None:
        if known_structs is None or name in known_structs:
            return None
        return f"struct `{name}` has pointer or non-scalar fields with unresolved ownership"
    if "(" in base:
        return "function pointer has no planned safe type"
    if known_structs is None:
        return None
    return f"type `{base}` has no planned safe mapping"


def _return_type(function: FunctionInfo, known_structs) -> tuple[str, str | None]:
    c_type = function.return_type.strip()
    pointee, depth, _ = split_pointer(c_type)
    allocates = any(
        item.idiom_type == "manual_allocation" for item in function.idioms
    )
    if depth == 0:
        return rust_type(c_type), _value_issue(pointee, known_structs)
    if depth > 1 or pointee in OPAQUE_POINTEES:
        return rust_type(c_type), "returned pointer has no planned safe type"
    if is_char_type(pointee):
        # NULL maps to None; a returned string is copied into an owned String.
        return "Option<String>", None
    if _is_vec_allocation(function):
        return f"Vec<{rust_type(c_type)}>", None
    if allocates:
        issue = _value_issue(pointee, known_structs)
        return f"Box<{rust_type(c_type)}>", issue
    return (
        rust_type(c_type),
        "returned pointer aliases caller-owned data; lifetime is not planned",
    )


def _is_integer_c_type(c_type: str) -> bool:
    mapped = _scalar(c_type)
    return mapped is not None and mapped not in {"f32", "f64", "bool"}


def generate_raw_signature(function: FunctionInfo) -> str:
    parameters = []
    for parameter in function.parameters:
        base = rust_type(parameter.c_type)
        if parameter.is_pointer:
            pointer = "*const" if parameter.is_const else "*mut"
            parameters.append(f"{rust_identifier(parameter.name)}: {pointer} {base}")
        else:
            parameters.append(f"{rust_identifier(parameter.name)}: {base}")
    return_type = rust_type(function.return_type)
    if "*" in function.return_type:
        return_type = f"*mut {return_type}"
    return (
        f"pub fn {rust_identifier(function.name)}"
        f"({', '.join(parameters)}) -> {return_type}"
    )


def _is_consumed_length(name: str, function: FunctionInfo) -> bool:
    if not re.search(r"(?:len|length|size|count|n)$", name, re.I):
        return False
    return any(
        fact.usage_kind == "pointer_length_array" for fact in function.pointer_facts
    )


def _indexed_parameter_is_written(body: str, name: str) -> bool:
    escaped = re.escape(name)
    return re.search(
        rf"\b{escaped}\s*\[[^\]]+\]\s*(?:[+\-*/]?=|\+\+|--)",
        body,
    ) is not None


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
