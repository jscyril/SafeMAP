"""Unit-level safe-Rust synthesis with per-unit compile gating.

Each planned unit is synthesized in dependency order (callees first), either by
an exact deterministic rule or, when an LLM client is configured, by a
plan-guided request followed by compiler-feedback repair. A unit enters the
crate only after it passes the policy check and compiles together with the
units already admitted, so one failing function cannot fail the others.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from ..artifacts import ArtifactStore
from ..llm.client import LLMClient, ProviderUnavailable
from ..llm.prompts import SYNTHESIS_REPAIR_TEMPLATE, SYNTHESIS_SYSTEM_PROMPT, SYNTHESIS_TEMPLATE
from ..llm.response_parser import parse_function_response
from ..models import CAnalysis, FunctionInfo, JsonModel, MigrationPlan, StructInfo, TranslationUnit
from ..process import run_command
from ..repair.error_parser import parse_cargo_diagnostics
from .safe_synthesizer import detect_synthesis_rule, _synthesize_function
from .signature_generator import (
    projectable_struct_names,
    rust_identifier,
    struct_field_rust_type,
)

CRATE_HEADER = "#![forbid(unsafe_code)]\n#![allow(non_snake_case, non_camel_case_types, dead_code)]\n"


@dataclass
class UnitOutcome(JsonModel):
    unit_id: str
    function: str
    status: str
    source: str = "none"
    attempts: int = 0
    reason: str | None = None
    rust_code: str | None = None
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class SynthesisContext:
    analysis: CAnalysis
    sources: dict[str, str]
    macros: dict[str, str] = field(default_factory=dict)
    enums: list[str] = field(default_factory=list)


def synthesize_units(
    analysis: CAnalysis,
    units: list[TranslationUnit],
    plans: list[MigrationPlan],
    output: Path,
    store: ArtifactStore,
    *,
    project_name: str,
    source_files: list[str],
    client: LLMClient | None = None,
    max_repair_attempts: int = 0,
    guided: bool = True,
) -> list[UnitOutcome]:
    functions = {item.name: item for item in analysis.functions}
    plan_by_unit = {plan.unit_id: plan for plan in plans}
    planned = [
        plan_by_unit[unit.unit_id] for unit in units
        if plan_by_unit[unit.unit_id].status == "planned"
    ]
    context = _load_context(analysis, source_files)
    prelude = render_struct_prelude(analysis.structs, planned)
    _write_crate(output, project_name, prelude, [])
    accepted: dict[str, str] = {}
    outcomes: list[UnitOutcome] = []
    for plan in planned:
        function = functions[plan.function]
        outcome = UnitOutcome(plan.unit_id, plan.function, "no_candidate")
        missing = sorted(
            call for call in plan.internal_calls
            if call != plan.function and call not in accepted
        )
        if missing:
            outcome.status = "dependency_missing"
            outcome.reason = "Untranslated internal dependency: " + ", ".join(missing)
            outcomes.append(outcome)
            continue
        candidates = []
        if plan.synthesis_support == "implemented_support" and detect_synthesis_rule(function, plan):
            code = _synthesize_function(function, plan)
            if code:
                candidates.append((f"rule:{plan.synthesis_rule}", code))
        for source, code in candidates:
            outcome.source = source
            outcome.attempts += 1
            error = _admit(output, project_name, prelude, accepted, plan, code)
            if error is None:
                outcome.status, outcome.rust_code = "compiled", code
                break
            outcome.status, outcome.reason = "compile_failed", error
        if outcome.status != "compiled" and client is not None:
            _llm_synthesize(
                outcome, function, plan, client, store, context, prelude,
                accepted, functions, output, project_name,
                max_repair_attempts, guided,
            )
        if outcome.status == "compiled" and outcome.rust_code:
            accepted[plan.function] = outcome.rust_code
        store.write_json(f"synthesis/{plan.unit_id}.json", outcome)
        outcomes.append(outcome)
    _write_crate(output, project_name, prelude, list(accepted.values()))
    return outcomes


def _llm_synthesize(
    outcome: UnitOutcome,
    function: FunctionInfo,
    plan: MigrationPlan,
    client: LLMClient,
    store: ArtifactStore,
    context: SynthesisContext,
    prelude: str,
    accepted: dict[str, str],
    functions: dict[str, FunctionInfo],
    output: Path,
    project_name: str,
    max_repair_attempts: int,
    guided: bool,
) -> None:
    outcome.source = "llm"
    prompt = build_synthesis_prompt(
        function, plan, context, prelude, accepted, functions, guided=guided,
    )
    code: str | None = None
    for attempt in range(0, max_repair_attempts + 1):
        label = "synthesis" if attempt == 0 else f"repair_{attempt}"
        store.write_text(f"prompts/{plan.unit_id}_{label}.txt", prompt)
        try:
            response = client.generate(prompt, SYNTHESIS_SYSTEM_PROMPT)
        except ProviderUnavailable:
            # Abort the run: an outage must not be scored as a method failure.
            raise
        except Exception as error:  # other provider errors are recorded
            outcome.status, outcome.reason = "llm_error", str(error)
            return
        outcome.llm_calls += 1
        outcome.input_tokens += response.input_tokens
        outcome.output_tokens += response.output_tokens
        outcome.attempts += 1
        store.write_text(f"responses/{plan.unit_id}_{label}.txt", response.text)
        try:
            code = parse_function_response(response.text, _rust_name(plan.function))
            error = _admit(output, project_name, prelude, accepted, plan, code)
            status = "compile_failed"
        except ValueError as rejection:
            error, status = f"Policy rejection: {rejection}", "rejected_policy"
        if error is None:
            outcome.status, outcome.rust_code, outcome.reason = "compiled", code, None
            return
        outcome.status, outcome.reason = status, error
        prompt = SYNTHESIS_REPAIR_TEMPLATE.replace(
            "<<<ORIGINAL_PROMPT>>>", build_synthesis_prompt(
                function, plan, context, prelude, accepted, functions, guided=guided,
            ),
        ).replace("<<<PREVIOUS_RUST>>>", code or response.text).replace(
            "<<<ERRORS>>>", error[:6000],
        )


def _admit(
    output: Path,
    project_name: str,
    prelude: str,
    accepted: dict[str, str],
    plan: MigrationPlan,
    code: str,
) -> str | None:
    """Return None if the candidate is policy-clean and compiles, else why not."""
    declared = _signature_of(code)
    if _normalize(declared) != _normalize(plan.target_signature):
        return (
            "Signature mismatch. Required exactly:\n"
            f"{plan.target_signature}\nGot:\n{declared}"
        )
    _write_crate(output, project_name, prelude, [*accepted.values(), code])
    check = run_command(
        ["cargo", "check", "--message-format=json", "--quiet"],
        output,
        timeout=300,
    )
    if check.status == "passed":
        return None
    diagnostics = parse_cargo_diagnostics(check.stdout)
    errors = [item.rendered or item.message for item in diagnostics if item.level == "error"]
    _write_crate(output, project_name, prelude, list(accepted.values()))
    return "\n".join(errors) or check.stderr or "cargo check failed"


def _signature_of(code: str) -> str:
    head = code.split("{", 1)[0]
    return " ".join(head.split())


def _normalize(signature: str) -> str:
    text = re.sub(r"\s+", " ", signature).strip()
    text = re.sub(r"\s*([(),:<>&\[\];])\s*", r"\1", text)
    return text.replace("->()", "")


def _rust_name(name: str) -> str:
    return rust_identifier(name).removeprefix("r#")


def _write_crate(output: Path, project_name: str, prelude: str, items: list[str]) -> None:
    source = output / "src"
    source.mkdir(parents=True, exist_ok=True)
    (source / "lib.rs").write_text(
        CRATE_HEADER + "\n" + "\n\n".join(part for part in [prelude, *items] if part) + "\n",
        encoding="utf-8",
    )
    cargo = output / "Cargo.toml"
    if not cargo.exists():
        cargo.write_text(
            "[package]\n"
            f'name = "{_crate_name(project_name)}"\n'
            'version = "0.1.0"\n'
            'edition = "2021"\n\n'
            "[dependencies]\n",
            encoding="utf-8",
        )


def _crate_name(project_name: str) -> str:
    name = re.sub(r"\W", "_", project_name).lower()
    return name if name and not name[0].isdigit() else f"c_{name}"


def render_struct_prelude(structs: list[StructInfo], plans: list[MigrationPlan]) -> str:
    """Render planned structs; pointer fields are projected out (see planner)."""
    mappable = projectable_struct_names(structs)
    signatures = " ".join(plan.target_signature for plan in plans)
    rendered = []
    for item in sorted(structs, key=lambda value: value.name):
        if item.name not in mappable or not re.search(rf"\b{re.escape(item.name)}\b", signatures):
            continue
        fields = "\n".join(
            f"    pub {rust_identifier(field['name'])}: {struct_field_rust_type(field['type'])},"
            for field in item.fields
            if struct_field_rust_type(field["type"]) is not None
        )
        omitted = [
            field["name"] for field in item.fields
            if struct_field_rust_type(field["type"]) is None
        ]
        if omitted:
            fields = f"    // scalar-field projection; omitted: {', '.join(omitted)}\n" + fields
        rendered.append(
            "#[derive(Clone, Copy, Debug, PartialEq)]\n"
            f"pub struct {item.name} {{\n{fields}\n}}"
        )
    return "\n\n".join(rendered)


def build_synthesis_prompt(
    function: FunctionInfo,
    plan: MigrationPlan,
    context: SynthesisContext,
    prelude: str,
    accepted: dict[str, str],
    functions: dict[str, FunctionInfo],
    *,
    guided: bool = True,
) -> str:
    callees = [
        _signature_of(accepted[call]) + ";"
        for call in plan.internal_calls
        if call in accepted and call != plan.function
    ]
    facts = {
        "pointer_facts": [item.to_dict() for item in function.pointer_facts],
        "idioms": [item.to_dict() for item in function.idioms],
        "calls": function.calls,
    }
    guidance = {
        "candidate_decision": plan.candidate_decision,
        "patterns": [item.to_dict() for item in plan.patterns],
        "type_migrations": plan.type_migrations,
        "constraints": plan.constraints,
    }
    replacements = {
        "<<<C_FUNCTION>>>": function.body,
        "<<<C_CONTEXT>>>": c_context_for(function, context) or "(none)",
        "<<<RUST_TYPES>>>": prelude or "(none)",
        "<<<RUST_CALLEES>>>": "\n".join(callees) or "(none)",
        "<<<ANALYSIS_FACTS>>>": (
            json.dumps(facts, indent=2) if guided else "(withheld: unguided ablation)"
        ),
        "<<<MIGRATION_PLAN>>>": (
            json.dumps(guidance, indent=2) if guided else "(withheld: unguided ablation)"
        ),
        "<<<TARGET_SIGNATURE>>>": plan.target_signature,
    }
    prompt = SYNTHESIS_TEMPLATE
    for marker, value in replacements.items():
        prompt = prompt.replace(marker, value)
    return prompt


def _load_context(analysis: CAnalysis, source_files: list[str]) -> SynthesisContext:
    sources: dict[str, str] = {}
    for name in source_files:
        path = Path(name)
        if path.is_file():
            sources[str(path)] = path.read_text(encoding="utf-8", errors="replace")
    context = SynthesisContext(analysis, sources)
    for text in sources.values():
        joined = re.sub(r"\\\n", " ", text)
        for match in re.finditer(r"^[ \t]*#[ \t]*define[ \t]+(\w+)(.*)$", joined, re.MULTILINE):
            context.macros.setdefault(match.group(1), f"#define {match.group(1)}{match.group(2)}".rstrip())
        for match in re.finditer(r"\b(?:typedef\s+)?enum\b[^{;]*\{[^}]*\}[^;]*;", text):
            context.enums.append(match.group(0))
    return context


def c_context_for(function: FunctionInfo, context: SynthesisContext) -> str:
    """Macros, enums, and const globals that the function body references."""
    identifiers = set(re.findall(r"\b[A-Za-z_]\w*\b", function.body))
    lines: list[str] = []
    seen: set[str] = set()
    frontier = sorted(identifiers)
    for _ in range(3):
        next_frontier = []
        for name in frontier:
            definition = context.macros.get(name)
            if definition and name not in seen and name != function.name:
                seen.add(name)
                lines.append(definition)
                next_frontier.extend(re.findall(r"\b[A-Za-z_]\w*\b", definition))
        frontier = next_frontier
    for enum in context.enums:
        if identifiers & set(re.findall(r"\b[A-Za-z_]\w*\b", enum)):
            lines.append(enum)
    for item in context.analysis.globals:
        if item.mutable or item.name not in identifiers:
            continue
        text = context.sources.get(item.file, "")
        declaration = _declaration_at(text, item.line)
        if declaration:
            lines.append(declaration)
    return "\n".join(lines)


def _declaration_at(text: str, line: int) -> str | None:
    lines = text.splitlines()
    if not 0 < line <= len(lines):
        return None
    collected = []
    for item in lines[line - 1:line + 199]:
        collected.append(item)
        if ";" in item:
            break
    return "\n".join(collected)
