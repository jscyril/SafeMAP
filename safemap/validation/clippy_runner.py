from __future__ import annotations

import json
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

