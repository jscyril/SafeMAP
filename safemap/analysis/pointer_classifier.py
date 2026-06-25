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
        arithmetic = bool(re.search(rf"\b{name}\s*(?:\+\+|--|\+|-)", body))
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
        if length and indexed:
            kind = "pointer_length_array"
            evidence = f"{parameter.name} is indexed and paired with {length}"
            confidence = 0.94
        elif checks_null:
            kind = "nullable_pointer"
            evidence = f"{parameter.name} is explicitly checked for null"
            confidence = 0.95
        elif written:
            kind = "output_parameter" if not indexed else "mutable_borrow"
            evidence = f"{parameter.name} is written through"
            confidence = 0.88
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

