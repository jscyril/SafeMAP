from pathlib import Path

import pytest

from scripts.freeze_conference_implementation import (
    _assert_no_runtime_config_overrides,
    validate_conference_config,
)


def _config(model: str) -> str:
    return f"""
translation:
  use_static_guidance: true
  use_pointer_roles: true
  use_safe_signatures: true
  use_dependency_grouping: true
  use_idiom_plans: true
  use_validation_feedback: true
  forbid_unsafe: true
llm:
  model: {model}
  temperature: 0.0
validation:
  differential_test_inputs: 1000
  run_c_sanitizers: true
"""


def test_freeze_config_rejects_placeholder_model(
    tmp_path: Path,
) -> None:
    path = tmp_path / "conference.yaml"
    path.write_text(
        _config("REPLACE_WITH_FROZEN_BASELINE_MODEL"),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exact competitive-baseline"):
        validate_conference_config(path)


def test_freeze_config_accepts_fully_specified_protocol(
    tmp_path: Path,
) -> None:
    path = tmp_path / "conference.yaml"
    path.write_text(
        _config("provider-model-version"),
        encoding="utf-8",
    )

    parsed = validate_conference_config(path)

    assert parsed["llm"]["model"] == "provider-model-version"


def test_freeze_rejects_runtime_model_override(monkeypatch) -> None:
    monkeypatch.setenv("SAFEMAP_MODEL", "different-model")

    with pytest.raises(ValueError, match="SAFEMAP_MODEL"):
        _assert_no_runtime_config_overrides()
