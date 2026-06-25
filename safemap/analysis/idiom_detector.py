from __future__ import annotations

import re

from ..models import DetectedIdiom, FunctionInfo

PATTERN_RUST = {
    "pointer_length_array": "Use &[T] or &mut [T]",
    "output_parameter": "Return the value, preferably in Result",
    "nullable_pointer": "Use Option<&T> or Option<&mut T>",
    "manual_allocation": "Use Box<T> or Vec<T>",
    "error_code_return": "Use Result<T, ErrorCode>",
    "lock_unlock": "Use Mutex/RwLock guard RAII",
    "c_string": "Use CStr/CString at FFI boundaries or str/String internally",
    "struct_pointer": "Use a reference or owned struct",
}


def detect_idioms(function: FunctionInfo) -> list[DetectedIdiom]:
    idioms: list[DetectedIdiom] = []
    for fact in function.pointer_facts:
        idiom_type = fact.usage_kind
        if idiom_type in {"owned_allocation", "manual_free"}:
            idiom_type = "manual_allocation"
        if idiom_type not in PATTERN_RUST:
            continue
        idioms.append(_idiom(
            function, idiom_type, [fact.variable],
            PATTERN_RUST[idiom_type], fact.confidence, fact.evidence,
        ))
    output_params = [
        item.variable for item in function.pointer_facts
        if item.usage_kind == "output_parameter"
    ]
    if output_params and function.return_type.strip() in {
        "int", "long", "short", "signed int", "unsigned int",
    }:
        idioms.append(_idiom(
            function, "error_code_return", output_params,
            PATTERN_RUST["error_code_return"], 0.86,
            "Integer status return is combined with written output parameter",
        ))
    if (
        any(item.usage_kind == "nullable_pointer" for item in function.pointer_facts)
        and re.search(r"\breturn\s+-\s*\d+\s*;", function.body)
    ):
        idioms.append(_idiom(
            function, "error_code_return", [],
            PATTERN_RUST["error_code_return"], 0.82,
            "A negative sentinel is returned when a nullable pointer is absent",
        ))
    body = function.body
    if re.search(r"\b(?:malloc|calloc|realloc|free)\s*\(", body):
        idioms.append(_idiom(
            function, "manual_allocation", [],
            PATTERN_RUST["manual_allocation"], 0.98,
            "Manual allocation API is called",
        ))
    if (
        re.search(r"\b(?:pthread_mutex_lock|mutex_lock)\s*\(", body)
        and re.search(r"\b(?:pthread_mutex_unlock|mutex_unlock)\s*\(", body)
    ):
        idioms.append(_idiom(
            function, "lock_unlock", [],
            PATTERN_RUST["lock_unlock"], 0.95,
            "Matched lock and unlock calls",
        ))
    if re.search(r"\b(?:strlen|strcmp|strcpy|strncpy)\s*\(", body):
        idioms.append(_idiom(
            function, "c_string", [],
            PATTERN_RUST["c_string"], 0.8,
            "C string API is called",
        ))
    unique: dict[tuple[str, tuple[str, ...]], DetectedIdiom] = {}
    for item in idioms:
        unique[(item.idiom_type, tuple(item.variables))] = item
    return list(unique.values())


def _idiom(
    function: FunctionInfo,
    idiom_type: str,
    variables: list[str],
    suggested: str,
    confidence: float,
    evidence: str,
) -> DetectedIdiom:
    return DetectedIdiom(
        idiom_type=idiom_type,
        location=f"{function.file}:{function.start_line}",
        variables=variables,
        suggested_rust_pattern=suggested,
        confidence=confidence,
        evidence=evidence,
    )
