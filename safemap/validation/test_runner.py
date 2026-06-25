from __future__ import annotations

import re
from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command


def run_cargo_tests(root: Path, timeout: float = 600) -> ValidationCheck:
    result = run_command(["cargo", "test", "--", "--nocapture"], root, timeout=timeout)
    passed = failed = 0
    for match in re.finditer(
        r"test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed", result.stdout
    ):
        passed += int(match.group(1))
        failed += int(match.group(2))
    return ValidationCheck(
        status=result.status,
        command=result,
        passed=passed,
        failed=failed,
        reason=result.reason,
    )

