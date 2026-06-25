from __future__ import annotations

import re


def parse_function_response(response: str, expected_name: str) -> str:
    text = response.strip()
    fenced = re.fullmatch(r"```(?:rust)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    match = re.search(
        rf"(?:pub(?:\([^)]*\))?\s+)?(?:unsafe\s+)?fn\s+{re.escape(expected_name)}\s*"
        r"(?:<[^>{}]*>)?\s*\(",
        text,
    )
    if not match:
        raise ValueError(f"Response does not contain function {expected_name}")
    start = match.start()
    opening = text.find("{", match.end())
    if opening < 0:
        raise ValueError("Function response has no body")
    closing = matching_brace(text, opening)
    if closing is None:
        raise ValueError("Function response has unbalanced braces")
    before = text[:start].strip()
    after = text[closing + 1:].strip()
    if before or after:
        raise ValueError("Response must contain exactly one function and no prose")
    function = text[start:closing + 1]
    _reject_unsafe(function)
    return function


def _reject_unsafe(source: str) -> None:
    checks = {
        "unsafe Rust": r"\bunsafe\b",
        "extern C": r"\bextern\s+\"C\"",
        "raw pointer type": r"\*(?:const|mut)\s+",
        "placeholder code": r"\b(?:todo|unimplemented)!\s*\(",
    }
    for label, pattern in checks.items():
        if re.search(pattern, source):
            raise ValueError(f"Response introduces forbidden {label}")


def matching_brace(source: str, opening: int) -> int | None:
    depth = 0
    state = "code"
    index = opening
    while index < len(source):
        char = source[index]
        pair = source[index:index + 2]
        if state == "code":
            if pair == "//":
                state = "line_comment"
                index += 1
            elif pair == "/*":
                state = "block_comment"
                index += 1
            elif char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
        elif state == "line_comment" and char == "\n":
            state = "code"
        elif state == "block_comment" and pair == "*/":
            state = "code"
            index += 1
        elif state in {"string", "char"}:
            if char == "\\":
                index += 1
            elif (state == "string" and char == '"') or (state == "char" and char == "'"):
                state = "code"
        index += 1
    return None
