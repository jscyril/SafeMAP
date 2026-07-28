from __future__ import annotations

import re

from ..models import (
    CAnalysis, EligibilityResult, MigrationPlan, PatternMigration, TranslationUnit,
)
from ..analysis.eligibility import classify_analysis
from .safe_synthesizer import detect_synthesis_rule
from .signature_generator import generate_signature

SAFE_PATTERNS = {
    "pointer_length_array",
    "fixed_size_array",
    "output_parameter",
    "nullable_pointer",
    "manual_allocation",
    "error_code_return",
    "lock_unlock",
    "c_string",
    "boolean_int",
    "struct_pointer",
}


def create_migration_plans(
    analysis: CAnalysis,
    units: list[TranslationUnit],
    threshold: float = 0.75,
    *,
    use_safe_signatures: bool = True,
    use_idiom_plans: bool = True,
) -> list[MigrationPlan]:
    functions = {item.name: item for item in analysis.functions}
    known_functions = set(functions)
    eligibility_by_function = _eligibility_by_function(analysis)
    plans = []
    for unit in units:
        function = functions[unit.c_function]
        eligibility = eligibility_by_function.get(function.name)
        if eligibility is None:
            eligibility = EligibilityResult(
                unit_id=unit.unit_id,
                function=function.name,
                category="unsupported",
                reasons=["Function was not classified"],
            )
        patterns = [
            PatternMigration(
                pattern=idiom.idiom_type,
                original=", ".join(idiom.variables) or idiom.evidence,
                replacement=idiom.suggested_rust_pattern,
                confidence=idiom.confidence,
            )
            for idiom in function.idioms
            if use_idiom_plans
            and idiom.idiom_type in SAFE_PATTERNS
            and idiom.confidence >= threshold
        ]
        safe_candidate = eligibility.eligible_for_safe_translation
        status = (
            "planned"
            if safe_candidate and (
                patterns or _is_safe_scalar_candidate(function)
            )
            else "rejected"
        )
        reason = None if status == "planned" else "; ".join(eligibility.reasons)
        plan = MigrationPlan(
            unit_id=unit.unit_id,
            target_signature=generate_signature(
                function,
                use_safe_signatures=use_safe_signatures,
            ),
            patterns=patterns,
            constraints=[
                "Preserve observable C behavior",
                "Do not use unsafe code",
                "Do not expose raw pointer public APIs",
                "Do not introduce unapproved external crates",
                "Compile with #![forbid(unsafe_code)]",
            ],
            validation_requirements=[
                "cargo check", "cargo test", "cargo clippy", "differential testing"
            ],
            source_file=function.file,
            function=function.name,
            eligibility=eligibility.category,
            eligibility_reasons=eligibility.reasons,
            detected_idioms=[_plan_idiom(item) for item in function.idioms],
            original_signature=_original_signature(function),
            type_migrations=_type_migrations(function),
            safety_constraints=[
                "no unsafe code",
                "no raw pointer public API",
                "compile with #![forbid(unsafe_code)]",
            ],
            validation={
                "compile": True,
                "unit_tests": "if_available",
                "differential_tests": "if_applicable",
                "clippy": True,
                "miri": "optional",
            },
            status=status,
            reason=reason,
            candidate_decision=eligibility.candidate_decision,
            analysis_backend=analysis.analysis_backend,
            internal_calls=[
                call for call in function.calls if call in known_functions
            ],
        )
        rule = detect_synthesis_rule(function, plan) if status == "planned" else None
        if not use_idiom_plans and rule != "scalar_return":
            rule = None
        if (
            rule == "internal_call_return"
            and unit.reason == "dependency grouping disabled"
        ):
            rule = None
            plan.reason = (
                "Internal-call synthesis requires dependency grouping"
            )
        plan.synthesis_rule = rule
        plan.synthesis_support = (
            "implemented_support"
            if rule is not None
            else "not_implemented"
            if eligibility.candidate_decision == "candidate_safe"
            else "not_applicable"
        )
        plans.append(plan)
    _enforce_supported_dependency_closure(plans)
    return plans


def _enforce_supported_dependency_closure(
    plans: list[MigrationPlan],
) -> None:
    by_function = {plan.function: plan for plan in plans}
    changed = True
    while changed:
        changed = False
        for plan in plans:
            if plan.synthesis_support != "implemented_support":
                continue
            missing = [
                dependency
                for dependency in plan.internal_calls
                if dependency not in by_function
                or by_function[dependency].synthesis_support
                != "implemented_support"
            ]
            if not missing:
                continue
            plan.synthesis_support = "not_implemented"
            plan.synthesis_rule = None
            plan.reason = (
                "Internal dependency lacks implemented synthesis support: "
                + ", ".join(sorted(missing))
            )
            changed = True


def _eligibility_by_function(analysis: CAnalysis) -> dict[str, EligibilityResult]:
    return {item.function: item for item in classify_analysis(analysis)}


def _plan_idiom(idiom) -> dict[str, object]:
    result: dict[str, object] = {
        "kind": idiom.idiom_type,
        "variables": idiom.variables,
        "rust_type": idiom.suggested_rust_pattern,
        "confidence": idiom.confidence,
        "evidence": idiom.evidence,
    }
    if idiom.idiom_type == "pointer_length_array" and idiom.variables:
        result["pointer"] = idiom.variables[0]
    return result


def _original_signature(function) -> str:
    params = ", ".join(
        f"{parameter.c_type} {parameter.name}".strip()
        for parameter in function.parameters
    )
    return f"{function.return_type} {function.name}({params})"


def _type_migrations(function) -> list[dict[str, str]]:
    migrations: list[dict[str, str]] = []
    for idiom in function.idioms:
        if idiom.idiom_type == "pointer_length_array" and idiom.variables:
            migrations.append({
                "c": ", ".join(idiom.variables),
                "rust": idiom.suggested_rust_pattern,
                "reason": idiom.evidence,
            })
        elif idiom.idiom_type in {
            "output_parameter",
            "nullable_pointer",
            "error_code_return",
            "manual_allocation",
            "c_string",
            "boolean_int",
        }:
            migrations.append({
                "c": ", ".join(idiom.variables) or idiom.idiom_type,
                "rust": idiom.suggested_rust_pattern,
                "reason": idiom.evidence,
            })
    return migrations


def _is_safe_scalar_candidate(function) -> bool:
    if function.return_type.strip() == "void":
        return False
    if function.parameters and any(parameter.is_pointer for parameter in function.parameters):
        return False
    return bool(re.search(r"\breturn\s+[^;]+;", function.body))
