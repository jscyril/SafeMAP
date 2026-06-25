from __future__ import annotations

from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command


def run_miri(root: Path, timeout: float = 1200) -> ValidationCheck:
    result = run_command(["cargo", "miri", "test"], root, timeout=timeout)
    combined = (result.stdout + "\n" + result.stderr).lower()
    unsupported_markers = (
        "unsupported operation", "not supported", "foreign function",
        "miri is not available",
    )
    if result.status == "failed" and any(marker in combined for marker in unsupported_markers):
        return ValidationCheck(
            status="unsupported",
            command=result,
            reason="Miri cannot execute this project's platform or FFI behavior",
        )
    return ValidationCheck(status=result.status, command=result, reason=result.reason)

