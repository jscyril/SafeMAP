from __future__ import annotations

from dataclasses import dataclass, field

from ..models import CommandResult, CompilerDiagnostic, JsonModel


@dataclass
class RepairAttempt(JsonModel):
    attempt: int
    compile_result: CommandResult
    diagnostics: list[CompilerDiagnostic] = field(default_factory=list)
    response_status: str = "not_requested"
    reason: str | None = None


@dataclass
class RepairHistory(JsonModel):
    unit_id: str
    status: str
    attempts: list[RepairAttempt] = field(default_factory=list)

