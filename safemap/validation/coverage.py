from __future__ import annotations

import shutil
from pathlib import Path

from ..models import ValidationCheck
from ..process import run_command


def run_coverage(root: Path) -> ValidationCheck:
    if shutil.which("cargo-llvm-cov"):
        result = run_command(["cargo", "llvm-cov", "--json"], root, timeout=1200)
    elif shutil.which("cargo-tarpaulin"):
        result = run_command(["cargo", "tarpaulin", "--out", "Json"], root, timeout=1200)
    else:
        return ValidationCheck(status="unsupported", reason="No Rust coverage tool installed")
    return ValidationCheck(status=result.status, command=result, reason=result.reason)

