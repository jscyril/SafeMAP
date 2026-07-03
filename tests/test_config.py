from pathlib import Path

import pytest

from safemap.config import load_config


def test_loads_nested_yaml(tmp_path: Path) -> None:
    path = tmp_path / "safemap.yaml"
    path.write_text(
        "translation:\n"
        "  max_repair_attempts: 2\n"
        "validation:\n"
        "  run_miri: true\n"
    )
    config = load_config(path)
    assert config.translation.max_repair_attempts == 2
    assert config.validation.run_miri is True


def test_rejects_unknown_keys(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("translation:\n  imaginary: true\n")
    with pytest.raises(ValueError, match="Unknown configuration key"):
        load_config(path)


def test_loads_gemini_config() -> None:
    config = load_config("safemap.gemini.yaml")

    assert config.llm.api_key_env == "GEMINI_API_KEY"
    assert config.llm.model == "gemini-3.5-flash"
    assert config.llm.base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_loads_ollama_config() -> None:
    config = load_config("safemap.ollama.yaml")

    assert config.llm.api_key_env == "OLLAMA_API_KEY"
    assert config.llm.model == "gemma4:12b"
    assert config.llm.base_url == "http://localhost:11434/v1"
