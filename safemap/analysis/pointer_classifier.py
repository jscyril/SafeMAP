from __future__ import annotations

import re

from ..models import ParameterInfo, PointerFact


def classify_pointers(
    parameters: list[ParameterInfo],
    body: str,
) -> list[PointerFact]:
    facts: list[PointerFact] = []
    parameter_names = {item.name for item in parameters}
    for parameter in parameters:
        if not parameter.is_pointer:
            continue
        name = re.escape(parameter.name)
        checks_null = bool(re.search(
            rf"(?:{name}\s*==\s*(?:NULL|0)|!\s*{name}\b|(?:NULL|0)\s*==\s*{name})",
            body,
        ))
        written = bool(re.search(rf"\*\s*{name}\s*(?:[+\-*/]?=|\+\+|--)", body))
        indexed = bool(re.search(rf"\b{name}\s*\[", body))
        arithmetic = bool(re.search(
            rf"\b{name}\s*(?:\+\+|--|\+|-(?!>))",
            body,
        ))
        freed = bool(re.search(rf"\bfree\s*\(\s*{name}\s*\)", body))
        allocated = bool(re.search(
            rf"\b{name}\s*=\s*(?:\([^)]*\)\s*)?(?:malloc|calloc|realloc)\s*\(",
            body,
        ))
        length = next(
            (
                candidate.name
                for candidate in parameters
                if candidate.name != parameter.name
                and not candidate.is_pointer
                and re.search(r"(?:len|length|size|count|n)$", candidate.name, re.I)
                and re.search(rf"\b{re.escape(candidate.name)}\b", body)
            ),
            None,
        )
        string_cursor = (
            parameter.is_const
            and _is_char_pointer(parameter.c_type)
            and (arithmetic or indexed)
            and length is None
            and parameter.array_length is None
            and not _pointer_escapes(parameter.name, body)
        )
        if pointer_to_array_dims(parameter.c_type) is not None:
            if _pointer_escapes(parameter.name, body) or re.search(
                rf"\b{name}\s*(?:\+\+|--|[+-]\s*\w)", _body_only(body),
            ):
                kind = "unknown_raw_pointer"
                evidence = f"{parameter.name} points to an array but escapes or moves"
                confidence = 0.6
            else:
                kind = "array_reference"
                evidence = f"{parameter.name} points to a whole fixed-size array"
                confidence = 0.95
        elif parameter.array_length is not None and indexed:
            kind = "fixed_size_array"
            evidence = (
                f"{parameter.name} is declared with fixed extent "
                f"{parameter.array_length} and indexed"
            )
            confidence = 0.97
        elif length and indexed:
            kind = "pointer_length_array"
            evidence = f"{parameter.name} is indexed and paired with {length}"
            confidence = 0.94
        elif checks_null:
            kind = "nullable_pointer"
            evidence = f"{parameter.name} is explicitly checked for null"
            confidence = 0.95
        elif string_cursor:
            kind = "c_string_cursor"
            evidence = f"{parameter.name} is a read-only C string scanned by index or increment"
            confidence = 0.85
        elif written and not indexed:
            kind = "output_parameter"
            evidence = f"{parameter.name} is written through"
            confidence = 0.88
        elif written:
            kind = "array_pointer"
            evidence = f"{parameter.name} is indexed and written without an inferred length"
            confidence = 0.72
        elif indexed:
            kind = "array_pointer"
            evidence = f"{parameter.name} is indexed without an inferred length"
            confidence = 0.72
        elif arithmetic:
            kind = "unknown_raw_pointer"
            evidence = f"{parameter.name} participates in pointer arithmetic"
            confidence = 0.98
        elif freed or allocated:
            kind = "owned_allocation"
            evidence = f"{parameter.name} participates in manual allocation"
            confidence = 0.9
        elif parameter.is_const:
            kind = "input_borrow"
            evidence = f"{parameter.name} is a const pointer"
            confidence = 0.75
        elif _only_field_access(parameter.name, body):
            if _field_written(parameter.name, body):
                kind = "mutable_borrow"
                evidence = f"{parameter.name} is only used through `->` and a field is written"
            else:
                kind = "input_borrow"
                evidence = f"{parameter.name} is only read through `->`"
            confidence = 0.85
        else:
            kind = "unknown_raw_pointer"
            evidence = f"No decisive ownership evidence for {parameter.name}"
            confidence = 0.4
        facts.append(PointerFact(
            variable=parameter.name,
            pointer_type=parameter.c_type,
            usage_kind=kind,
            evidence=evidence,
            confidence=confidence,
        ))
        if freed:
            facts.append(PointerFact(
                variable=parameter.name,
                pointer_type=parameter.c_type,
                usage_kind="manual_free",
                evidence=f"free({parameter.name}) is called",
                confidence=0.99,
            ))
    for allocated_name in re.findall(
        r"\b([A-Za-z_]\w*)\s*=\s*(?:\([^)]*\)\s*)?(?:malloc|calloc|realloc)\s*\(",
        body,
    ):
        if allocated_name not in parameter_names:
            facts.append(PointerFact(
                variable=allocated_name,
                pointer_type="inferred pointer",
                usage_kind="owned_allocation",
                evidence=f"{allocated_name} receives a heap allocation",
                confidence=0.98,
            ))
    return facts


def _body_only(body: str) -> str:
    """The function body without its signature (parameters would count as uses)."""
    opening = body.find("{")
    return body[opening:] if opening >= 0 else body


def _only_field_access(name: str, body: str) -> bool:
    inner = _body_only(body)
    escaped = re.escape(name)
    if not re.search(rf"\b{escaped}\s*->", inner):
        return False
    rest = re.sub(rf"\b{escaped}\s*->\s*\w+", " ", inner)
    return re.search(rf"\b{escaped}\b", rest) is None


def _field_written(name: str, body: str) -> bool:
    escaped = re.escape(name)
    field = rf"\b{escaped}\s*->\s*\w+(?:\s*\[[^\]]*\]|\s*\.\s*\w+|\s*->\s*\w+)*"
    inner = _body_only(body)
    return bool(
        re.search(rf"{field}\s*(?:[+\-*/%&|^]|<<|>>)?=(?!=)", inner)
        or re.search(rf"{field}\s*(?:\+\+|--)", inner)
        or re.search(rf"(?:\+\+|--)\s*{field}", inner)
        or re.search(rf"&\s*{field}", inner)
    )


# Library functions that only read a `const char *` argument.
READ_ONLY_LIBC = {
    "strlen", "strcmp", "strncmp", "strchr", "strrchr", "strstr", "strspn",
    "strcspn", "strpbrk", "atoi", "atol", "atof", "strtol", "strtoul",
    "strtod", "printf", "puts", "fputs", "strcasecmp", "strncasecmp",
}
READ_KINDS = {"input_borrow", "c_string_cursor"}
WRITE_KINDS = {"mutable_borrow", "output_parameter"}


def resolve_passed_pointers(functions) -> None:
    """Give a pointer that is only passed on the role of the callee's parameter.

    A parameter left `unknown_raw_pointer` whose other uses are all `->` field
    accesses becomes a borrow when every call it is passed to takes it as a
    borrow; a write anywhere makes it mutable. Anything else (stored, returned,
    reassigned, passed where the callee needs an array or ownership) stays
    unknown. Iterates to a fixed point so chains of calls resolve.
    """
    by_name = {item.name: item for item in functions}
    changed = True
    while changed:
        changed = False
        for function in functions:
            for fact in function.pointer_facts:
                if fact.usage_kind != "unknown_raw_pointer":
                    continue
                resolved = _resolve(function, fact.variable, by_name)
                if resolved is None:
                    continue
                kind, evidence = resolved
                fact.usage_kind, fact.evidence, fact.confidence = kind, evidence, 0.8
                changed = True


def _resolve(function, name: str, by_name) -> tuple[str, str] | None:
    parameter = next((item for item in function.parameters if item.name == name), None)
    if parameter is None:
        return None
    inner = _strip_literals(_body_only(function.body))
    escaped = re.escape(name)
    sites = list(re.finditer(rf"(?<=[(,])\s*{escaped}\s*(?=[,)])", inner))
    if not sites:
        return None
    rest = re.sub(rf"\b{escaped}\s*->\s*\w+", " ", inner)
    rest = re.sub(rf"(?<=[(,])\s*{escaped}\s*(?=[,)])", " ", rest)
    if re.search(rf"\b{escaped}\b", rest):
        return None
    writes = _field_written(name, inner)
    callees = []
    for site in sites:
        call = _enclosing_call(inner, site.start())
        if call is None:
            return None
        callee, index = call
        if callee == function.name:
            continue
        target = by_name.get(callee)
        if target is None:
            if callee in READ_ONLY_LIBC and parameter.is_const:
                callees.append(callee)
                continue
            return None
        if index >= len(target.parameters):
            return None
        target_name = target.parameters[index].name
        kind = next(
            (item.usage_kind for item in target.pointer_facts if item.variable == target_name),
            None,
        )
        if kind in READ_KINDS or kind == "nullable_pointer" and target.parameters[index].is_const:
            callees.append(callee)
        elif kind in WRITE_KINDS or kind == "nullable_pointer":
            writes = True
            callees.append(callee)
        else:
            return None
    if not callees:
        return None
    kind = "mutable_borrow" if writes else "input_borrow"
    return kind, f"{name} is passed as a borrow to {', '.join(sorted(set(callees)))}"


def _strip_literals(source: str) -> str:
    source = re.sub(r"/\*.*?\*/", " ", source, flags=re.DOTALL)
    source = re.sub(r"//[^\n]*", " ", source)
    source = re.sub(r"'(?:\\.|[^'\\])'", "0", source)
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', source)


def _enclosing_call(body: str, position: int) -> tuple[str, int] | None:
    """Name of the call whose argument list contains `position`, and the index."""
    depth, commas = 0, 0
    for index in range(position - 1, -1, -1):
        char = body[index]
        if char in ")]":
            depth += 1
        elif char in "([":
            if depth:
                depth -= 1
                continue
            if char == "[":
                return None
            match = re.search(r"([A-Za-z_]\w*)\s*$", body[:index])
            if not match or match.group(1) in {"if", "while", "for", "switch", "return", "sizeof"}:
                return None
            return match.group(1), commas
        elif char == "," and depth == 0:
            commas += 1
        elif char in ";{}" and depth == 0:
            return None
    return None


def _is_char_pointer(c_type: str) -> bool:
    """Plain `char` only: `unsigned char`/`uint8_t` buffers are bytes, not text."""
    base = re.sub(r"\b(?:const|restrict|__restrict|volatile)\b", " ", c_type)
    return c_type.count("*") == 1 and " ".join(base.replace("*", " ").split()) == "char"


def pointer_to_array_dims(c_type: str) -> tuple[str, list[int]] | None:
    """`unsigned char (*)[4][4]` -> ("unsigned char", [4, 4])."""
    match = re.fullmatch(r"\s*(.+?)\s*\(\s*\*\s*\)\s*((?:\[\s*\d+\s*\])+)\s*", c_type)
    if not match:
        return None
    element = " ".join(re.sub(r"\b(?:const|volatile)\b", " ", match.group(1)).split())
    return element, [int(item) for item in re.findall(r"\d+", match.group(2))]


def _pointer_escapes(name: str, body: str) -> bool:
    """The pointer itself (not a character it reads) leaves the function."""
    inner = _strip_literals(_body_only(body))
    escaped = re.escape(name)
    return bool(
        # return s; / return s + 1;  (but not return s[0]; or return *s;)
        re.search(rf"\breturn\s+\(?\s*{escaped}\s*(?:[+\-;)])", inner)
        # stored into a field, through an output pointer, or into an array slot
        or re.search(rf"(?:->\s*\w+|\.\s*\w+|\]|\*\s*\w+)\s*=\s*\(?\s*{escaped}\s*[;+\-)]", inner)
    )
