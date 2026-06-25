from __future__ import annotations

from pathlib import Path

from ..artifacts import ArtifactStore
from ..llm.client import LLMClient
from ..llm.prompt_builder import build_rewrite_prompt
from ..llm.prompts import REWRITE_SYSTEM_PROMPT
from ..llm.response_parser import parse_function_response
from ..models import FunctionInfo, MigrationPlan
from .patch_applier import replace_rust_function
from .unit_extractor import find_rust_function


def rewrite_function(
    function: FunctionInfo,
    plan: MigrationPlan,
    rust_file: Path,
    client: LLMClient,
    store: ArtifactStore,
    attempt: int = 1,
    tests: str = "",
    guided: bool = True,
) -> dict:
    source = rust_file.read_text(encoding="utf-8")
    _, _, current = find_rust_function(source, function.name)
    prompt = build_rewrite_prompt(function, current, plan, tests, guided=guided)
    store.write_text(f"prompts/{plan.unit_id}_attempt_{attempt}.txt", prompt)
    response = client.generate(prompt, REWRITE_SYSTEM_PROMPT)
    store.write_text(f"responses/{plan.unit_id}_attempt_{attempt}.txt", response.text)
    replacement = parse_function_response(response.text, function.name)
    store.write_text(f"rewrites/{plan.unit_id}_before.rs", current)
    replace_rust_function(rust_file, function.name, replacement)
    store.write_text(f"rewrites/{plan.unit_id}_after.rs", replacement)
    return {
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "model": response.model,
    }
