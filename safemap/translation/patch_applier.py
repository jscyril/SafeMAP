from __future__ import annotations

from pathlib import Path

from .unit_extractor import find_rust_function


def replace_rust_function(path: Path, name: str, replacement: str) -> str:
    source = path.read_text(encoding="utf-8")
    start, end, previous = find_rust_function(source, name)
    path.write_text(source[:start] + replacement + source[end:], encoding="utf-8")
    return previous

