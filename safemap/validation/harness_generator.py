from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..models import FunctionInfo, MigrationPlan, StructInfo
from ..translation.signature_generator import rust_identifier, rust_type


@dataclass(frozen=True)
class GeneratedHarness:
    c_source: str
    rust_source: str
    functions: tuple[str, ...]
    cases: int
    seed: int
    generator: str = "lcg32-small-scalars-v1"


_INTEGER_TYPES = {
    "char",
    "signed char",
    "unsigned char",
    "short",
    "short int",
    "unsigned short",
    "unsigned short int",
    "int",
    "unsigned",
    "unsigned int",
    "long",
    "long int",
    "unsigned long",
    "unsigned long int",
    "long long",
    "long long int",
    "unsigned long long",
    "unsigned long long int",
    "long long",
    "long long int",
    "unsigned long long",
    "unsigned long long int",
    "size_t",
}
_FLOAT_TYPES = {"float", "double"}


def generate_scalar_harness(
    c_source: Path,
    package: str,
    functions: list[FunctionInfo],
    plans: list[MigrationPlan],
    structs: list[StructInfo] | None = None,
    *,
    cases: int,
    seed: int,
) -> GeneratedHarness | None:
    plan_by_function = {plan.function: plan for plan in plans}
    struct_by_name = {
        item.name: item for item in (structs or [])
    }
    selected = [
        function
        for function in functions
        if _is_supported_scalar(
            function,
            plan_by_function.get(function.name),
        )
        or _is_supported_dot_product(
            function,
            plan_by_function.get(function.name),
        )
        or _is_supported_fixed_array(
            function,
            plan_by_function.get(function.name),
        )
        or _is_supported_struct_field(
            function,
            plan_by_function.get(function.name),
            struct_by_name,
        )
    ]
    if not selected:
        return None

    c_calls = "\n".join(
        _c_function_cases(function, cases, struct_by_name)
        for function in selected
    )
    rust_calls = "\n".join(
        _rust_function_cases(
            function,
            package,
            cases,
            struct_by_name,
        )
        for function in selected
    )
    include = str(c_source.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    c_harness = (
        "#include <stdint.h>\n"
        "#include <stdio.h>\n"
        "#include <string.h>\n"
        "#define main safemap_original_main\n"
        f'#include "{include}"\n'
        "#undef main\n\n"
        "static int next_i32(uint32_t *state) {\n"
        "    *state = *state * 1103515245u + 12345u;\n"
        "    return (int)((*state >> 16) % 201u) - 100;\n"
        "}\n\n"
        "static double next_f64(uint32_t *state) {\n"
        "    return (double)next_i32(state) / 7.0;\n"
        "}\n\n"
        "int main(void) {\n"
        f"    uint32_t state = {seed & 0xffffffff}u;\n"
        f"{c_calls}\n"
        "    return 0;\n"
        "}\n"
    )
    rust_harness = (
        "fn next_i32(state: &mut u32) -> i32 {\n"
        "    *state = state.wrapping_mul(1103515245).wrapping_add(12345);\n"
        "    ((*state >> 16) % 201) as i32 - 100\n"
        "}\n\n"
        "fn next_f64(state: &mut u32) -> f64 {\n"
        "    next_i32(state) as f64 / 7.0\n"
        "}\n\n"
        "fn main() {\n"
        f"    let mut state = {seed & 0xffffffff}u32;\n"
        f"{rust_calls}\n"
        "}\n"
    )
    return GeneratedHarness(
        c_source=c_harness,
        rust_source=rust_harness,
        functions=tuple(function.name for function in selected),
        cases=cases,
        seed=seed,
    )


def _is_supported_scalar(
    function: FunctionInfo,
    plan: MigrationPlan | None,
) -> bool:
    if plan is None or plan.synthesis_support != "implemented_support":
        return False
    if plan.synthesis_rule not in {
        "scalar_return",
        "boolean_integer",
        "bit_reverse",
        "internal_call_return",
    }:
        return False
    if any(item.is_pointer for item in function.parameters):
        return False
    if _normalize_c_type(function.return_type) not in _INTEGER_TYPES | _FLOAT_TYPES:
        return False
    return all(
        _normalize_c_type(parameter.c_type) in _INTEGER_TYPES | _FLOAT_TYPES
        for parameter in function.parameters
    )


def _is_supported_dot_product(
    function: FunctionInfo,
    plan: MigrationPlan | None,
) -> bool:
    return bool(
        plan is not None
        and plan.synthesis_support == "implemented_support"
        and plan.synthesis_rule == "slice_dot_product"
        and _normalize_c_type(function.return_type) in _FLOAT_TYPES
        and len([
            parameter for parameter in function.parameters
            if parameter.is_pointer
        ]) == 2
    )


def _is_supported_fixed_array(
    function: FunctionInfo,
    plan: MigrationPlan | None,
) -> bool:
    arrays = [
        parameter
        for parameter in function.parameters
        if parameter.array_length is not None
    ]
    return bool(
        plan is not None
        and plan.synthesis_support == "implemented_support"
        and plan.synthesis_rule in {
            "fixed_array_sum",
            "fixed_array_max",
        }
        and len(arrays) == 1
        and len(function.parameters) == 1
        and _pointer_base_type(arrays[0].c_type)
        in _INTEGER_TYPES | _FLOAT_TYPES
        and _normalize_c_type(function.return_type)
        in _INTEGER_TYPES | _FLOAT_TYPES
    )


def _is_supported_struct_field(
    function: FunctionInfo,
    plan: MigrationPlan | None,
    structs: dict[str, StructInfo],
) -> bool:
    if (
        plan is None
        or plan.synthesis_support != "implemented_support"
        or plan.synthesis_rule != "struct_field_return"
        or len(function.parameters) != 1
    ):
        return False
    name = _struct_name(function.parameters[0].c_type)
    item = structs.get(name or "")
    return bool(
        item is not None
        and item.fields
        and all(
            "*" not in field["type"]
            and "[" not in field["type"]
            and _normalize_c_type(field["type"])
            in _INTEGER_TYPES | _FLOAT_TYPES
            for field in item.fields
        )
    )


def _normalize_c_type(value: str) -> str:
    compact = re.sub(r"\b(?:const|volatile|static|register)\b", "", value)
    return " ".join(compact.replace("*", " * ").split()).strip()


def _c_function_cases(
    function: FunctionInfo,
    cases: int,
    structs: dict[str, StructInfo],
) -> str:
    if _is_dot_product_shape(function):
        return _c_dot_product_cases(function, cases)
    fixed = next(
        (
            parameter
            for parameter in function.parameters
            if parameter.array_length is not None
        ),
        None,
    )
    if fixed is not None:
        return _c_fixed_array_cases(function, fixed, cases)
    struct_name = (
        _struct_name(function.parameters[0].c_type)
        if len(function.parameters) == 1
        else None
    )
    if struct_name in structs:
        return _c_struct_cases(
            function,
            structs[struct_name],
            cases,
        )
    declarations, arguments = _c_arguments(function)
    result_type = _normalize_c_type(function.return_type)
    called_name = (
        "safemap_original_main"
        if function.name == "main"
        else function.name
    )
    call = f"{called_name}({', '.join(arguments)})"
    lines = [
        f"    for (int case_index = 0; case_index < {cases}; case_index++) {{",
        *[f"        {line}" for line in declarations],
    ]
    if _is_boolean(function):
        lines.append(
            f'        printf("{function.name}:%d\\n", (int)({call}));'
        )
    elif result_type == "float":
        lines.extend([
            f"        float result = {call};",
            "        uint32_t bits = 0;",
            "        memcpy(&bits, &result, sizeof(bits));",
            f'        printf("{function.name}:%08x\\n", bits);',
        ])
    elif result_type == "double":
        lines.extend([
            f"        double result = {call};",
            "        uint64_t bits = 0;",
            "        memcpy(&bits, &result, sizeof(bits));",
            f'        printf("{function.name}:%016llx\\n", '
            "(unsigned long long)bits);",
        ])
    elif "unsigned" in result_type or result_type == "size_t":
        lines.append(
            f'        printf("{function.name}:%llu\\n", '
            f"(unsigned long long)({call}));"
        )
    else:
        lines.append(
            f'        printf("{function.name}:%lld\\n", (long long)({call}));'
        )
    lines.append("    }")
    return "\n".join(lines)


def _rust_function_cases(
    function: FunctionInfo,
    package: str,
    cases: int,
    structs: dict[str, StructInfo],
) -> str:
    if _is_dot_product_shape(function):
        return _rust_dot_product_cases(function, package, cases)
    fixed = next(
        (
            parameter
            for parameter in function.parameters
            if parameter.array_length is not None
        ),
        None,
    )
    if fixed is not None:
        return _rust_fixed_array_cases(
            function,
            fixed,
            package,
            cases,
        )
    struct_name = (
        _struct_name(function.parameters[0].c_type)
        if len(function.parameters) == 1
        else None
    )
    if struct_name in structs:
        return _rust_struct_cases(
            function,
            structs[struct_name],
            package,
            cases,
        )
    declarations, arguments = _rust_arguments(function)
    result_type = _normalize_c_type(function.return_type)
    call = (
        f"{package}::{rust_identifier(function.name)}"
        f"({', '.join(arguments)})"
    )
    lines = [
        f"    for _case_index in 0..{cases} {{",
        *[f"        {line}" for line in declarations],
    ]
    if _is_boolean(function):
        lines.append(
            f'        println!("{function.name}:{{}}", ({call}) as i32);'
        )
    elif result_type == "float":
        lines.append(
            f'        println!("{function.name}:{{:08x}}", ({call}).to_bits());'
        )
    elif result_type == "double":
        lines.append(
            f'        println!("{function.name}:{{:016x}}", ({call}).to_bits());'
        )
    elif "unsigned" in result_type or result_type == "size_t":
        lines.append(
            f'        println!("{function.name}:{{}}", ({call}) as u128);'
        )
    else:
        lines.append(
            f'        println!("{function.name}:{{}}", ({call}) as i128);'
        )
    lines.append("    }")
    return "\n".join(lines)


def _c_arguments(function: FunctionInfo) -> tuple[list[str], list[str]]:
    declarations = []
    arguments = []
    for index, parameter in enumerate(function.parameters):
        c_type = _normalize_c_type(parameter.c_type)
        name = f"arg_{index}"
        if c_type in _FLOAT_TYPES:
            declarations.append(f"{c_type} {name} = ({c_type})next_f64(&state);")
        else:
            declarations.append(f"{c_type} {name} = ({c_type})next_i32(&state);")
            if _must_be_nonzero(function, parameter.name):
                declarations.append(f"if ({name} == 0) {name} = 1;")
        arguments.append(name)
    return declarations, arguments


def _is_dot_product_shape(function: FunctionInfo) -> bool:
    return (
        len([
            parameter for parameter in function.parameters
            if parameter.is_pointer
        ]) == 2
        and len([
            parameter for parameter in function.parameters
            if not parameter.is_pointer
        ]) == 1
        and re.search(
            r"\b[A-Za-z_]\w*\s*\+=\s*[^;]*\[[^\]]+\][^;]*\*"
            r"[^;]*\[[^\]]+\]",
            function.body,
        ) is not None
    )


def _c_dot_product_cases(function: FunctionInfo, cases: int) -> str:
    pointers = [
        parameter for parameter in function.parameters if parameter.is_pointer
    ]
    length = next(
        parameter for parameter in function.parameters if not parameter.is_pointer
    )
    left, right = pointers
    left_type = _normalize_c_type(left.c_type).replace(" *", "")
    right_type = _normalize_c_type(right.c_type).replace(" *", "")
    result_type = _normalize_c_type(function.return_type)
    return "\n".join([
        f"    for (int case_index = 0; case_index < {cases}; case_index++) {{",
        f"        {left_type} left[8];",
        f"        {right_type} right[8];",
        "        int length = (next_i32(&state) + 100) % 8 + 1;",
        "        for (int i = 0; i < length; i++) {",
        f"            left[i] = ({left_type})next_f64(&state);",
        f"            right[i] = ({right_type})next_f64(&state);",
        "        }",
        f"        {result_type} result = {function.name}("
        f"left, right, ({_normalize_c_type(length.c_type)})length);",
        "        uint64_t bits = 0;",
        "        memcpy(&bits, &result, sizeof(bits));",
        f'        printf("{function.name}:%016llx\\n", '
        "(unsigned long long)bits);",
        "    }",
    ])


def _rust_dot_product_cases(
    function: FunctionInfo,
    package: str,
    cases: int,
) -> str:
    pointers = [
        parameter for parameter in function.parameters if parameter.is_pointer
    ]
    left_type = _rust_scalar_type(
        _normalize_c_type(pointers[0].c_type).replace(" *", "")
    )
    right_type = _rust_scalar_type(
        _normalize_c_type(pointers[1].c_type).replace(" *", "")
    )
    return "\n".join([
        f"    for _case_index in 0..{cases} {{",
        "        let length = ((next_i32(&mut state) + 100) % 8 + 1) as usize;",
        f"        let mut left = [0 as {left_type}; 8];",
        f"        let mut right = [0 as {right_type}; 8];",
        "        for i in 0..length {",
        f"            left[i] = next_f64(&mut state) as {left_type};",
        f"            right[i] = next_f64(&mut state) as {right_type};",
        "        }",
        f"        let result = {package}::{rust_identifier(function.name)}("
        "&left[..length], &right[..length]);",
        f'        println!("{function.name}:{{:016x}}", result.to_bits());',
        "    }",
    ])


def _rust_arguments(function: FunctionInfo) -> tuple[list[str], list[str]]:
    declarations = []
    arguments = []
    signature_types = _rust_parameter_types(function)
    for index, parameter in enumerate(function.parameters):
        c_type = _normalize_c_type(parameter.c_type)
        rust_type = signature_types[index] if index < len(signature_types) else "i32"
        name = f"arg_{index}"
        generator = "next_f64(&mut state)" if c_type in _FLOAT_TYPES else "next_i32(&mut state)"
        declarations.append(f"let mut {name} = {generator} as {rust_type};")
        if c_type not in _FLOAT_TYPES and _must_be_nonzero(function, parameter.name):
            declarations.append(f"if {name} == 0 {{ {name} = 1; }}")
        arguments.append(name)
    return declarations, arguments


def _rust_parameter_types(function: FunctionInfo) -> list[str]:
    result = []
    for parameter in function.parameters:
        c_type = _normalize_c_type(parameter.c_type)
        if c_type == "float":
            result.append("f32")
        elif c_type == "double":
            result.append("f64")
        elif "unsigned" in c_type or c_type == "size_t":
            result.append("u64" if "long" in c_type or c_type == "size_t" else "u32")
        elif "long" in c_type:
            result.append("i64")
        else:
            result.append("i32")
    return result


def _rust_scalar_type(c_type: str) -> str:
    if c_type == "float":
        return "f32"
    if c_type == "double":
        return "f64"
    if "unsigned" in c_type or c_type == "size_t":
        return "u64" if "long" in c_type or c_type == "size_t" else "u32"
    if "long" in c_type:
        return "i64"
    return "i32"


def _pointer_base_type(c_type: str) -> str:
    return _normalize_c_type(c_type).replace(" *", "")


def _struct_name(c_type: str) -> str | None:
    match = re.search(r"\bstruct\s+([A-Za-z_]\w*)", c_type)
    return match.group(1) if match else None


def _c_fixed_array_cases(
    function: FunctionInfo,
    parameter,
    cases: int,
) -> str:
    length = parameter.array_length
    base = _pointer_base_type(parameter.c_type)
    result_type = _normalize_c_type(function.return_type)
    lines = [
        f"    for (int case_index = 0; case_index < {cases}; case_index++) {{",
        f"        {base} values[{length}];",
        f"        for (int i = 0; i < {length}; ++i) {{",
        (
            f"            values[i] = ({base})next_f64(&state);"
            if base in _FLOAT_TYPES
            else f"            values[i] = ({base})next_i32(&state);"
        ),
        "        }",
        f"        {result_type} result = {function.name}(values);",
        *_c_print_result(function.name, result_type, "result"),
        "    }",
    ]
    return "\n".join(lines)


def _rust_fixed_array_cases(
    function: FunctionInfo,
    parameter,
    package: str,
    cases: int,
) -> str:
    length = parameter.array_length
    base = _rust_scalar_type(_pointer_base_type(parameter.c_type))
    result_type = _normalize_c_type(function.return_type)
    generator = (
        "next_f64(&mut state)"
        if _pointer_base_type(parameter.c_type) in _FLOAT_TYPES
        else "next_i32(&mut state)"
    )
    call = (
        f"{package}::{rust_identifier(function.name)}(&values)"
    )
    return "\n".join([
        f"    for _case_index in 0..{cases} {{",
        f"        let mut values = [0 as {base}; {length}];",
        f"        for value in values.iter_mut() {{ *value = {generator} as {base}; }}",
        f"        let result = {call};",
        *_rust_print_result(function.name, result_type, "result"),
        "    }",
    ])


def _c_struct_cases(
    function: FunctionInfo,
    item: StructInfo,
    cases: int,
) -> str:
    result_type = _normalize_c_type(function.return_type)
    initializers = []
    for field in item.fields:
        field_type = _normalize_c_type(field["type"])
        generator = (
            "next_f64(&state)"
            if field_type in _FLOAT_TYPES
            else "next_i32(&state)"
        )
        initializers.append(
            f".{field['name']} = ({field_type}){generator}"
        )
    return "\n".join([
        f"    for (int case_index = 0; case_index < {cases}; case_index++) {{",
        f"        struct {item.name} value = {{ {', '.join(initializers)} }};",
        f"        {result_type} result = {function.name}(&value);",
        *_c_print_result(function.name, result_type, "result"),
        "    }",
    ])


def _rust_struct_cases(
    function: FunctionInfo,
    item: StructInfo,
    package: str,
    cases: int,
) -> str:
    result_type = _normalize_c_type(function.return_type)
    fields = []
    for field in item.fields:
        field_type = _normalize_c_type(field["type"])
        generator = (
            "next_f64(&mut state)"
            if field_type in _FLOAT_TYPES
            else "next_i32(&mut state)"
        )
        fields.append(
            f"{rust_identifier(field['name'])}: "
            f"{generator} as {rust_type(field_type)}"
        )
    return "\n".join([
        f"    for _case_index in 0..{cases} {{",
        f"        let value = {package}::{item.name} {{ {', '.join(fields)} }};",
        f"        let result = {package}::{rust_identifier(function.name)}(&value);",
        *_rust_print_result(function.name, result_type, "result"),
        "    }",
    ])


def _c_print_result(
    name: str,
    result_type: str,
    expression: str,
) -> list[str]:
    if result_type == "float":
        return [
            "        uint32_t bits = 0;",
            f"        memcpy(&bits, &{expression}, sizeof(bits));",
            f'        printf("{name}:%08x\\n", bits);',
        ]
    if result_type == "double":
        return [
            "        uint64_t bits = 0;",
            f"        memcpy(&bits, &{expression}, sizeof(bits));",
            f'        printf("{name}:%016llx\\n", '
            "(unsigned long long)bits);",
        ]
    if "unsigned" in result_type or result_type == "size_t":
        return [
            f'        printf("{name}:%llu\\n", '
            f"(unsigned long long)({expression}));"
        ]
    return [
        f'        printf("{name}:%lld\\n", '
        f"(long long)({expression}));"
    ]


def _rust_print_result(
    name: str,
    result_type: str,
    expression: str,
) -> list[str]:
    if result_type == "float":
        return [
            f'        println!("{name}:{{:08x}}", {expression}.to_bits());'
        ]
    if result_type == "double":
        return [
            f'        println!("{name}:{{:016x}}", {expression}.to_bits());'
        ]
    if "unsigned" in result_type or result_type == "size_t":
        return [
            f'        println!("{name}:{{}}", {expression} as u128);'
        ]
    return [
        f'        println!("{name}:{{}}", {expression} as i128);'
    ]


def _must_be_nonzero(function: FunctionInfo, parameter: str) -> bool:
    escaped = re.escape(parameter)
    return re.search(rf"(?:/|%)\s*{escaped}\b", function.body) is not None


def _is_boolean(function: FunctionInfo) -> bool:
    return any(item.idiom_type == "boolean_int" for item in function.idioms)
