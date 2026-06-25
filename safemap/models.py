from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar, get_args, get_origin, get_type_hints

SCHEMA_VERSION = "1.0"
T = TypeVar("T")


def _encode(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {f.name: _encode(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    return value


def _decode(annotation: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(annotation)
    args = get_args(annotation)
    if origin is list:
        subtype = args[0] if args else Any
        return [_decode(subtype, item) for item in value]
    if origin is dict:
        value_type = args[1] if len(args) == 2 else Any
        return {key: _decode(value_type, item) for key, item in value.items()}
    if origin is not None and type(None) in args:
        subtype = next(item for item in args if item is not type(None))
        return _decode(subtype, value)
    if annotation is Path:
        return Path(value)
    if isinstance(annotation, type) and dataclasses.is_dataclass(annotation):
        return from_dict(annotation, value)
    return value


def from_dict(cls: type[T], data: dict[str, Any]) -> T:
    hints = get_type_hints(cls)
    values = {
        field.name: _decode(hints.get(field.name, Any), data[field.name])
        for field in dataclasses.fields(cls)
        if field.name in data
    }
    return cls(**values)


class JsonModel:
    def to_dict(self) -> dict[str, Any]:
        return _encode(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass
class CommandResult(JsonModel):
    command: list[str]
    cwd: str
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    duration_seconds: float = 0.0
    status: str = "passed"
    reason: str | None = None


@dataclass
class ProjectInfo(JsonModel):
    schema_version: str = SCHEMA_VERSION
    project_name: str = ""
    root: str = ""
    input_path: str = ""
    c_files: list[str] = field(default_factory=list)
    header_files: list[str] = field(default_factory=list)
    build_files: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    build_system: str = "unknown"
    compile_commands: str | None = None
    test_commands: list[list[str]] = field(default_factory=list)
    detected_entrypoints: list[str] = field(default_factory=list)
    created_at: str = ""


@dataclass
class ParameterInfo(JsonModel):
    name: str
    c_type: str
    is_pointer: bool = False
    is_const: bool = False


@dataclass
class PointerFact(JsonModel):
    variable: str
    pointer_type: str
    usage_kind: str
    evidence: str
    confidence: float


@dataclass
class DetectedIdiom(JsonModel):
    idiom_type: str
    location: str
    variables: list[str]
    suggested_rust_pattern: str
    confidence: float
    evidence: str


@dataclass
class EligibilityResult(JsonModel):
    unit_id: str
    function: str
    category: str
    reasons: list[str] = field(default_factory=list)
    unsupported_features: list[str] = field(default_factory=list)
    pointer_roles: dict[str, list[str]] = field(default_factory=dict)
    eligible_for_safe_translation: bool = False


@dataclass
class FunctionInfo(JsonModel):
    name: str
    return_type: str
    parameters: list[ParameterInfo]
    body: str
    file: str
    start_line: int
    end_line: int
    calls: list[str] = field(default_factory=list)
    pointer_facts: list[PointerFact] = field(default_factory=list)
    idioms: list[DetectedIdiom] = field(default_factory=list)


@dataclass
class StructInfo(JsonModel):
    name: str
    fields: list[dict[str, str]]
    file: str
    line: int


@dataclass
class GlobalInfo(JsonModel):
    name: str
    c_type: str
    mutable: bool
    file: str
    line: int


@dataclass
class CAnalysis(JsonModel):
    schema_version: str = SCHEMA_VERSION
    functions: list[FunctionInfo] = field(default_factory=list)
    structs: list[StructInfo] = field(default_factory=list)
    globals: list[GlobalInfo] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


@dataclass
class RustMetrics(JsonModel):
    unsafe_blocks: int = 0
    unsafe_functions: int = 0
    raw_pointer_types: int = 0
    raw_pointer_dereferences: int = 0
    transmute_calls: int = 0
    ffi_calls: int = 0
    libc_usages: int = 0
    extern_c_blocks: int = 0
    raw_pointer_public_api_count: int = 0
    unsafe_lines: int = 0
    candidate_functions_for_rewrite: list[str] = field(default_factory=list)


@dataclass
class TranslationUnit(JsonModel):
    unit_id: str
    kind: str
    c_function: str
    rust_function: str
    dependencies: list[str]
    priority: float
    reason: str
    members: list[str] = field(default_factory=list)


@dataclass
class PatternMigration(JsonModel):
    pattern: str
    original: str
    replacement: str
    confidence: float


@dataclass
class MigrationPlan(JsonModel):
    unit_id: str
    target_signature: str
    patterns: list[PatternMigration]
    constraints: list[str]
    validation_requirements: list[str]
    source_file: str = ""
    function: str = ""
    eligibility: str = "unsupported"
    eligibility_reasons: list[str] = field(default_factory=list)
    detected_idioms: list[dict[str, Any]] = field(default_factory=list)
    original_signature: str = ""
    type_migrations: list[dict[str, str]] = field(default_factory=list)
    safety_constraints: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    status: str = "planned"
    reason: str | None = None


@dataclass
class CompilerDiagnostic(JsonModel):
    code: str | None
    level: str
    message: str
    rendered: str = ""
    file: str | None = None
    line: int | None = None
    column: int | None = None


@dataclass
class ValidationCheck(JsonModel):
    status: str
    command: CommandResult | None = None
    errors: list[CompilerDiagnostic] = field(default_factory=list)
    passed: int | None = None
    failed: int | None = None
    reason: str | None = None


@dataclass
class ValidationResult(JsonModel):
    compile: ValidationCheck
    tests: ValidationCheck
    clippy: ValidationCheck
    miri: ValidationCheck
    differential: ValidationCheck


@dataclass
class RunMetrics(JsonModel):
    schema_version: str = SCHEMA_VERSION
    project: str = ""
    baseline: RustMetrics | None = None
    safemap: RustMetrics | None = None
    baseline_compile: bool | None = None
    safemap_compile: bool | None = None
    test_pass_rate: float | None = None
    differential_pass_rate: float | None = None
    total_units: int = 0
    eligible_units: int = 0
    fully_safe_accepted_units: int = 0
    fully_safe_translation_unit_acceptance_rate: float = 0.0
    compile_success_units: int = 0
    test_pass_units: int = 0
    differential_pass_units: int = 0
    raw_pointer_public_api_count: dict[str, int] = field(default_factory=dict)
    unsafe_blocks: dict[str, int] = field(default_factory=dict)
    unsafe_functions: dict[str, int] = field(default_factory=dict)
    raw_pointer_count: dict[str, int] = field(default_factory=dict)
    idiom_migrations: dict[str, int] = field(default_factory=dict)
    eligibility_counts: dict[str, int] = field(default_factory=dict)
    failure_categories: dict[str, int] = field(default_factory=dict)
    fully_safe_accepted_unit_ids: list[str] = field(default_factory=list)
    repair_attempts: int = 0
    llm_calls: int = 0
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    translation_seconds: float = 0.0
    original_runtime_seconds: float | None = None
    rust_runtime_seconds: float | None = None
    maintainability: dict[str, Any] = field(default_factory=dict)
    migrated_idioms: dict[str, int] = field(default_factory=dict)
    failed_units: list[dict[str, str]] = field(default_factory=list)
    residual_unsafe: list[dict[str, Any]] = field(default_factory=list)
