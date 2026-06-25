from __future__ import annotations

import json

from ..models import CompilerDiagnostic


def parse_cargo_diagnostics(output: str) -> list[CompilerDiagnostic]:
    diagnostics = []
    for line in output.splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("reason") != "compiler-message":
            continue
        message = record.get("message", {})
        primary = next(
            (span for span in message.get("spans", []) if span.get("is_primary")),
            {},
        )
        diagnostics.append(CompilerDiagnostic(
            code=(message.get("code") or {}).get("code"),
            level=message.get("level", "error"),
            message=message.get("message", ""),
            rendered=message.get("rendered", ""),
            file=primary.get("file_name"),
            line=primary.get("line_start"),
            column=primary.get("column_start"),
        ))
    return diagnostics

