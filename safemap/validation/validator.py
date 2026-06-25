from __future__ import annotations

from pathlib import Path

from ..config import ValidationConfig
from ..models import ValidationCheck, ValidationResult
from .cargo_runner import run_cargo_check
from .clippy_runner import run_clippy
from .miri_runner import run_miri
from .test_runner import run_cargo_tests


def validate_project(root: Path, config: ValidationConfig) -> ValidationResult:
    skipped = lambda reason: ValidationCheck(status="skipped", reason=reason)
    return ValidationResult(
        compile=run_cargo_check(root, config.timeout_seconds)
        if config.run_cargo_check else skipped("Disabled"),
        tests=run_cargo_tests(root, config.timeout_seconds)
        if config.run_tests else skipped("Disabled"),
        clippy=run_clippy(root, config.timeout_seconds)
        if config.run_clippy else skipped("Disabled"),
        miri=run_miri(root, max(config.timeout_seconds, 600))
        if config.run_miri else skipped("Disabled"),
        differential=skipped("Requires an executable-compatible harness"),
    )

