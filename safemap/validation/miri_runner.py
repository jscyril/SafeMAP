from __future__ import annotations

from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command


def run_miri(root: Path, timeout: float = 1200) -> ValidationCheck:
    result = run_command(["cargo", "miri", "test"], root, timeout=timeout)
    unsupported = _miri_unsupported_reason(result.stdout + "\n" + result.stderr)
    if result.status == "failed" and unsupported:
        return ValidationCheck(
            status="unsupported",
            command=result,
            reason=unsupported,
        )
    return ValidationCheck(status=result.status, command=result, reason=result.reason)


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
