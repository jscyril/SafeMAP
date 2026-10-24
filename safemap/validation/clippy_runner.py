from __future__ import annotations

import json
import re
from pathlib import Path

from ..models import CompilerDiagnostic, ValidationCheck
from ..process import run_command


def run_clippy(root: Path, timeout: float = 600) -> ValidationCheck:
    result = run_command(
        ["cargo", "clippy", "--message-format=json", "--all-targets"],
        root,
        timeout=timeout,
    )
    warnings = []
    for line in result.stdout.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = record.get("message", {}) if record.get("reason") == "compiler-message" else {}
        if message.get("level") != "warning":
            continue
        warnings.append(CompilerDiagnostic(
            code=(message.get("code") or {}).get("code"),
            level="warning",
            message=message.get("message", ""),
            rendered=message.get("rendered", ""),
        ))
    return ValidationCheck(
        status=result.status,
        command=result,
        errors=warnings,
        reason=result.reason,
    )



def clippy_error_lines(check: ValidationCheck) -> list[tuple[str, int]] | None:
    """(file, line) of every Clippy error, or None if a failure has no source line."""
    if check.command is None:
        return None
    found = []
    for line in check.command.stdout.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = record.get("message", {}) if record.get("reason") == "compiler-message" else {}
        if not str(message.get("level", "")).startswith("error"):
            continue
        spans = [span for span in message.get("spans", []) if span.get("is_primary")]
        if not spans:
            if message.get("message", "").startswith("aborting due to"):
                continue  # rustc's summary line, not a diagnostic
            return None
        span = spans[0]
        while span.get("expansion"):  # blame the macro call site, not its definition
            span = span["expansion"]["span"]
        found.append((span["file_name"], span["line_start"]))
    # A failed run with no attributable error (timeout, crash) cannot be split.
    return found or None


def function_spans(source: str) -> list[tuple[str, int, int]]:
    """(name, first line, last line) of each top-level `fn` in Rust source."""
    spans = []
    depth, line, i, n = 0, 1, 0, len(source)
    pending: tuple[str, int] | None = None
    opened: tuple[str, int] | None = None
    while i < n:
        ch = source[i]
        if ch == "\n":
            line += 1
        elif source.startswith("//", i):
            i = source.find("\n", i)
            i = n if i < 0 else i
            continue
        elif source.startswith("/*", i):
            end = source.find("*/", i + 2)
            end = n if end < 0 else end + 2
            line += source.count("\n", i, end)
            i = end
            continue
        elif ch == '"' or (
            not (i and _ident(source[i - 1])) and re.match(r'b?r#*"|b"', source[i:i + 8])
        ):
            end = _skip_string(source, i)
            line += source.count("\n", i, end)
            i = end
            continue
        elif ch == "'":
            match = re.match(r"'(?:\\.[^']*|[^\\'])'", source[i:i + 12])
            if match:
                i += len(match.group(0))
                continue
        elif ch == "{":
            if depth == 0 and pending:
                opened, pending = pending, None
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and opened:
                spans.append((opened[0], opened[1], line))
                opened = None
        elif ch == ";" and depth == 0:
            pending = None  # a declaration without a body
        elif depth == 0 and source.startswith("fn", i) and (i == 0 or not _ident(source[i - 1])):
            match = re.match(r"fn\s+(?:r#)?([A-Za-z_]\w*)", source[i:])
            if match:
                pending = (match.group(1), line)
                i += len(match.group(0))
                continue
        i += 1
    return spans


def _ident(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


def _skip_string(source: str, i: int) -> int:
    start = i
    while source[i] in "br":
        i += 1
    hashes = 0
    while source[i] == "#":
        hashes += 1
        i += 1
    raw = "r" in source[start:i]
    i += 1  # opening quote
    closing = '"' + "#" * hashes
    while i < len(source):
        if not raw and source[i] == "\\":
            i += 2
            continue
        if source.startswith(closing, i):
            return i + len(closing)
        i += 1
    return i
