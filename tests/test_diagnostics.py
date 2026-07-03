from safemap.config import LLMConfig
from safemap.llm.client import _http_error_message, _missing_key_message
from safemap.models import CommandResult
from safemap.translation.c2rust_runner import (
    _diagnose_c2rust_compile_failure,
    _diagnose_c2rust_failure,
)
from safemap.validation.miri_runner import _miri_unsupported_reason


def test_llm_missing_key_message_names_provider_and_env() -> None:
    message = _missing_key_message(
        LLMConfig(
            provider="openai_compatible",
            model="gemini-3.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key_env="GEMINI_API_KEY",
        )
    )

    assert "GEMINI_API_KEY" in message
    assert "gemini-3.5-flash" in message
    assert "dummy" in message


def test_llm_quota_message_is_actionable() -> None:
    message = _http_error_message(
        429,
        '{"error": {"message": "quota exceeded"}}',
        LLMConfig(model="gemini-3.5-flash"),
    )

    assert "Rate limit or quota" in message
    assert "gemini-3.5-flash" in message


def test_c2rust_libclang_failure_has_llvm_guidance() -> None:
    result = CommandResult(
        command=["c2rust", "transpile"],
        cwd=".",
        exit_code=1,
        stderr="error while loading shared libraries: libclang.so: cannot open",
        status="failed",
    )

    assert "SAFEMAP_C2RUST_LIB_DIR" in _diagnose_c2rust_failure(result)


def test_c2rust_nightly_feature_failure_is_baseline_compile_issue() -> None:
    result = CommandResult(
        command=["cargo", "check"],
        cwd=".",
        exit_code=1,
        stderr="#![feature(raw_ref_op)] may not be used on the stable release channel",
        status="failed",
    )

    assert "baseline compile failure" in _diagnose_c2rust_compile_failure(result)


def test_miri_missing_component_is_unsupported() -> None:
    reason = _miri_unsupported_reason("error: no such command: `miri`")

    assert reason is not None
    assert "rustup component add miri" in reason
