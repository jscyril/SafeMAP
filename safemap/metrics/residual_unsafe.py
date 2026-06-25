from __future__ import annotations

import re
from pathlib import Path

from ..llm.response_parser import matching_brace


def classify_residual_unsafe(path: Path) -> list[dict]:
    files = [path] if path.is_file() else sorted(path.rglob("*.rs"))
    results = []
    for file in files:
        source = file.read_text(encoding="utf-8", errors="replace")
        for match in re.finditer(r"\bunsafe\s*\{", source):
            opening = source.find("{", match.start())
            closing = matching_brace(source, opening)
            if closing is None:
                continue
            block = source[match.start():closing + 1]
            category, reason = _classify(block)
            line = source.count("\n", 0, match.start()) + 1
            results.append({
                "location": f"{file}:{line}",
                "category": category,
                "reason": reason,
                "start_line": line,
                "end_line": source.count("\n", 0, closing) + 1,
            })
    return results


def _classify(block: str) -> tuple[str, str]:
    patterns = [
        ("inline_assembly", r"\b(?:asm|global_asm)!", "Inline assembly requires unsafe."),
        ("union_usage", r"\bunion\b|\.u(?:nion)?_", "Union field access remains unsafe."),
        ("ffi_boundary", r"\bextern\s+\"C\"|libc::", "The block crosses an FFI boundary."),
        ("pointer_arithmetic", r"\.(?:add|offset|sub)\s*\(", "Raw pointer arithmetic could not be bounded."),
        ("global_mutable_state", r"\bstatic\s+mut\b", "Mutable global state requires unsafe access."),
        ("manual_memory_layout", r"\b(?:transmute|from_raw_parts|from_raw)\b", "Manual layout or ownership conversion remains."),
        ("complex_aliasing", r"\*(?:const|mut)\b|as\s+\*(?:const|mut)", "Raw pointer aliasing could not be proven safe."),
    ]
    for category, pattern, reason in patterns:
        if re.search(pattern, block):
            return category, reason
    return "unknown", "No supported static pattern explains this unsafe block."

