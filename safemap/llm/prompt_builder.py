from __future__ import annotations

import json

from ..models import FunctionInfo, MigrationPlan
from .prompts import REPAIR_TEMPLATE, REWRITE_TEMPLATE


def build_rewrite_prompt(
    function: FunctionInfo,
    rust_code: str,
    plan: MigrationPlan,
    tests: str = "",
    compiler_errors: str = "",
    guided: bool = True,
) -> str:
    replacements = {
        "<<<C_CODE>>>": function.body,
        "<<<RUST_CODE>>>": rust_code,
        "<<<ANALYSIS_FACTS>>>": json.dumps({
            "pointer_facts": [item.to_dict() for item in function.pointer_facts],
            "idioms": [item.to_dict() for item in function.idioms],
            "calls": function.calls,
        }, indent=2) if guided else "(withheld for unguided baseline)",
        "<<<MIGRATION_PLAN>>>": plan.to_json() if guided else "(none; unguided baseline)",
        "<<<TARGET_SIGNATURE>>>": plan.target_signature,
        "<<<TESTS>>>": tests or "(none discovered)",
        "<<<COMPILER_ERRORS>>>": compiler_errors or "(none)",
    }
    return _replace(REWRITE_TEMPLATE, replacements)


def build_repair_prompt(
    function: FunctionInfo,
    current_rust: str,
    plan: MigrationPlan,
    compiler_errors: str,
) -> str:
    return _replace(REPAIR_TEMPLATE, {
        "<<<C_CODE>>>": function.body,
        "<<<CURRENT_RUST_CODE>>>": current_rust,
        "<<<MIGRATION_PLAN>>>": plan.to_json(),
        "<<<COMPILER_ERRORS>>>": compiler_errors,
    })


def _replace(template: str, replacements: dict[str, str]) -> str:
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template
