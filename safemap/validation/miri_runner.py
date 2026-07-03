from __future__ import annotations

import re
from pathlib import Path

from ..models import CompilerDiagnostic, ValidationCheck
from ..process import run_command


def run_miri(root: Path, timeout: float = 1200) -> ValidationCheck:
    result = run_command(["cargo", "miri", "test"], root, timeout=timeout)
    output = result.stdout + "\n" + result.stderr
    unsupported = _miri_unsupported_reason(output)
    if result.status == "failed" and unsupported:
        return ValidationCheck(
            status="unsupported",
            command=result,
            reason=unsupported,
            errors=_miri_diagnostics(output),
        )
    passed, failed = _miri_test_counts(output)
    return ValidationCheck(
        status=result.status,
        command=result,
        errors=_miri_diagnostics(output),
        passed=passed,
        failed=failed,
        reason=result.reason,
    )


def _miri_unsupported_reason(output: str) -> str | None:
    combined = output.lower()
    if "no such command: `miri`" in combined or "component 'miri'" in combined:
        return (
            "Miri is not installed for the active Rust toolchain. Install it with "
            "`rustup component add miri` or disable validation.run_miri."
        )
    if "unsupported operation" in combined or "not supported" in combined:
        return "Miri cannot execute an operation used by this project."
    if "foreign function" in combined or "extern function" in combined:
        return "Miri cannot execute this project's FFI or foreign-function behavior."
    if "miri is not available" in combined:
        return "Miri is not available for the active Rust toolchain."
    return None


def _miri_test_counts(output: str) -> tuple[int, int]:
    passed = failed = 0
    for match in re.finditer(
        r"test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed",
        output,
    ):
        passed += int(match.group(1))
        failed += int(match.group(2))
    return passed, failed


def _miri_diagnostics(output: str) -> list[CompilerDiagnostic]:
    diagnostics: list[CompilerDiagnostic] = []
    lines = output.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"\s*(error|warning)(?:\[[^\]]+\])?:\s*(.+)", line)
        if not match:
            continue
        file_name, line_number, column = _next_location(lines[index + 1:index + 8])
        diagnostics.append(CompilerDiagnostic(
            code=None,
            level=match.group(1),
            message=match.group(2).strip(),
            rendered=_diagnostic_snippet(lines, index),
            file=file_name,
            line=line_number,
            column=column,
        ))
    if diagnostics:
        return diagnostics
    if "Undefined Behavior:" in output:
        return [CompilerDiagnostic(
            code=None,
            level="error",
            message=_first_matching_line(output, "Undefined Behavior:"),
            rendered=_tail(output),
        )]
    return []


def _next_location(lines: list[str]) -> tuple[str | None, int | None, int | None]:
    for line in lines:
        match = re.search(r"-->\s+(.+?):(\d+):(\d+)", line)
        if match:
            return match.group(1), int(match.group(2)), int(match.group(3))
    return None, None, None


def _diagnostic_snippet(lines: list[str], index: int) -> str:
    snippet = lines[index:index + 6]
    return "\n".join(snippet).strip()


def _first_matching_line(output: str, pattern: str) -> str:
    for line in output.splitlines():
        if pattern in line:
            return line.strip()
    return pattern


def _tail(output: str, max_lines: int = 12) -> str:
    return "\n".join(output.splitlines()[-max_lines:]).strip()
