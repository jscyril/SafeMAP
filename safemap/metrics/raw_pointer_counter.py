from __future__ import annotations

from pathlib import Path

from ..analysis.rust_analyzer import analyze_rust_path


def count_raw_pointers(path: str | Path) -> int:
    return analyze_rust_path(path).raw_pointer_types

