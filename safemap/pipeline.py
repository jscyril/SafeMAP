from __future__ import annotations

import json
import copy
import hashlib
import shutil
import time
from pathlib import Path

from .analysis.c_analyzer import analyze_c_project
from .analysis.dependency_graph import (
    create_independent_translation_units,
    create_translation_units,
)
from .analysis.eligibility import classify_analysis
from .analysis.rust_analyzer import analyze_rust_path
from .artifacts import ArtifactStore
from .config import LLMConfig, SafeMapConfig
from .ingestion.project_loader import ingest_project
from .llm.client import LLMClient, OpenAICompatibleClient
from .metrics.report_generator import comparison_csv, generate_markdown
from .metrics.residual_unsafe import classify_residual_unsafe
from .models import (
    CAnalysis, MigrationPlan, PatternMigration, ProjectInfo, RunMetrics, TranslationUnit,
    from_dict,
)
from .process import run_command
from .translation.c2rust_runner import run_c2rust
from .translation.migration_planner import create_migration_plans
from .translation.rewriter import rewrite_function
from .translation.safe_synthesizer import synthesize_safe_crate
from .repair.compiler_repair import repair_function
from .validation.validator import validate_project
from .validation.differential_tester import (
    build_and_compare_projects,
    validate_c_oracle_sanitizers,
)
from .analysis.complexity_metrics import cyclomatic_complexity
from .llm.response_parser import reject_forbidden_constructs


def run_pipeline(
    input_path: str | Path,
    output_base: str | Path,
    config: SafeMapConfig,
    client: LLMClient | None = None,
) -> ArtifactStore:
    started = time.monotonic()
    source = Path(input_path).resolve()
    project_name = config.project.name or source.stem
    store = ArtifactStore.create(Path(output_base).resolve(), project_name)
    store.record_environment()
    _record_tool_versions(store)
    project = ingest_project(source, store)
    raw_analysis = analyze_c_project(project)
    store.write_json("analysis/c_analysis_raw.json", raw_analysis)
    analysis = _effective_analysis(raw_analysis, config)
    store.write_json("analysis/c_analysis.json", analysis)
    units = (
        create_translation_units(analysis)
        if config.translation.use_dependency_grouping
        else create_independent_translation_units(analysis)
    )
    store.write_json("analysis/translation_units.json", [item.to_dict() for item in units])
    eligibility = classify_analysis(analysis)
    store.write_json("analysis/eligibility.json", [item.to_dict() for item in eligibility])
    plans = (
        create_migration_plans(
            analysis,
            units,
            config.translation.automatic_confidence_threshold,
            use_safe_signatures=config.translation.use_safe_signatures,
            use_idiom_plans=config.translation.use_idiom_plans,
        )
        if config.translation.use_static_guidance
        else _unguided_plans(units)
    )
    for plan in plans:
        store.write_json(f"plans/{plan.unit_id}.json", plan)
    store.write_json(
        "analysis/component_configuration.json",
        {
            "use_static_guidance": config.translation.use_static_guidance,
            "use_pointer_roles": config.translation.use_pointer_roles,
            "use_safe_signatures": config.translation.use_safe_signatures,
            "use_dependency_grouping": config.translation.use_dependency_grouping,
            "use_idiom_plans": config.translation.use_idiom_plans,
            "use_validation_feedback": config.translation.use_validation_feedback,
        },
    )
    baseline_result = run_c2rust(project, store) if config.translation.use_c2rust else None
    baseline_root = store.path("baseline/rust")
    final_root = store.path("final/rust")
    used_direct_translation = False
    direct_llm_usage: dict[str, int | str] | None = None
    baseline_metrics = analyze_rust_path(baseline_root) if list(baseline_root.rglob("*.rs")) else None
    if baseline_metrics:
        store.write_json("analysis/baseline_rust.json", baseline_metrics)
    synthesized_units: list[str] = []
    synthesized_units = synthesize_safe_crate(
        project,
        analysis.functions,
        plans,
        final_root,
        structs=analysis.structs,
    )
    if synthesized_units:
        store.write_json("logs/safe_synthesis.json", {
            "status": "passed",
            "generated_units": synthesized_units,
        })
    if baseline_result and baseline_result.status == "passed" and config.translation.use_llm:
        if not (final_root / "Cargo.toml").exists():
            shutil.copytree(baseline_root, final_root, dirs_exist_ok=True)
    elif (
        not synthesized_units
        and config.translation.use_llm
        and _project_loc(project) <= config.translation.direct_llm_max_c_loc
    ):
        llm = client or OpenAICompatibleClient(config.llm)
        try:
            direct_llm_usage = _direct_llm_translation(
                project,
                final_root,
                llm,
                store,
                config.llm,
            )
            used_direct_translation = True
        except Exception as error:
            store.write_json("logs/direct_llm_error.json", {
                "status": "failed", "reason": str(error),
            })
            call_path = store.path("logs/direct_llm_call.json")
            if call_path.is_file():
                call_record = json.loads(
                    call_path.read_text(encoding="utf-8")
                )
                call_record["status"] = (
                    "rejected"
                    if call_record.get("response_path")
                    else "failed"
                )
                call_record["failure"] = {
                    "type": type(error).__name__,
                    "message": str(error),
                }
                store.write_json("logs/direct_llm_call.json", call_record)
    metrics = RunMetrics(
        project=project.project_name,
        baseline=baseline_metrics,
        baseline_compile=_compile_status(store.path("baseline/compile.json")),
        total_units=len(units),
    )
    _apply_eligibility_metrics(metrics, eligibility)
    _apply_synthesis_metrics(metrics, plans, synthesized_units)
    _record_synthesized_idioms(metrics, plans, synthesized_units)
    if direct_llm_usage:
        metrics.llm_calls += 1
        metrics.llm_input_tokens += int(direct_llm_usage.get("input_tokens", 0))
        metrics.llm_output_tokens += int(direct_llm_usage.get("output_tokens", 0))
    if (
        config.translation.use_llm
        and final_root.exists()
        and not used_direct_translation
        and not synthesized_units
    ):
        llm = client or OpenAICompatibleClient(config.llm)
        _rewrite_units(
            analysis, units, plans, final_root, llm, store, metrics,
            max_repair_attempts=(
                config.translation.max_repair_attempts
                if config.translation.use_validation_feedback
                else 0
            ),
            guided=config.translation.use_static_guidance,
        )
    if final_root.exists() and (final_root / "Cargo.toml").exists():
        validation = validate_project(final_root, config.validation)
        if (
            config.validation.run_differential_tests
            and len(project.c_files) == 1
        ):
            if config.validation.run_c_sanitizers:
                validation.c_sanitizers = validate_c_oracle_sanitizers(
                    Path(project.c_files[0]),
                    seed=config.validation.seed,
                    random_inputs=config.validation.differential_test_inputs,
                    functions=analysis.functions,
                    plans=plans,
                    structs=analysis.structs,
                    artifact_path=store.path(
                        "validation/c_sanitizer_cases.json"
                    ),
                )
            validation.differential = build_and_compare_projects(
                Path(project.c_files[0]), final_root,
                seed=config.validation.seed,
                random_inputs=config.validation.differential_test_inputs,
                functions=analysis.functions,
                plans=plans,
                structs=analysis.structs,
                artifact_path=store.path(
                    "validation/differential_cases.json"
                ),
            )
        store.write_json("validation/results.json", validation)
        metrics.safemap_compile = validation.compile.status == "passed"
        if validation.tests.passed is not None:
            total = validation.tests.passed + (validation.tests.failed or 0)
            metrics.test_pass_rate = validation.tests.passed / total if total else None
        metrics.safemap = analyze_rust_path(final_root)
        metrics.residual_unsafe = classify_residual_unsafe(final_root)
        if validation.differential.passed is not None:
            total = validation.differential.passed + (validation.differential.failed or 0)
            metrics.differential_pass_rate = (
                validation.differential.passed / total if total else None
            )
        metrics.maintainability = _maintainability(final_root)
        store.write_json("analysis/final_rust.json", metrics.safemap)
        _apply_safe_acceptance(metrics, plans, validation, final_root)
    _apply_research_metric_maps(metrics)
    _write_unit_decisions(
        store,
        project,
        analysis,
        units,
        eligibility,
        plans,
        metrics,
    )
    metrics.translation_seconds = time.monotonic() - started
    _write_reports(store, metrics)
    store.write_json("run_status.json", {
        "status": "completed",
        "baseline_status": baseline_result.status if baseline_result else "skipped",
        "final_project": str(final_root) if final_root.exists() else None,
    })
    return store


def _effective_analysis(
    analysis: CAnalysis,
    config: SafeMapConfig,
) -> CAnalysis:
    effective = copy.deepcopy(analysis)
    if not config.translation.use_pointer_roles:
        for function in effective.functions:
            function.pointer_facts = []
    return effective


def load_project(store: ArtifactStore) -> ProjectInfo:
    return from_dict(ProjectInfo, store.read_json("project.json"))


def analyze_c_stage(store: ArtifactStore) -> CAnalysis:
    analysis = analyze_c_project(load_project(store))
    store.write_json("analysis/c_analysis.json", analysis)
    units = create_translation_units(analysis)
    store.write_json("analysis/translation_units.json", [item.to_dict() for item in units])
    store.write_json(
        "analysis/eligibility.json",
        [item.to_dict() for item in classify_analysis(analysis)],
    )
    return analysis


def plan_stage(store: ArtifactStore, threshold: float = 0.75) -> list[MigrationPlan]:
    analysis = from_dict(CAnalysis, store.read_json("analysis/c_analysis.json"))
    units = [
        from_dict(TranslationUnit, item)
        for item in store.read_json("analysis/translation_units.json")
    ]
    plans = create_migration_plans(analysis, units, threshold)
    for plan in plans:
        store.write_json(f"plans/{plan.unit_id}.json", plan)
    return plans


def rewrite_stage(
    store: ArtifactStore,
    config: SafeMapConfig,
    client: LLMClient | None = None,
) -> RunMetrics:
    project = load_project(store)
    analysis = from_dict(CAnalysis, store.read_json("analysis/c_analysis.json"))
    units = [
        from_dict(TranslationUnit, item)
        for item in store.read_json("analysis/translation_units.json")
    ]
    plans = [
        from_dict(MigrationPlan, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(store.path("plans").glob("*.json"))
    ]
    baseline_root = store.path("baseline/rust")
    final_root = store.path("final/rust")
    if not final_root.exists():
        if not baseline_root.exists():
            raise FileNotFoundError("No baseline Rust project is available")
        shutil.copytree(baseline_root, final_root, dirs_exist_ok=True)
    metrics = RunMetrics(project=project.project_name)
    _rewrite_units(
        analysis, units, plans, final_root,
        client or OpenAICompatibleClient(config.llm), store, metrics,
        max_repair_attempts=config.translation.max_repair_attempts,
    )
    store.write_json("reports/rewrite_metrics.json", metrics)
    return metrics


def repair_stage(
    store: ArtifactStore,
    config: SafeMapConfig,
    client: LLMClient | None = None,
) -> list[dict]:
    analysis = from_dict(CAnalysis, store.read_json("analysis/c_analysis.json"))
    functions = {item.name: item for item in analysis.functions}
    final_root = store.path("final/rust")
    results = []
    llm = client or OpenAICompatibleClient(config.llm)
    for path in sorted(store.path("plans").glob("*.json")):
        plan = from_dict(MigrationPlan, json.loads(path.read_text(encoding="utf-8")))
        name = plan.target_signature.split("fn ", 1)[-1].split("(", 1)[0].strip()
        rust_file = _find_function_file(final_root, name)
        if rust_file is None or name not in functions:
            continue
        history = repair_function(
            functions[name], plan, rust_file, final_root, llm, store,
            config.translation.max_repair_attempts,
        )
        results.append(history.to_dict())
    return results


def report_stage(store: ArtifactStore) -> RunMetrics:
    project = load_project(store)
    baseline_root = store.path("baseline/rust")
    final_root = store.path("final/rust")
    metrics = RunMetrics(
        project=project.project_name,
        baseline=analyze_rust_path(baseline_root) if baseline_root.exists() else None,
        safemap=analyze_rust_path(final_root) if final_root.exists() else None,
        baseline_compile=_compile_status(store.path("baseline/compile.json")),
    )
    validation_path = store.path("validation/results.json")
    if validation_path.exists():
        validation = json.loads(validation_path.read_text(encoding="utf-8"))
        metrics.safemap_compile = validation["compile"]["status"] == "passed"
    if final_root.exists():
        metrics.residual_unsafe = classify_residual_unsafe(final_root)
    _write_reports(store, metrics)
    return metrics


def _rewrite_units(
    analysis: CAnalysis,
    units: list[TranslationUnit],
    plans: list[MigrationPlan],
    final_root: Path,
    client: LLMClient,
    store: ArtifactStore,
    metrics: RunMetrics,
    max_repair_attempts: int = 5,
    guided: bool = True,
) -> None:
    functions = {item.name: item for item in analysis.functions}
    plan_by_id = {item.unit_id: item for item in plans}
    for unit in units:
        plan = plan_by_id[unit.unit_id]
        if plan.status != "planned" or not plan.patterns:
            if plan.status != "planned":
                metrics.failed_units.append({
                    "unit_id": unit.unit_id,
                    "reason": plan.reason or "Manual review required",
                })
            continue
        rust_file = _find_function_file(final_root, unit.rust_function)
        if rust_file is None:
            metrics.failed_units.append({
                "unit_id": unit.unit_id,
                "reason": f"Rust function not found: {unit.rust_function}",
            })
            continue
        try:
            usage = rewrite_function(
                functions[unit.c_function], plan, rust_file, client, store,
                guided=guided,
            )
            metrics.llm_calls += 1
            metrics.llm_input_tokens += usage["input_tokens"]
            metrics.llm_output_tokens += usage["output_tokens"]
            for pattern in plan.patterns:
                metrics.migrated_idioms[pattern.pattern] = (
                    metrics.migrated_idioms.get(pattern.pattern, 0) + 1
                )
            if (final_root / "Cargo.toml").exists():
                history = repair_function(
                    functions[unit.c_function], plan, rust_file, final_root,
                    client, store, max_repair_attempts,
                )
                applied_repairs = sum(
                    attempt.response_status == "applied" for attempt in history.attempts
                )
                metrics.repair_attempts += applied_repairs
                metrics.llm_calls += applied_repairs
                if history.status != "passed":
                    metrics.failed_units.append({
                        "unit_id": unit.unit_id,
                        "reason": "Compiler repair budget exhausted; rewrite rolled back",
                    })
        except Exception as error:
            metrics.failed_units.append({
                "unit_id": unit.unit_id,
                "reason": str(error),
            })


def _find_function_file(root: Path, name: str) -> Path | None:
    import re
    pattern = re.compile(
        rf"\bfn\s+(?:r#)?{re.escape(name)}\s*(?:<|\()"
    )
    for file in sorted(root.rglob("*.rs")):
        if "target" in file.relative_to(root).parts:
            continue
        if pattern.search(file.read_text(encoding="utf-8", errors="replace")):
            return file
    return None


def _compile_status(path: Path) -> bool | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("status") == "passed"


def _write_reports(store: ArtifactStore, metrics: RunMetrics) -> None:
    store.write_json("reports/metrics.json", metrics)
    store.write_text("reports/report.md", generate_markdown(metrics))
    store.write_text("reports/comparison.csv", comparison_csv(metrics))


def _apply_eligibility_metrics(metrics: RunMetrics, eligibility) -> None:
    metrics.eligibility_counts = {}
    metrics.candidate_decision_counts = {}
    for item in eligibility:
        metrics.eligibility_counts[item.category] = (
            metrics.eligibility_counts.get(item.category, 0) + 1
        )
        if item.eligible_for_safe_translation:
            metrics.eligible_units += 1
        elif item.category in {"unsupported", "unsafe_required", "requires_manual_refactor"}:
            metrics.failure_categories[item.category] = (
                metrics.failure_categories.get(item.category, 0) + 1
            )
        metrics.candidate_decision_counts[item.candidate_decision] = (
            metrics.candidate_decision_counts.get(item.candidate_decision, 0) + 1
        )
    metrics.candidate_safe_units = metrics.candidate_decision_counts.get(
        "candidate_safe", 0
    )


def _apply_synthesis_metrics(
    metrics: RunMetrics,
    plans: list[MigrationPlan],
    synthesized_units: list[str],
) -> None:
    metrics.synthesis_support_counts = {}
    for plan in plans:
        metrics.synthesis_support_counts[plan.synthesis_support] = (
            metrics.synthesis_support_counts.get(plan.synthesis_support, 0) + 1
        )
    metrics.synthesis_supported_units = metrics.synthesis_support_counts.get(
        "implemented_support", 0
    )
    metrics.generated_unit_ids = sorted(set(synthesized_units))
    metrics.generated_units = len(metrics.generated_unit_ids)


def _apply_safe_acceptance(
    metrics: RunMetrics,
    plans: list[MigrationPlan],
    validation,
    final_root: Path,
) -> None:
    final = metrics.safemap
    compile_ok = validation.compile.status == "passed"
    tests_ok = validation.tests.status in {"passed", "skipped"}
    clippy_ok = validation.clippy.status in {"passed", "skipped"}
    policy_safe_project = (
        compile_ok
        and tests_ok
        and clippy_ok
        and final is not None
        and final.unsafe_blocks == 0
        and final.unsafe_functions == 0
        and final.extern_c_blocks == 0
        and final.raw_pointer_public_api_count == 0
    )
    planned_eligible = [
        plan.unit_id for plan in plans
        if plan.eligibility in {"safe_translatable", "safe_translatable_with_api_change"}
        and plan.status == "planned"
        and _find_function_file(final_root, plan.function) is not None
    ]
    if compile_ok:
        metrics.compile_success_units = len(planned_eligible)
    if tests_ok:
        metrics.test_pass_units = len(planned_eligible)
    if validation.differential.status == "passed":
        metrics.differential_pass_units = len(planned_eligible)
    if policy_safe_project:
        metrics.policy_safe_unit_ids = list(planned_eligible)
        metrics.policy_safe_units = len(planned_eligible)
    elif planned_eligible:
        metrics.failure_categories["validation_failed"] = (
            metrics.failure_categories.get("validation_failed", 0) + len(planned_eligible)
        )
    behavioral_ok = (
        policy_safe_project
        and validation.differential.status == "passed"
        and validation.c_sanitizers.status == "passed"
    )
    if behavioral_ok:
        metrics.behaviorally_validated_unit_ids = list(planned_eligible)
        metrics.behaviorally_validated_units = len(planned_eligible)
        metrics.fully_safe_accepted_unit_ids = list(planned_eligible)
        metrics.fully_safe_accepted_units = len(planned_eligible)
    elif policy_safe_project and planned_eligible:
        category = (
            "c_oracle_undefined_behavior"
            if validation.c_sanitizers.status == "failed"
            else "behavioral_validation_missing_or_failed"
        )
        metrics.failure_categories[category] = (
            metrics.failure_categories.get(category, 0) + len(planned_eligible)
        )
    metrics.fully_safe_translation_unit_acceptance_rate = (
        metrics.fully_safe_accepted_units / metrics.eligible_units
        if metrics.eligible_units else 0.0
    )
    metrics.raw_pointer_public_api_count = {
        "baseline_c2rust": (
            metrics.baseline.raw_pointer_public_api_count if metrics.baseline else 0
        ),
        "safemap_final": (
            metrics.safemap.raw_pointer_public_api_count if metrics.safemap else 0
        ),
    }


def _write_unit_decisions(
    store: ArtifactStore,
    project: ProjectInfo,
    analysis: CAnalysis,
    units: list[TranslationUnit],
    eligibility,
    plans: list[MigrationPlan],
    metrics: RunMetrics,
) -> None:
    metadata = {}
    expected_path = Path(project.root) / "expected.json"
    if expected_path.is_file():
        metadata = json.loads(expected_path.read_text(encoding="utf-8"))
    targets = set()
    primary = metadata.get("primary_function")
    if primary:
        targets.add(str(primary))
    expected_functions = metadata.get("expected_functions")
    if isinstance(expected_functions, dict):
        targets.update(str(name) for name in expected_functions)
    entrypoints = set(project.detected_entrypoints)
    entrypoints.add("main")

    eligibility_by_function = {item.function: item for item in eligibility}
    plans_by_unit = {plan.unit_id: plan for plan in plans}
    generated = set(metrics.generated_unit_ids)
    policy_safe = set(metrics.policy_safe_unit_ids)
    behaviorally_validated = set(metrics.behaviorally_validated_unit_ids)
    decisions = []
    for unit in units:
        plan = plans_by_unit.get(unit.unit_id)
        item = eligibility_by_function.get(unit.c_function)
        function = unit.c_function
        role = (
            "declared_target"
            if function in targets
            else "entry_point"
            if function in entrypoints
            else "helper"
        )
        decisions.append({
            "project": project.project_name,
            "unit_id": unit.unit_id,
            "function": function,
            "members": unit.members,
            "role": role,
            "analysis_backend": analysis.analysis_backend,
            "legacy_eligibility": item.category if item else "unknown",
            "candidate_decision": (
                item.candidate_decision if item else "unknown"
            ),
            "candidate_reasons": item.reasons if item else ["Missing decision"],
            "synthesis_support": (
                plan.synthesis_support if plan else "not_applicable"
            ),
            "synthesis_rule": plan.synthesis_rule if plan else None,
            "plan_status": plan.status if plan else "missing",
            "generated": unit.unit_id in generated,
            "compile_passed": (
                unit.unit_id in policy_safe
                or unit.unit_id in set(metrics.generated_unit_ids)
                and metrics.safemap_compile is True
            ),
            "policy_safe": unit.unit_id in policy_safe,
            "behaviorally_validated": unit.unit_id in behaviorally_validated,
        })
    store.write_json("analysis/unit_decisions.json", decisions)

    unit_by_member = {
        member: unit
        for unit in units
        for member in unit.members
    }
    function_decisions = []
    for function in analysis.functions:
        unit = unit_by_member.get(function.name)
        plan = plans_by_unit.get(unit.unit_id) if unit else None
        item = eligibility_by_function.get(function.name)
        unit_id = unit.unit_id if unit else None
        role = (
            "declared_target"
            if function.name in targets
            else "entry_point"
            if function.name in entrypoints
            else "helper"
        )
        function_decisions.append({
            "project": project.project_name,
            "function": function.name,
            "source_file": function.file,
            "start_line": function.start_line,
            "end_line": function.end_line,
            "unit_id": unit_id,
            "role": role,
            "analysis_backend": analysis.analysis_backend,
            "analysis_backend_reason": analysis.analysis_backend_reason,
            "legacy_eligibility": item.category if item else "unknown",
            "candidate_decision": (
                item.candidate_decision if item else "unknown"
            ),
            "candidate_reasons": item.reasons if item else ["Missing decision"],
            "unsupported_features": (
                item.unsupported_features if item else []
            ),
            "pointer_roles": item.pointer_roles if item else {},
            "synthesis_support": (
                plan.synthesis_support if plan else "not_applicable"
            ),
            "synthesis_rule": plan.synthesis_rule if plan else None,
            "generated": bool(unit_id and unit_id in generated),
            "policy_safe": bool(unit_id and unit_id in policy_safe),
            "behaviorally_validated": bool(
                unit_id and unit_id in behaviorally_validated
            ),
        })
    store.write_json("analysis/function_decisions.json", function_decisions)


def _apply_research_metric_maps(metrics: RunMetrics) -> None:
    metrics.unsafe_blocks = {
        "baseline_c2rust": metrics.baseline.unsafe_blocks if metrics.baseline else 0,
        "safemap_final": metrics.safemap.unsafe_blocks if metrics.safemap else 0,
    }
    metrics.unsafe_functions = {
        "baseline_c2rust": metrics.baseline.unsafe_functions if metrics.baseline else 0,
        "safemap_final": metrics.safemap.unsafe_functions if metrics.safemap else 0,
    }
    metrics.raw_pointer_count = {
        "baseline_c2rust": metrics.baseline.raw_pointer_types if metrics.baseline else 0,
        "safemap_final": metrics.safemap.raw_pointer_types if metrics.safemap else 0,
    }
    if not metrics.raw_pointer_public_api_count:
        metrics.raw_pointer_public_api_count = {
            "baseline_c2rust": (
                metrics.baseline.raw_pointer_public_api_count if metrics.baseline else 0
            ),
            "safemap_final": (
                metrics.safemap.raw_pointer_public_api_count if metrics.safemap else 0
            ),
        }
    metrics.idiom_migrations = {
        "pointer_length_array_to_slice": metrics.migrated_idioms.get("pointer_length_array", 0),
        "output_parameter_to_return": metrics.migrated_idioms.get("output_parameter", 0),
        "nullable_pointer_to_option": metrics.migrated_idioms.get("nullable_pointer", 0),
        "error_code_to_result": metrics.migrated_idioms.get("error_code_return", 0),
        "malloc_free_to_vec_or_box": metrics.migrated_idioms.get("manual_allocation", 0),
        "c_string_to_str": metrics.migrated_idioms.get("c_string", 0),
        "boolean_int_to_bool": metrics.migrated_idioms.get("boolean_int", 0),
    }


def _record_synthesized_idioms(
    metrics: RunMetrics,
    plans: list[MigrationPlan],
    synthesized_units: list[str],
) -> None:
    generated = set(synthesized_units)
    for plan in plans:
        if plan.unit_id not in generated:
            continue
        for pattern in plan.patterns:
            metrics.migrated_idioms[pattern.pattern] = (
                metrics.migrated_idioms.get(pattern.pattern, 0) + 1
            )


def _record_tool_versions(store: ArtifactStore) -> None:
    commands = {
        "python": ["python3", "--version"],
        "clang": ["clang", "--version"],
        "c2rust": ["c2rust", "--version"],
        "cargo": ["cargo", "--version"],
        "rustc": ["rustc", "--version"],
    }
    versions = {}
    for name, command in commands.items():
        result = run_command(command, store.root)
        versions[name] = {
            "status": result.status,
            "version": (result.stdout or result.stderr).splitlines()[:1],
            "reason": result.reason,
        }
    store.write_json("tool_versions.json", versions)


def _project_loc(project: ProjectInfo) -> int:
    return sum(
        len(Path(file).read_text(encoding="utf-8", errors="replace").splitlines())
        for file in project.c_files
    )


def _direct_llm_translation(
    project: ProjectInfo,
    final_root: Path,
    client: LLMClient,
    store: ArtifactStore,
    llm_config: LLMConfig,
) -> dict[str, int | str]:
    sources = "\n\n".join(
        f"// FILE: {Path(file).name}\n"
        + Path(file).read_text(encoding="utf-8", errors="replace")
        for file in project.c_files
    )
    prompt = (
        "Translate this small C program into fully safe, idiomatic Rust while preserving "
        "its observable behavior. Return only one complete Rust source file, without "
        "Markdown fences or prose. The crate must compile with #![forbid(unsafe_code)]. "
        "Do not use unsafe, unsafe fn, unsafe impl, extern \"C\", *const, or *mut. "
        "Avoid external crates.\n\n" + sources
    )
    store.write_text("prompts/direct_translation.txt", prompt)
    call_record = {
        "schema_version": "safemap.llm_call.v1",
        "baseline": "direct_llm_c_to_safe_rust",
        "provider": llm_config.provider,
        "requested_model": llm_config.model,
        "base_url": llm_config.base_url,
        "temperature": llm_config.temperature,
        "max_tokens": llm_config.max_tokens,
        "timeout_seconds": llm_config.timeout_seconds,
        "retry_index": 0,
        "total_attempts": 1,
        "system_prompt": None,
        "prompt_path": "prompts/direct_translation.txt",
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "response_path": None,
        "status": "requested",
        "response_model": None,
        "input_tokens": None,
        "output_tokens": None,
        "failure": None,
    }
    store.write_json("logs/direct_llm_call.json", call_record)
    try:
        response = client.generate(prompt)
    except Exception as error:
        call_record["status"] = "failed"
        call_record["failure"] = {
            "type": type(error).__name__,
            "message": str(error),
        }
        store.write_json("logs/direct_llm_call.json", call_record)
        raise
    store.write_text("responses/direct_translation.txt", response.text)
    call_record.update({
        "status": "completed",
        "response_path": "responses/direct_translation.txt",
        "response_model": response.model,
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
    })
    store.write_json("logs/direct_llm_call.json", call_record)
    rust = response.text.strip()
    if rust.startswith("```"):
        lines = rust.splitlines()
        rust = "\n".join(lines[1:-1])
    reject_forbidden_constructs(rust)
    if "fn " not in rust or "{" not in rust:
        raise ValueError("Direct LLM translation did not return Rust source")
    if "#![forbid(unsafe_code)]" not in rust:
        rust = "#![forbid(unsafe_code)]\n\n" + rust
    source_dir = final_root / "src"
    source_dir.mkdir(parents=True, exist_ok=True)
    has_main = "fn main" in rust
    (source_dir / ("main.rs" if has_main else "lib.rs")).write_text(rust + "\n", encoding="utf-8")
    (final_root / "Cargo.toml").write_text(
        "[package]\n"
        f'name = "{project.project_name.replace("-", "_")}"\n'
        'version = "0.1.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n",
        encoding="utf-8",
    )
    return {
        "input_tokens": response.input_tokens,
        "output_tokens": response.output_tokens,
        "model": response.model,
    }


def _unguided_plans(units: list[TranslationUnit]) -> list[MigrationPlan]:
    return [
        MigrationPlan(
            unit_id=unit.unit_id,
            target_signature="Preserve the current Rust signature exactly",
            patterns=[PatternMigration(
                pattern="unguided_rewrite",
                original="C2Rust-generated function",
                replacement="Safer idiomatic Rust",
                confidence=1.0,
            )],
            constraints=[
                "Preserve observable C behavior",
                "Avoid unsafe where possible",
            ],
            validation_requirements=["cargo check", "cargo test"],
            function=unit.c_function,
        )
        for unit in units
    ]


def _maintainability(root: Path) -> dict:
    import re
    sources = [
        file.read_text(encoding="utf-8", errors="replace")
        for file in sorted(root.rglob("*.rs"))
        if "target" not in file.relative_to(root).parts
    ]
    source = "\n".join(sources)
    function_count = len(re.findall(r"\bfn\s+[A-Za-z_]\w*\s*(?:<|\()", source))
    loc = sum(len(item.splitlines()) for item in sources)
    return {
        "lines_of_code": loc,
        "function_count": function_count,
        "average_function_length": round(loc / function_count, 2) if function_count else 0,
        "approximate_cyclomatic_complexity": cyclomatic_complexity(source),
    }
