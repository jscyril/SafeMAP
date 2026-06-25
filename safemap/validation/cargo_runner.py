from __future__ import annotations

from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command
from ..repair.error_parser import parse_cargo_diagnostics


def run_cargo_check(root: Path, timeout: float = 600) -> ValidationCheck:
    result = run_command(
        ["cargo", "check", "--message-format=json"], root, timeout=timeout
    )
    return ValidationCheck(
        status=result.status,
        command=result,
        errors=parse_cargo_diagnostics(result.stdout + "\n" + result.stderr),
        reason=result.reason,
    )

