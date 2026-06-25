from __future__ import annotations

import re

from ..models import CAnalysis, EligibilityResult, FunctionInfo

SAFE_CATEGORIES = {
    "safe_translatable",
    "safe_translatable_with_api_change",
}

ELIGIBILITY_CATEGORIES = (
    "safe_translatable",
    "safe_translatable_with_api_change",
    "requires_safe_wrapper",
    "requires_manual_refactor",
    "unsafe_required",
    "unsupported",
)

UNSUPPORTED_PATTERNS = (
    ("union_usage", re.compile(r"\bunion\b")),
    ("function_pointer", re.compile(r"\(\s*\*\s*[A-Za-z_]\w*\s*\)\s*\(")),
    ("inline_assembly", re.compile(r"\b(?:asm|__asm__)\b")),
    ("volatile_access", re.compile(r"\bvolatile\b")),
    ("setjmp_longjmp", re.compile(r"\b(?:setjmp|longjmp)\s*\(")),
    ("pointer_integer_cast", re.compile(r"\(\s*(?:uintptr_t|intptr_t|size_t|long|int)\s*\)\s*[A-Za-z_]\w*")),
)

UNSAFE_REQUIRED_CALLS = {
    "memcpy", "memmove", "memset", "fopen", "fclose", "fread", "fwrite",
}

SUPPORTED_POINTER_KINDS = {
    "pointer_length_array",
    "output_parameter",
    "nullable_pointer",
    "owned_allocation",
    "manual_free",
    "input_borrow",
}

API_CHANGE_IDIOMS = {
    "pointer_length_array",
    "output_parameter",
    "nullable_pointer",
    "manual_allocation",
    "error_code_return",
    "c_string",
}


def classify_analysis(analysis: CAnalysis) -> list[EligibilityResult]:
    return [
        classify_function(function, f"unit_{index}")
        for index, function in enumerate(analysis.functions)
    ]


def classify_function(function: FunctionInfo, unit_id: str) -> EligibilityResult:
    unsupported = _unsupported_features(function)
    pointer_roles = _pointer_roles(function)
    reasons: list[str] = []

    if unsupported:
        category = "unsupported"
        reasons.append("Unsupported C construct detected")
    elif _requires_unsafe(function):
        category = "unsafe_required"
        reasons.append("Function depends on operations that normally require unsafe Rust or FFI")
    elif _has_unknown_pointer(function):
        category = "requires_manual_refactor"
        reasons.append("Pointer role, ownership, or aliasing could not be resolved statically")
    elif _has_complex_aliasing(function):
        category = "requires_manual_refactor"
        reasons.append("Multiple mutable pointer-like parameters create unresolved aliasing risk")
    elif any(item.idiom_type in API_CHANGE_IDIOMS for item in function.idioms):
        category = "safe_translatable_with_api_change"
        reasons.append("Safe translation is possible with a Rust-native API change")
    else:
        category = "safe_translatable"
        reasons.append("No unsupported constructs or unresolved pointer hazards detected")

    return EligibilityResult(
        unit_id=unit_id,
        function=function.name,
        category=category,
        reasons=reasons,
        unsupported_features=unsupported,
        pointer_roles=pointer_roles,
        eligible_for_safe_translation=category in SAFE_CATEGORIES,
    )


def _unsupported_features(function: FunctionInfo) -> list[str]:
    features = [
        name for name, pattern in UNSUPPORTED_PATTERNS
        if pattern.search(function.body)
    ]
    if any(item.usage_kind == "function_pointer" for item in function.pointer_facts):
        features.append("function_pointer")
    return sorted(set(features))


def _requires_unsafe(function: FunctionInfo) -> bool:
    if re.search(r"\bextern\b", function.body):
        return True
    return any(call in UNSAFE_REQUIRED_CALLS for call in function.calls)


def _has_unknown_pointer(function: FunctionInfo) -> bool:
    return any(
        item.usage_kind not in SUPPORTED_POINTER_KINDS
        or item.usage_kind in {"unknown_raw_pointer", "pointer_arithmetic"}
        for item in function.pointer_facts
    )


def _has_complex_aliasing(function: FunctionInfo) -> bool:
    mutable_pointers = [
        parameter.name for parameter in function.parameters
        if parameter.is_pointer and not parameter.is_const
    ]
    writes = sum(
        1 for name in mutable_pointers
        if re.search(rf"(?:\*\s*{re.escape(name)}|{re.escape(name)}\s*\[)", function.body)
    )
    return writes > 1


def _pointer_roles(function: FunctionInfo) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    for fact in function.pointer_facts:
        roles.setdefault(fact.variable, []).append(_normalize_role(fact.usage_kind))
    return {name: sorted(set(values)) for name, values in roles.items()}


def _normalize_role(kind: str) -> str:
    return {
        "pointer_length_array": "array_pointer",
        "output_parameter": "output_pointer",
        "input_borrow": "input_pointer",
        "mutable_borrow": "inout_pointer",
        "manual_free": "owned_allocation",
        "unknown_raw_pointer": "unknown_pointer",
    }.get(kind, kind)
