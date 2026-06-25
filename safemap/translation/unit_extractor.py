from __future__ import annotations

import re

from ..llm.response_parser import matching_brace


def find_rust_function(source: str, name: str) -> tuple[int, int, str]:
    pattern = re.compile(
        rf"(?:pub(?:\([^)]*\))?\s+)?(?:unsafe\s+)?"
        rf"(?:extern\s+\"C\"\s+)?fn\s+{re.escape(name)}\s*"
    )
    match = pattern.search(source)
    if not match:
        raise ValueError(f"Rust function not found: {name}")
    opening = source.find("{", match.end())
    if opening < 0:
        raise ValueError(f"Rust function has no body: {name}")
    closing = matching_brace(source, opening)
    if closing is None:
        raise ValueError(f"Rust function has unbalanced braces: {name}")
    return match.start(), closing + 1, source[match.start():closing + 1]

