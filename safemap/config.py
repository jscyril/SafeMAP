from __future__ import annotations

import dataclasses
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectConfig:
    name: str | None = None
    input: str | None = None


@dataclass
class TranslationConfig:
    mode: str = "safemap_full"
    use_c2rust: bool = True
    use_llm: bool = True
    use_static_guidance: bool = True
    forbid_unsafe: bool = True
    allow_c2rust_fallback_as_success: bool = False
    max_units: int | None = None
    max_repair_attempts: int = 5
    direct_llm_max_c_loc: int = 500
    automatic_confidence_threshold: float = 0.75


@dataclass
class LLMConfig:
    provider: str = "openai_compatible"
    model: str = "configurable-model-name"
    base_url: str = "https://api.openai.com/v1"
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout_seconds: float = 120.0
    api_key_env: str = "OPENAI_API_KEY"


@dataclass
class ValidationConfig:
    run_cargo_check: bool = True
    run_tests: bool = True
    run_clippy: bool = True
    run_miri: bool = False
    run_differential_tests: bool = True
    cargo_check: bool | None = None
    cargo_test: bool | None = None
    clippy: bool | None = None
    miri: bool | None = None
    differential_testing: bool | None = None
    differential_test_inputs: int = 1000
    seed: int = 0
    timeout_seconds: float = 120.0


@dataclass
class MetricsConfig:
    count_unsafe: bool = True
    count_raw_pointers: bool = True
    count_clippy_warnings: bool = True


@dataclass
class EligibilityConfig:
    reject_unknown_pointers: bool = True
    reject_unresolved_aliasing: bool = True
    reject_unions: bool = True
    reject_function_pointers: bool = True
    reject_inline_asm: bool = True


@dataclass
class RepairConfig:
    enabled: bool = True
    max_iterations: int = 3
    forbid_unsafe: bool = True


@dataclass
class ReportingConfig:
    write_markdown: bool = True
    write_json: bool = True
    write_csv: bool = True


@dataclass
class SafeMapConfig:
    project: ProjectConfig = field(default_factory=ProjectConfig)
    translation: TranslationConfig = field(default_factory=TranslationConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    eligibility: EligibilityConfig = field(default_factory=EligibilityConfig)
    repair: RepairConfig = field(default_factory=RepairConfig)
    reporting: ReportingConfig = field(default_factory=ReportingConfig)


def _merge_dataclass(instance: Any, values: dict[str, Any]) -> Any:
    valid = {item.name for item in dataclasses.fields(instance)}
    for key, value in values.items():
        if key not in valid:
            raise ValueError(f"Unknown configuration key: {key}")
        current = getattr(instance, key)
        if dataclasses.is_dataclass(current) and isinstance(value, dict):
            _merge_dataclass(current, value)
        else:
            setattr(instance, key, value)
    return instance


def load_config(path: str | Path | None = None) -> SafeMapConfig:
    config = SafeMapConfig()
    raw: dict[str, Any] = {}
    if path:
        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError("Configuration root must be a mapping")
        _merge_dataclass(config, raw)
    if os.getenv("SAFEMAP_MODEL"):
        config.llm.model = os.environ["SAFEMAP_MODEL"]
    if os.getenv("SAFEMAP_BASE_URL"):
        config.llm.base_url = os.environ["SAFEMAP_BASE_URL"]
    _normalize_aliases(config, raw)
    return config


def _normalize_aliases(config: SafeMapConfig, raw: dict[str, Any]) -> None:
    validation = config.validation
    if validation.cargo_check is not None:
        validation.run_cargo_check = validation.cargo_check
    if validation.cargo_test is not None:
        validation.run_tests = validation.cargo_test
    if validation.clippy is not None:
        validation.run_clippy = validation.clippy
    if validation.miri is not None:
        validation.run_miri = validation.miri
    if validation.differential_testing is not None:
        validation.run_differential_tests = validation.differential_testing
    if "repair" in raw:
        config.translation.max_repair_attempts = config.repair.max_iterations
