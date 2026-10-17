"""Per-unit differential testing against a sanitized C oracle.

Inputs are generated once (seeded) and embedded as literal tables in both a C
harness, which includes the original translation unit and runs under ASan and
UBSan, and a Rust harness linked against the generated crate. Each unit is
compared case by case. Inputs on which the C oracle triggers a sanitizer abort
have no defined C behavior; they are excluded and counted, and a unit needs a
minimum fraction of defined inputs to be accepted.
"""
from __future__ import annotations

import os
import random
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..models import FunctionInfo, JsonModel, MigrationPlan, StructInfo
from ..process import run_command
from ..translation.signature_generator import (
    C_TO_RUST,
    QUALIFIERS,
    mappable_struct_names,
    projectable_struct_names,
    rust_identifier,
    split_pointer,
    struct_field_rust_type,
)

GENERATOR = "safemap-unit-harness-v1"
MIN_DEFINED_FRACTION = 0.5
SCALARS = {"i8", "u8", "i16", "u16", "i32", "u32", "i64", "u64", "usize", "f32", "f64", "bool"}
STRING_POOL = ["", "a", "ab", "abc", "A", "Z", "0", "123", "-4.5", "true", "null",
               "key=value", "a,b", "\"q\"", "x y", "[s]", "#c", ";", "\\", "\t", "\n"]
STRING_ALPHABET = "abcxyzABCXYZ0123456789 _-.,;=#[]\"\\\t\n"


@dataclass
class UnitBehavior(JsonModel):
    unit_id: str
    function: str
    status: str
    reason: str | None = None
    cases: int = 0
    defined_cases: int = 0
    undefined_cases: int = 0
    matched: int = 0
    mismatched: int = 0
    first_mismatch: dict | None = None
    generator: str = GENERATOR
    seed: int = 0


@dataclass
class _Slot:
    """One piece of the C/Rust interface and how the harness drives it."""
    name: str
    kind: str                # scalar | str | slice | array | struct | length | out
    rust: str = ""           # element/scalar/struct Rust type
    c_type: str = ""         # C element/scalar type for declarations
    mutable: bool = False
    nullable: bool = False
    by_ref: bool = False
    length: int | None = None
    struct: StructInfo | None = None
    in_rust: bool = True


@dataclass
class _UnitSpec:
    plan: MigrationPlan
    function: FunctionInfo
    c_args: list[_Slot]
    rust_params: list[_Slot]
    returns: str
    outs: list[_Slot] = field(default_factory=list)
    values: list[dict] = field(default_factory=list)
    structs: dict[str, StructInfo] = field(default_factory=dict)
    constants: list[int] = field(default_factory=list)


def validate_units(
    c_source: Path,
    rust_root: Path,
    work: Path,
    functions: list[FunctionInfo],
    plans: list[MigrationPlan],
    structs: list[StructInfo],
    unit_ids: list[str],
    *,
    cases: int = 1000,
    seed: int = 0,
    include_dirs: list[str] | None = None,
) -> dict[str, UnitBehavior]:
    by_name = {item.name: item for item in functions}
    struct_by_name = {item.name: item for item in structs}
    mappable = projectable_struct_names(structs)
    macros = _macro_table(c_source)
    results: dict[str, UnitBehavior] = {}
    specs: list[_UnitSpec] = []
    for plan in plans:
        if plan.unit_id not in unit_ids:
            continue
        spec, reason = _spec(plan, by_name[plan.function], struct_by_name, mappable)
        if spec is None:
            results[plan.unit_id] = UnitBehavior(
                plan.unit_id, plan.function, "not_harnessable", reason, seed=seed,
            )
            continue
        rng = random.Random(f"{seed}:{plan.function}")
        spec.constants = _mined_constants(
            spec.function.body + "\n" + _referenced_macros(spec.function.body, macros)
        )
        spec.values = [_case_values(spec, rng) for _ in range(cases)]
        specs.append(spec)
    work.mkdir(parents=True, exist_ok=True)
    c_binary, specs = _build_c(c_source, work, specs, results, include_dirs or [], seed)
    rust_binary, specs = _build_rust(rust_root, work, specs, results, seed)
    for index, spec in enumerate(specs):
        results[spec.plan.unit_id] = _compare(index, spec, c_binary, rust_binary, work, seed)
    return results


# ---------------------------------------------------------------- planning

def _spec(plan, function, struct_by_name, mappable) -> tuple[_UnitSpec | None, str | None]:
    params, returns = _parse_signature(plan.target_signature)
    if params is None:
        return None, "Target signature could not be parsed"
    rust_by_name = {name: kind for name, kind in params}
    outputs = {
        fact.variable for fact in function.pointer_facts
        if fact.usage_kind == "output_parameter"
    }
    c_args: list[_Slot] = []
    rust_slots: dict[str, _Slot] = {}
    outs: list[_Slot] = []
    slices: list[_Slot] = []
    for parameter in function.parameters:
        base, depth, _ = split_pointer(parameter.c_type)
        if parameter.array_length is not None and depth == 0:
            depth = 1
        name = rust_identifier(parameter.name)
        rust = rust_by_name.get(name)
        if rust is None:
            if parameter.name in outputs and depth == 1:
                scalar = _c_scalar(base)
                if scalar is None:
                    return None, f"Moved output `{parameter.name}` is not scalar"
                slot = _Slot(parameter.name, "out", scalar, base, in_rust=False)
                outs.append(slot)
                c_args.append(slot)
                continue
            if depth == 0 and _c_scalar(base) not in (None, "bool", "f32", "f64"):
                c_args.append(_Slot(parameter.name, "length", _c_scalar(base), base, in_rust=False))
                continue
            return None, f"C parameter `{parameter.name}` has no Rust counterpart"
        slot = _slot_for(parameter.name, rust, base, struct_by_name, mappable)
        if slot is None:
            return None, f"Parameter type `{rust}` is not harnessable"
        rust_slots[name] = slot
        if slot.kind == "slice":
            slices.append(slot)
        c_args.append(slot)
    if set(rust_slots) != set(rust_by_name):
        return None, "Rust parameters do not correspond to C parameters"
    if any(slot.kind == "length" for slot in c_args) and not slices:
        return None, "Length parameter without a slice"
    spec = _UnitSpec(
        plan, function, c_args, [rust_slots[name] for name, _ in params], returns, outs,
        structs={name: struct_by_name[name] for name in mappable if name in struct_by_name},
    )
    reason = _return_issue(spec, struct_by_name, mappable_struct_names(list(struct_by_name.values())))
    return (None, reason) if reason else (spec, None)


def _parse_signature(signature: str):
    head = re.match(r"\s*pub fn\s+(?:r#)?\w+\s*\(", signature)
    if not head:
        return None, None
    depth, index = 1, head.end()
    while index < len(signature) and depth:
        depth += {"(": 1, ")": -1}.get(signature[index], 0)
        index += 1
    if depth:
        return None, None
    inner = signature[head.end():index - 1]
    tail = signature[index:].strip()
    returns = tail.removeprefix("->").strip() if tail.startswith("->") else "()"
    params = []
    depth, current = 0, ""
    for char in inner:
        if char in "<([":
            depth += 1
        elif char in ">)]":
            depth -= 1
        if char == "," and depth == 0:
            params.append(current)
            current = ""
        else:
            current += char
    if current.strip():
        params.append(current)
    parsed = []
    for item in params:
        name, _, kind = item.partition(":")
        parsed.append((name.strip(), " ".join(kind.split())))
    return parsed, returns or "()"


def _slot_for(name, rust, c_base, struct_by_name, mappable) -> _Slot | None:
    nullable = False
    inner = re.fullmatch(r"Option<(.+)>", rust)
    if inner:
        nullable, rust = True, inner.group(1)
    if rust == "&str":
        return _Slot(name, "str", "str", "char", nullable=nullable)
    slice = re.fullmatch(r"&(mut )?\[(\w+)\]", rust)
    if slice and slice.group(2) in SCALARS and not nullable:
        return _Slot(name, "slice", slice.group(2), _c_decl_base(c_base, slice.group(2)),
                     mutable=bool(slice.group(1)))
    array = re.fullmatch(r"&(mut )?\[(\w+); (\d+)\]", rust)
    if array and array.group(2) in SCALARS and not nullable:
        return _Slot(name, "array", array.group(2), _c_decl_base(c_base, array.group(2)),
                     mutable=bool(array.group(1)), length=int(array.group(3)))
    reference = re.fullmatch(r"&(mut )?(\w+)", rust)
    by_ref, mutable, type_name = False, False, rust
    if reference:
        by_ref, mutable, type_name = True, bool(reference.group(1)), reference.group(2)
    elif nullable:
        return None
    if type_name in SCALARS:
        return _Slot(name, "scalar", type_name, c_base, mutable, nullable, by_ref)
    if type_name in mappable and type_name in struct_by_name:
        return _Slot(name, "struct", type_name, f"struct {type_name}", mutable, nullable,
                     by_ref, struct=struct_by_name[type_name])
    return None


def _return_issue(spec: _UnitSpec, struct_by_name, mappable) -> str | None:
    returns = spec.returns
    result = re.fullmatch(r"Result<(.+), i32>", returns)
    if result:
        if spec.function.return_type.strip() not in {"int", "long", "short", "signed char"}:
            return "Result return over a non-integer C return"
        inner = result.group(1)
        if not spec.outs:
            return None if inner in SCALARS else f"Result payload `{inner}` is not harnessable"
        return None
    if returns.startswith("(") and returns != "()":
        return None
    if returns in SCALARS or returns in {"()", "Option<String>"}:
        return None
    box = re.fullmatch(r"Box<(\w+)>", returns)
    if box and (box.group(1) in SCALARS or box.group(1) in mappable):
        return None
    if returns in mappable:
        return None
    return f"Return type `{returns}` is not harnessable"


def _scalar_fields(struct: StructInfo) -> list[dict]:
    return [item for item in struct.fields if struct_field_rust_type(item["type"]) is not None]


def _c_scalar(base: str) -> str | None:
    base = " ".join(QUALIFIERS.sub(" ", base).split())
    if base.startswith("enum "):
        return "i32"
    mapped = C_TO_RUST.get(base)
    return mapped if mapped in SCALARS else None


def _c_decl_base(c_base: str, rust: str) -> str:
    return c_base if c_base and c_base != "void" else rust


# ---------------------------------------------------------------- inputs

def _case_values(spec: _UnitSpec, rng: random.Random) -> dict:
    values: dict = {}
    slice_length = rng.choice([0, 1, 2, 3, 4, 5, 8, 12]) if rng.random() < 0.9 else rng.randint(0, 24)
    for slot in spec.c_args:
        if slot.kind == "length":
            values[slot.name] = slice_length
        elif slot.kind == "out":
            values[slot.name] = 0
        elif slot.nullable and rng.random() < 0.2:
            values[slot.name] = None
        elif slot.kind == "scalar":
            values[slot.name] = _scalar_value(slot.rust, rng, spec.constants)
        elif slot.kind == "str":
            values[slot.name] = _string_value(rng)
        elif slot.kind in {"slice", "array"}:
            count = slot.length if slot.kind == "array" else max(slice_length, 1 if slot.mutable else 0)
            if slot.rust in {"u8", "i8"} and not slot.mutable:
                text = _string_value(rng).encode()[: count or None]
                values[slot.name] = list(text) if slot.kind == "slice" else (list(text) + [0] * count)[:count]
            elif slot.rust in {"u8", "i8"}:
                values[slot.name] = [rng.choice([0x2a, 0x41, 0x7a, 0x00]) for _ in range(count)]
            else:
                values[slot.name] = [_scalar_value(slot.rust, rng, spec.constants) for _ in range(count)]
        elif slot.kind == "struct":
            values[slot.name] = {
                item["name"]: _field_value(item["type"], rng, spec.constants)
                for item in _scalar_fields(slot.struct)
            }
    _share_equal_values(spec, values, rng)
    # all consumed lengths describe the slices actually passed
    for slot in spec.c_args:
        if slot.kind == "slice" and values.get(slot.name) is not None:
            for other in spec.c_args:
                if other.kind == "length":
                    values[other.name] = len(values[slot.name])
            break
    return values


def _mined_constants(body: str) -> list[int]:
    """Integer literals in the C body and their neighbours (boundary inputs)."""
    found = set()
    for match in re.finditer(r"(?<![\w.])(0[xX][0-9a-fA-F]+|\d+)(?![\w.])", body):
        value = int(match.group(1), 0)
        if value <= 1 << 20:
            found.update({value - 1, value, value + 1, -value})
    return sorted(found)


def _macro_table(c_source: Path) -> dict[str, str]:
    """Object-like macro bodies from the source file and its sibling headers."""
    table: dict[str, str] = {}
    for path in [c_source, *sorted(c_source.parent.glob("*.h"))]:
        text = re.sub(r"\\\n", " ", path.read_text(encoding="utf-8", errors="replace"))
        for match in re.finditer(r"^[ \t]*#[ \t]*define[ \t]+(\w+)[ \t]+(.+)$", text, re.MULTILINE):
            table.setdefault(match.group(1), match.group(2))
    return table


def _referenced_macros(body: str, macros: dict[str, str]) -> str:
    """Bodies of macros the function uses (two levels), for constant mining."""
    seen, frontier, parts = set(), set(re.findall(r"\b[A-Za-z_]\w*\b", body)), []
    for _ in range(2):
        found = set()
        for name in frontier - seen:
            seen.add(name)
            if name in macros:
                parts.append(macros[name])
                found.update(re.findall(r"\b[A-Za-z_]\w*\b", macros[name]))
        frontier = found
    text = "\n".join(parts)
    # (1 << 3) style flag macros: include the shifted value itself.
    for left, right in re.findall(r"\b(\d+)\s*<<\s*(\d+)\b", text):
        if int(right) < 31:
            text += f"\n{int(left) << int(right)}"
    return text


def _scalar_value(rust: str, rng: random.Random, constants: list[int] | None = None):
    if constants and rust not in {"bool", "f32", "f64"} and rng.random() < 0.25:
        low, high = _integer_range(rust)
        usable = [item for item in constants if low <= item <= high]
        if usable:
            return rng.choice(usable)
    if rust == "bool":
        return rng.random() < 0.5
    if rust in {"f32", "f64"}:
        if rng.random() < 0.3:
            return rng.choice([0.0, -0.0, 1.0, -1.0, 0.5, 2.5, -3.25, 100.0, 1e-3])
        return round(rng.uniform(-1000, 1000), 3)
    if rust in {"u8", "i8"}:
        low, high = (0, 255) if rust == "u8" else (-128, 127)
        if rng.random() < 0.6:
            return rng.choice([ord(c) for c in "aAzZ09 ,;=\"#\n\t\\"])
        return rng.randint(low, high)
    if rust.startswith("u") or rust == "usize":
        return rng.choice([0, 1, 2]) if rng.random() < 0.3 else rng.randint(0, 64)
    return rng.choice([0, 1, -1]) if rng.random() < 0.3 else rng.randint(-100, 100)


def _integer_range(rust: str) -> tuple[int, int]:
    bits = {"i8": 8, "u8": 8, "i16": 16, "u16": 16, "i32": 32, "u32": 32}.get(rust, 64)
    if rust.startswith("u") or rust == "usize":
        return 0, min(2 ** bits - 1, 1 << 20)
    return -(2 ** (bits - 1)), 2 ** (bits - 1) - 1


def _string_value(rng: random.Random) -> str:
    if rng.random() < 0.4:
        return rng.choice(STRING_POOL)
    return "".join(rng.choice(STRING_ALPHABET) for _ in range(rng.randint(0, 12)))


def _field_value(c_type: str, rng: random.Random, constants: list[int] | None = None):
    rust = struct_field_rust_type(c_type)
    array = re.fullmatch(r"\[(\w+); (\d+)\]", rust or "")
    if array:
        return [_scalar_value(array.group(1), rng, constants) for _ in range(int(array.group(2)))]
    return _scalar_value(rust, rng, constants)


def _share_equal_values(spec: _UnitSpec, values: dict, rng: random.Random) -> None:
    """Sometimes give same-typed inputs equal values (equal strings, equal
    scalars): random generation alone almost never reaches those paths."""
    groups: dict[tuple, list[_Slot]] = {}
    for slot in spec.c_args:
        if slot.kind in {"scalar", "str", "slice", "array"} and not slot.mutable:
            groups.setdefault((slot.kind, slot.rust, slot.length), []).append(slot)
    for slots in groups.values():
        if len(slots) > 1 and rng.random() < 0.2:
            source = values.get(slots[0].name)
            for slot in slots[1:]:
                if source is None or not slot.nullable or rng.random() < 0.8:
                    values[slot.name] = list(source) if isinstance(source, list) else source


# ---------------------------------------------------------------- literals

def _c_literal(value, rust: str) -> str:
    if rust == "bool":
        return "1" if value else "0"
    if rust in {"f32", "f64"}:
        text = repr(float(value))
        text = "-0.0" if text == "-0.0" else text
        return text + ("f" if rust == "f32" else "")
    if rust in {"u64", "usize"}:
        return f"{value}ULL"
    if rust == "i64":
        return f"{value}LL"
    return str(value)


def _rust_literal(value, rust: str) -> str:
    if rust == "bool":
        return "true" if value else "false"
    if rust in {"f32", "f64"}:
        text = repr(float(value))
        return f"{text}_{rust}"
    return f"{value}_{rust}" if value >= 0 else f"({value}_{rust})"


def _c_string(value: str | bytes) -> str:
    data = value.encode() if isinstance(value, str) else bytes(value)
    return '"' + "".join(
        chr(b) if 32 <= b < 127 and chr(b) not in '"\\?' else f"\\{b:03o}" for b in data
    ) + '"'


def _rust_string(value: str) -> str:
    return '"' + "".join(
        c if 32 <= ord(c) < 127 and c not in '"\\' else f"\\u{{{ord(c):x}}}" for c in value
    ) + '"'


# ---------------------------------------------------------------- C harness

C_PRELUDE = r"""
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
static void sm_i(long long v) { printf(" %lld", v); }
static void sm_u(unsigned long long v) { printf(" %llu", v); }
static void sm_f64(double v) { if (v != v) { printf(" nan"); } else { uint64_t b; memcpy(&b, &v, 8); printf(" %016llx", (unsigned long long)b); } }
static void sm_f32(float v) { if (v != v) { printf(" nan"); } else { uint32_t b; memcpy(&b, &v, 4); printf(" %08x", (unsigned)b); } }
static void sm_s(const char *s) { if (!s) { printf(" NULL"); return; } printf(" \""); for (const unsigned char *p = (const unsigned char *)s; *p; p++) { if (*p >= 32 && *p < 127 && *p != '"' && *p != '\\') putchar(*p); else printf("\\x%02x", *p); } printf("\""); }
static void sm_end(int k) { printf(" |%d\n", k); fflush(stdout); }
"""


def _c_print(expr: str, rust: str) -> str:
    if rust == "bool":
        return f"sm_i(({expr}) != 0);"
    if rust == "f64":
        return f"sm_f64({expr});"
    if rust == "f32":
        return f"sm_f32({expr});"
    if rust == "i8":
        return f"sm_i((signed char)({expr}));"
    if rust == "u8":
        return f"sm_u((unsigned char)({expr}));"
    if rust.startswith("u") or rust == "usize":
        return f"sm_u({expr});"
    return f"sm_i({expr});"


def _c_struct_print(expr: str, struct: StructInfo) -> list[str]:
    lines = []
    for item in _scalar_fields(struct):
        rust = struct_field_rust_type(item["type"])
        array = re.fullmatch(r"\[(\w+); (\d+)\]", rust)
        if array:
            lines.append(
                f"for (int sm_j = 0; sm_j < {array.group(2)}; sm_j++) "
                + _c_print(f"{expr}.{item['name']}[sm_j]", array.group(1))
            )
        else:
            lines.append(_c_print(f"{expr}.{item['name']}", rust))
    return lines


def _c_unit(index: int, spec: _UnitSpec) -> str:
    fn = spec.function.name
    lines = [f"static void sm_unit_{index}(int k) {{", "    switch (k) {"]
    for k, values in enumerate(spec.values):
        body, args, after = [], [], []
        for slot in spec.c_args:
            value = values.get(slot.name)
            var = f"sm_{slot.name}"
            if slot.kind == "length":
                args.append(_c_literal(value, slot.rust))
            elif slot.kind == "out":
                body.append(f"{slot.c_type} {var} = 0;")
                args.append(f"&{var}")
            elif value is None:
                args.append("NULL")
                if slot.mutable or slot.kind == "struct":
                    after.append('printf(" -");')
            elif slot.kind == "str":
                # A distinct array per argument: merged literals would alias.
                body.append(f"char {var}[] = {_c_string(value)};")
                args.append(var)
            elif slot.kind == "scalar":
                if slot.by_ref:
                    body.append(f"{slot.c_type} {var} = {_c_literal(value, slot.rust)};")
                    args.append(f"&{var}")
                    if slot.mutable:
                        after.append(_c_print(var, slot.rust))
                else:
                    args.append(_c_literal(value, slot.rust))
            elif slot.kind in {"slice", "array"}:
                items = ", ".join(_c_literal(item, slot.rust) for item in value) or "0"
                body.append(f"{slot.c_type} {var}[{len(value) + 1}] = {{{items}}};")
                body.append(f"{var}[{len(value)}] = 0;")
                args.append(var)
                if slot.mutable:
                    after.append(
                        f"for (int sm_j = 0; sm_j < {len(value)}; sm_j++) "
                        + _c_print(f"{var}[sm_j]", slot.rust)
                    )
            elif slot.kind == "struct":
                body.append(f"struct {slot.rust} {var};")
                body.append(f"memset(&{var}, 0, sizeof {var});")
                for item in _scalar_fields(slot.struct):
                    field_value = value[item["name"]]
                    rust = struct_field_rust_type(item["type"])
                    if isinstance(field_value, list):
                        element = rust.split(";")[0].strip("[ ")
                        for j, entry in enumerate(field_value):
                            body.append(f"{var}.{item['name']}[{j}] = {_c_literal(entry, element)};")
                    else:
                        body.append(f"{var}.{item['name']} = {_c_literal(field_value, rust)};")
                args.append(f"&{var}" if slot.by_ref else var)
                if slot.mutable:
                    after.extend(_c_struct_print(var, slot.struct))
        call = f"{fn}({', '.join(args)})"
        body.extend(_c_return(spec, call))
        body.extend(after)
        lines.append(f"    case {k}: {{ " + " ".join(body) + f" sm_end({k}); break; }}")
    lines += ["    }", "}"]
    return "\n".join(lines)


def _c_return(spec: _UnitSpec, call: str) -> list[str]:
    returns = spec.returns
    c_return = spec.function.return_type
    outs = [_c_print(f"sm_{slot.name}", slot.rust) for slot in spec.outs]
    if returns == "()" or (c_return.strip() == "void" and spec.outs):
        return [f"{call};", *outs]
    if returns.startswith("Result<"):
        if spec.outs:
            return [f"int sm_r = (int){call};",
                    "if (sm_r == 0) { printf(\" ok\"); " + " ".join(outs) + " } else { printf(\" err\"); sm_i(sm_r); }"]
        return [f"long long sm_r = {call};", "sm_i(sm_r);"]
    if returns.startswith("("):
        first = _split_tuple(returns)[0] if c_return.strip() != "void" else None
        lines = [f"{c_return} sm_r = {call};", _c_print("sm_r", first)] if first else [f"{call};"]
        return [*lines, *outs]
    if returns == "Option<String>":
        return [f"sm_s((const char *){call});"]
    box = re.fullmatch(r"Box<(\w+)>", returns)
    if box:
        inner = box.group(1)
        if inner in SCALARS:
            return [f"{c_return} sm_r = {call};", "if (!sm_r) { printf(\" NULL\"); } else { " + _c_print("*sm_r", inner) + " }"]
        struct = _struct_of(spec, inner)
        return [f"{c_return} sm_r = {call};", "if (!sm_r) { printf(\" NULL\"); } else { "
                + " ".join(_c_struct_print("(*sm_r)", struct)) + " }"]
    if returns in SCALARS:
        return [f"{c_return} sm_r = {call};", _c_print("sm_r", returns)]
    struct = _struct_of(spec, returns)
    return [f"struct {returns} sm_r = {call};", *_c_struct_print("sm_r", struct)]


def _struct_of(spec: _UnitSpec, name: str) -> StructInfo:
    return spec.structs[name]


def _split_tuple(text: str) -> list[str]:
    return [item.strip() for item in text.strip("()").split(",") if item.strip()]


def _c_main(specs: list[_UnitSpec]) -> str:
    cases = "\n".join(
        f"    if (u == {i}) {{ for (int k = start; k < {len(spec.values)}; k++) sm_unit_{i}(k); return 0; }}"
        for i, spec in enumerate(specs)
    )
    return (
        "int main(int argc, char **argv) {\n"
        "    if (argc < 3) return 2;\n"
        "    int u = atoi(argv[1]); int start = atoi(argv[2]);\n"
        f"{cases}\n    return 3;\n}}\n"
    )


def _build_c(c_source, work, specs, results, include_dirs, seed):
    while True:
        include = str(c_source.resolve()).replace("\\", "\\\\").replace('"', '\\"')
        parts = [C_PRELUDE, "#define main sm_original_main", f'#include "{include}"', "#undef main"]
        ranges = []
        for index, spec in enumerate(specs):
            start = sum(part.count("\n") + 1 for part in parts)
            parts.append(_c_unit(index, spec))
            ranges.append((start, sum(part.count("\n") + 1 for part in parts), spec))
        parts.append(_c_main(specs))
        harness = work / "c_harness.c"
        harness.write_text("\n".join(parts), encoding="utf-8")
        binary = work / "c_harness"
        command = [
            # Same leniency as the C oracle build: legacy sources use
            # implicit int and implicit declarations.
            "clang", "-O0", "-g", "-w", "-Wno-error=implicit-int",
            "-Wno-error=implicit-function-declaration", "-fsanitize=address,undefined",
            "-fno-sanitize-recover=all", "-fno-omit-frame-pointer",
            *[f"-I{item}" for item in [str(c_source.parent), *include_dirs]],
            str(harness), "-o", str(binary), "-lm",
        ]
        built = run_command(command, work, timeout=900)
        if built.status == "passed":
            return binary, specs
        bad = set()
        for match in re.finditer(r"c_harness\.c:(\d+):\d+: error", built.stderr):
            line = int(match.group(1))
            for start, end, spec in ranges:
                if start <= line <= end:
                    bad.add(spec.plan.unit_id)
        if not bad:
            for spec in specs:
                results[spec.plan.unit_id] = UnitBehavior(
                    spec.plan.unit_id, spec.function.name, "harness_build_failed",
                    "C oracle harness failed to build: " + built.stderr[-1500:], seed=seed,
                )
            return binary, []
        for spec in specs:
            if spec.plan.unit_id in bad:
                results[spec.plan.unit_id] = UnitBehavior(
                    spec.plan.unit_id, spec.function.name, "harness_build_failed",
                    "C oracle harness for this unit failed to build", seed=seed,
                )
        specs = [spec for spec in specs if spec.plan.unit_id not in bad]


# ---------------------------------------------------------------- Rust harness

RUST_PRELUDE = r"""
#![allow(unused_mut, unused_variables, unused_unsafe, non_snake_case, unused_parens, clippy::all)]
use std::fmt::Write as _;
fn sm_i(o: &mut String, v: i128) { let _ = write!(o, " {}", v); }
fn sm_f64(o: &mut String, v: f64) { if v.is_nan() { o.push_str(" nan"); } else { let _ = write!(o, " {:016x}", v.to_bits()); } }
fn sm_f32(o: &mut String, v: f32) { if v.is_nan() { o.push_str(" nan"); } else { let _ = write!(o, " {:08x}", v.to_bits()); } }
fn sm_s(o: &mut String, s: Option<&str>) {
    match s {
        None => o.push_str(" NULL"),
        Some(s) => {
            o.push_str(" \"");
            for b in s.bytes().take_while(|b| *b != 0) {
                if (32..127).contains(&b) && b != b'"' && b != b'\\' { o.push(b as char); } else { let _ = write!(o, "\\x{:02x}", b); }
            }
            o.push('"');
        }
    }
}
"""


def _rust_print(expr: str, rust: str) -> str:
    if rust == "bool":
        return f"sm_i(&mut o, ({expr}) as i128);"
    if rust == "f64":
        return f"sm_f64(&mut o, {expr});"
    if rust == "f32":
        return f"sm_f32(&mut o, {expr});"
    return f"sm_i(&mut o, ({expr}) as i128);"


def _rust_struct_print(expr: str, struct: StructInfo) -> list[str]:
    lines = []
    for item in _scalar_fields(struct):
        rust = struct_field_rust_type(item["type"])
        name = rust_identifier(item["name"])
        array = re.fullmatch(r"\[(\w+); (\d+)\]", rust)
        if array:
            lines.append(f"for sm_v in {expr}.{name}.iter() {{ {_rust_print('*sm_v', array.group(1))} }}")
        else:
            lines.append(_rust_print(f"{expr}.{name}", rust))
    return lines


def _rust_struct_literal(slot: _Slot, value: dict) -> str:
    fields = []
    for item in _scalar_fields(slot.struct):
        rust = struct_field_rust_type(item["type"])
        entry = value[item["name"]]
        if isinstance(entry, list):
            element = rust.split(";")[0].strip("[ ")
            text = "[" + ", ".join(_rust_literal(x, element) for x in entry) + "]"
        else:
            text = _rust_literal(entry, rust)
        fields.append(f"{rust_identifier(item['name'])}: {text}")
    return f"{slot.rust} {{ {', '.join(fields)} }}"


def _rust_unit(index: int, spec: _UnitSpec, crate: str) -> str:
    fn = f"{crate}::{rust_identifier(spec.function.name)}"
    lines = [
        f"pub fn sm_unit_{index}(k: usize) -> String {{",
        "    let mut o = String::new();",
        "    match k {",
    ]
    for k, values in enumerate(spec.values):
        body, args, after = [], [], []
        for slot in spec.rust_params:
            value = values.get(slot.name)
            var = f"sm_{slot.name}"
            if value is None and slot.nullable:
                args.append("None")
                if slot.mutable or slot.kind == "struct":
                    after.append('o.push_str(" -");')
                continue
            wrap = (lambda text: f"Some({text})") if slot.nullable else (lambda text: text)
            if slot.kind == "str":
                body.append(f"let {var}: String = String::from({_rust_string(value)});")
                args.append(wrap(f"{var}.as_str()"))
            elif slot.kind == "scalar":
                if slot.by_ref:
                    body.append(f"let mut {var}: {slot.rust} = {_rust_literal(value, slot.rust)};")
                    args.append(wrap(f"&mut {var}" if slot.mutable else f"&{var}"))
                    if slot.mutable:
                        after.append(_rust_print(var, slot.rust))
                else:
                    args.append(_rust_literal(value, slot.rust))
            elif slot.kind in {"slice", "array"}:
                items = ", ".join(_rust_literal(item, slot.rust) for item in value)
                kind = f"[{slot.rust}; {len(value)}]" if slot.kind == "array" else f"Vec<{slot.rust}>"
                literal = f"[{items}]" if slot.kind == "array" else f"vec![{items}]"
                body.append(f"let mut {var}: {kind} = {literal};")
                reference = f"&mut {var}" if slot.mutable else f"&{var}"
                args.append(reference if slot.kind == "array" else reference + "[..]")
                if slot.mutable:
                    after.append(f"for sm_v in {var}.iter() {{ {_rust_print('*sm_v', slot.rust)} }}")
            elif slot.kind == "struct":
                body.append(f"let mut {var} = {crate}::{_rust_struct_literal(slot, value)};")
                if slot.by_ref:
                    args.append(wrap(f"&mut {var}" if slot.mutable else f"&{var}"))
                else:
                    args.append(var)
                if slot.mutable:
                    after.extend(_rust_struct_print(var, slot.struct))
        call = f"{fn}({', '.join(args)})"
        body.extend(_rust_return(spec, call))
        body.extend(after)
        lines.append(f"        {k} => {{ " + " ".join(body) + " }")
    lines += ["        _ => {}", "    }", "    o", "}"]
    return "\n".join(lines)


def _rust_return(spec: _UnitSpec, call: str) -> list[str]:
    returns = spec.returns
    out_types = [slot.rust for slot in spec.outs]
    if returns == "()":
        return [f"{call};"]
    if returns.startswith("Result<"):
        if spec.outs:
            names = [f"sm_o{i}" for i in range(len(out_types))]
            pattern = names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"
            prints = " ".join(_rust_print(name, kind) for name, kind in zip(names, out_types))
            return [f"match {call} {{ Ok({pattern}) => {{ o.push_str(\" ok\"); {prints} }} "
                    "Err(sm_e) => { o.push_str(\" err\"); sm_i(&mut o, sm_e as i128); } }"]
        inner = re.fullmatch(r"Result<(.+), i32>", returns).group(1)
        return [f"match {call} {{ Ok(sm_v) => {{ {_rust_print('sm_v', inner)} }} "
                "Err(sm_e) => { sm_i(&mut o, sm_e as i128); } }"]
    if returns.startswith("("):
        kinds = _split_tuple(returns)
        names = [f"sm_t{i}" for i in range(len(kinds))]
        destructure = names[0] if len(names) == 1 else "(" + ", ".join(names) + ")"
        return [f"let {destructure} = {call};",
                *[_rust_print(name, kind) for name, kind in zip(names, kinds)]]
    if returns == "Option<String>":
        return [f"let sm_r = {call};", "sm_s(&mut o, sm_r.as_deref());"]
    box = re.fullmatch(r"Box<(\w+)>", returns)
    if box:
        inner = box.group(1)
        if inner in SCALARS:
            return [f"let sm_r = {call};", _rust_print("*sm_r", inner)]
        return [f"let sm_r = {call};", *_rust_struct_print("sm_r", _struct_of(spec, inner))]
    if returns in SCALARS:
        return [f"let sm_r = {call};", _rust_print("sm_r", returns)]
    return [f"let sm_r = {call};", *_rust_struct_print("sm_r", _struct_of(spec, returns))]


def _build_rust(rust_root, work, specs, results, seed):
    crate = _crate_name(rust_root)
    harness = work / "rust_harness"
    while True:
        source = harness / "src"
        source.mkdir(parents=True, exist_ok=True)
        for old in source.glob("u*.rs"):
            old.unlink()
        modules = []
        for index, spec in enumerate(specs):
            (source / f"u{index}.rs").write_text(
                "#![allow(unused_mut, unused_variables, unused_parens)]\nuse super::*;\n"
                + _rust_unit(index, spec, crate) + "\n",
                encoding="utf-8",
            )
            modules.append(f"mod u{index};")
        dispatch = "\n".join(
            f"        {i} => u{i}::sm_unit_{i}," for i in range(len(specs))
        )
        counts = ", ".join(str(len(spec.values)) for spec in specs)
        (source / "main.rs").write_text(
            RUST_PRELUDE + "\n" + "\n".join(modules) + "\n"
            "fn main() {\n"
            "    std::panic::set_hook(Box::new(|_| {}));\n"
            "    let args: Vec<String> = std::env::args().collect();\n"
            "    let u: usize = args[1].parse().unwrap();\n"
            f"    let counts: [usize; {len(specs)}] = [{counts}];\n"
            "    let run: fn(usize) -> String = match u {\n"
            f"{dispatch}\n        _ => std::process::exit(3),\n    }};\n"
            "    for k in 0..counts[u] {\n"
            "        let line = std::panic::catch_unwind(|| run(k)).unwrap_or_else(|_| \" PANIC\".to_string());\n"
            "        println!(\"{} |{}\", line, k);\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        (harness / "Cargo.toml").write_text(
            "[package]\nname = \"safemap_unit_harness\"\nversion = \"0.1.0\"\nedition = \"2021\"\n\n"
            f"[dependencies]\n{crate} = {{ path = \"{rust_root.resolve().as_posix()}\" }}\n",
            encoding="utf-8",
        )
        if not specs:
            return None, specs
        built = run_command(
            # Debug profile: Rust overflow checks stay on, so a translation that
            # relies on silent wraparound where C does not wrap is caught.
            ["cargo", "build", "--quiet", "--message-format=short"],
            harness, timeout=1800,
        )
        binary = harness / "target" / "debug" / "safemap_unit_harness"
        if built.status == "passed":
            return binary, specs
        bad = {int(match.group(1)) for match in re.finditer(r"src/u(\d+)\.rs:\d+:\d+: error", built.stderr)}
        if not bad:
            for spec in specs:
                results[spec.plan.unit_id] = UnitBehavior(
                    spec.plan.unit_id, spec.function.name, "harness_build_failed",
                    "Rust harness failed to build: " + built.stderr[-1500:], seed=seed,
                )
            return None, []
        for index in sorted(bad):
            spec = specs[index]
            results[spec.plan.unit_id] = UnitBehavior(
                spec.plan.unit_id, spec.function.name, "harness_build_failed",
                "Rust harness for this unit failed to build (interface mismatch)", seed=seed,
            )
        specs = [spec for i, spec in enumerate(specs) if i not in bad]


def _crate_name(rust_root: Path) -> str:
    text = (rust_root / "Cargo.toml").read_text(encoding="utf-8")
    match = re.search(r'^name\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1).replace("-", "_") if match else "crate"


# ---------------------------------------------------------------- compare

def _parse_lines(text: str) -> dict[int, str]:
    lines = {}
    for line in text.splitlines():
        body, sep, index = line.rpartition(" |")
        if sep and index.isdigit():
            lines[int(index)] = body.strip()
    return lines


def _compare(index, spec, c_binary, rust_binary, work, seed) -> UnitBehavior:
    total = len(spec.values)
    result = UnitBehavior(spec.plan.unit_id, spec.function.name, "failed", cases=total, seed=seed)
    env = dict(os.environ)
    env["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0:halt_on_error=1"
    env["UBSAN_OPTIONS"] = "halt_on_error=1:print_stacktrace=0"
    c_lines: dict[int, str] = {}
    undefined: list[int] = []
    start = 0
    while start < total:
        run = run_command([str(c_binary), str(index), str(start)], work, timeout=120, env=env)
        got = _parse_lines(run.stdout)
        c_lines.update(got)
        if run.status == "passed":
            break
        last = max([k for k in got if k >= start], default=start - 1)
        if run.reason and "Timed out" in run.reason:
            result.status, result.reason = "c_oracle_timeout", f"C oracle did not terminate at case {last + 1}"
            return result
        if "Sanitizer" in run.stderr or "runtime error:" in run.stderr:
            undefined.append(last + 1)
        else:
            # Defined termination (abort, exit, failed assert): Rust must panic.
            c_lines[last + 1] = "PANIC"
        start = last + 2
    result.undefined_cases = len(undefined)
    defined = [k for k in range(total) if k in c_lines]
    result.defined_cases = len(defined)
    if result.defined_cases < MIN_DEFINED_FRACTION * total:
        result.status = "insufficient_defined_inputs"
        result.reason = (
            f"C oracle had undefined behavior on {len(undefined)}/{total} inputs"
        )
        return result
    rust = run_command([str(rust_binary), str(index)], work, timeout=120)
    rust_lines = {key: value.strip() for key, value in _parse_lines(rust.stdout).items()}
    for k in defined:
        if rust_lines.get(k) == c_lines[k]:
            result.matched += 1
        else:
            result.mismatched += 1
            if result.first_mismatch is None:
                result.first_mismatch = {
                    "case": k,
                    "inputs": {key: _jsonable(value) for key, value in spec.values[k].items()},
                    "c": c_lines[k],
                    "rust": rust_lines.get(k, "<no output>"),
                }
    if result.mismatched == 0 and result.matched == result.defined_cases:
        result.status = "passed"
        result.reason = (
            f"{result.matched} defined inputs matched; "
            f"{result.undefined_cases} undefined-behavior inputs excluded"
        )
    else:
        result.reason = f"{result.mismatched}/{result.defined_cases} defined inputs differed"
    return result


def _jsonable(value):
    if isinstance(value, float) and value != value:
        return "nan"
    return value
