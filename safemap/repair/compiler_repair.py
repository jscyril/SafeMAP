from __future__ import annotations

from pathlib import Path

from ..artifacts import ArtifactStore
from ..llm.client import LLMClient
from ..llm.prompt_builder import build_repair_prompt
from ..llm.response_parser import parse_function_response
from ..models import FunctionInfo, MigrationPlan
from ..process import run_command
from ..translation.patch_applier import replace_rust_function
from ..translation.unit_extractor import find_rust_function
from .error_parser import parse_cargo_diagnostics
from .repair_history import RepairAttempt, RepairHistory


def repair_function(
    function: FunctionInfo,
    plan: MigrationPlan,
    rust_file: Path,
    cargo_root: Path,
    client: LLMClient,
    store: ArtifactStore,
    max_attempts: int = 5,
) -> RepairHistory:
    source = rust_file.read_text(encoding="utf-8")
    _, _, original = find_rust_function(source, function.name)
    history = RepairHistory(plan.unit_id, "failed")
    for attempt_number in range(1, max_attempts + 1):
        check = run_command(
            ["cargo", "check", "--message-format=json"],
            cargo_root,
            timeout=600,
        )
        diagnostics = parse_cargo_diagnostics(check.stdout + "\n" + check.stderr)
        attempt = RepairAttempt(attempt_number, check, diagnostics)
        history.attempts.append(attempt)
        if check.status == "passed":
            history.status = "passed"
            break
        current_source = rust_file.read_text(encoding="utf-8")
        _, _, current = find_rust_function(current_source, function.name)
        rendered = "\n".join(
            item.rendered or f"{item.code}: {item.message}" for item in diagnostics
        ) or check.stderr
        prompt = build_repair_prompt(function, current, plan, rendered)
        store.write_text(f"prompts/{plan.unit_id}_repair_{attempt_number}.txt", prompt)
        try:
            response = client.generate(prompt)
            store.write_text(
                f"responses/{plan.unit_id}_repair_{attempt_number}.txt", response.text
            )
            replacement = parse_function_response(response.text, function.name)
            replace_rust_function(rust_file, function.name, replacement)
            attempt.response_status = "applied"
        except Exception as error:
            attempt.response_status = "rejected"
            attempt.reason = str(error)
    if history.status != "passed":
        final_check = run_command(
            ["cargo", "check", "--message-format=json"],
            cargo_root,
            timeout=600,
        )
        final_diagnostics = parse_cargo_diagnostics(
            final_check.stdout + "\n" + final_check.stderr
        )
        history.attempts.append(RepairAttempt(
            max_attempts + 1, final_check, final_diagnostics
        ))
        if final_check.status == "passed":
            history.status = "passed"
    if history.status != "passed":
        replace_rust_function(rust_file, function.name, original)
    store.write_json(f"repair/{plan.unit_id}.json", history)
    return history
