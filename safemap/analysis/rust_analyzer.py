from __future__ import annotations

import re
from pathlib import Path

from ..models import RustMetrics

FUNCTION_RE = re.compile(
    r"(?:pub(?:\([^)]*\))?\s+)?(?:unsafe\s+)?fn\s+([A-Za-z_]\w*)\s*\("
)


def analyze_rust_path(path: str | Path) -> RustMetrics:
    root = Path(path)
    files = [root] if root.is_file() else sorted(root.rglob("*.rs"))
    aggregate = RustMetrics()
    candidates: set[str] = set()
    for file in files:
        metrics = analyze_rust_source(file.read_text(encoding="utf-8", errors="replace"))
        for field in (
            "unsafe_blocks", "unsafe_functions", "raw_pointer_types",
            "raw_pointer_dereferences", "transmute_calls", "ffi_calls",
            "libc_usages", "extern_c_blocks", "raw_pointer_public_api_count",
            "unsafe_lines",
        ):
            setattr(aggregate, field, getattr(aggregate, field) + getattr(metrics, field))
        candidates.update(metrics.candidate_functions_for_rewrite)
    aggregate.candidate_functions_for_rewrite = sorted(candidates)
    return aggregate


def analyze_rust_source(source: str) -> RustMetrics:
    clean = _strip_comments_and_strings(source)
    unsafe_ranges = _keyword_block_ranges(clean, "unsafe")
    without_pointer_types = re.sub(
        r"\*(?:const|mut)\s+[A-Za-z_][\w:<>,\s\[\]();]*",
        "",
        clean,
    )
    functions = list(FUNCTION_RE.finditer(clean))
    candidates = []
    for index, function in enumerate(functions):
        end = functions[index + 1].start() if index + 1 < len(functions) else len(clean)
        body = clean[function.start():end]
        if "unsafe" in body or re.search(r"\*(?:const|mut)\s+\w+", body):
            candidates.append(function.group(1))
    return RustMetrics(
        unsafe_blocks=len(unsafe_ranges),
        unsafe_functions=len(
            re.findall(r"\bunsafe\s+(?:extern\s+\"C\"\s+)?fn\b", source)
        ),
        raw_pointer_types=len(re.findall(r"\*(?:const|mut)\s+[A-Za-z_(\[]", clean)),
        raw_pointer_dereferences=len(
            re.findall(r"(?<![\w)])\*\s*[A-Za-z_]\w*", without_pointer_types)
        ),
        transmute_calls=len(re.findall(r"\b(?:std::mem::)?transmute(?:\s*::[^(\s]+)?\s*\(", clean)),
        ffi_calls=len(re.findall(r"\b(?:libc|core::ffi|std::ffi)::", clean)),
        libc_usages=len(re.findall(r"\blibc::", clean)),
        extern_c_blocks=len(re.findall(r"\bextern\s+\"C\"\s*\{", source)),
        raw_pointer_public_api_count=len(re.findall(
            r"\bpub\s+(?:unsafe\s+)?fn\s+[A-Za-z_]\w*\s*\([^)]*\*(?:const|mut)\s+",
            clean,
        )),
        unsafe_lines=_count_lines_in_ranges(clean, unsafe_ranges),
        candidate_functions_for_rewrite=sorted(set(candidates)),
    )


def _strip_comments_and_strings(source: str) -> str:
    pattern = re.compile(
        r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'',
        re.DOTALL,
    )
    return pattern.sub(lambda match: "\n" * match.group(0).count("\n"), source)


def _keyword_block_ranges(source: str, keyword: str) -> list[tuple[int, int]]:
    ranges = []
    for match in re.finditer(rf"\b{keyword}\s*\{{", source):
        start = match.start()
        brace = source.find("{", match.start())
        depth = 0
        for index in range(brace, len(source)):
            if source[index] == "{":
                depth += 1
            elif source[index] == "}":
                depth -= 1
                if depth == 0:
                    ranges.append((start, index + 1))
                    break
    return ranges


def _count_lines_in_ranges(source: str, ranges: list[tuple[int, int]]) -> int:
    lines = set()
    for start, end in ranges:
        first = source.count("\n", 0, start) + 1
        last = source.count("\n", 0, end) + 1
        lines.update(range(first, last + 1))
    return len(lines)
