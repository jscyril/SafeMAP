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


def test_load_dotenv_keeps_shell_values(tmp_path, monkeypatch) -> None:
    from safemap.cli import load_dotenv
    env = tmp_path / ".env"
    env.write_text("# comment\nSM_A=from_file\nSM_B='quoted'\nSM_C=\n# SM_D=off\n", encoding="utf-8")
    monkeypatch.setenv("SM_A", "from_shell")
    for name in ("SM_B", "SM_C", "SM_D"):
        monkeypatch.delenv(name, raising=False)
    load_dotenv(env)
    import os
    assert os.environ["SM_A"] == "from_shell"
    assert os.environ["SM_B"] == "quoted"
    assert os.environ["SM_C"] == ""
    assert "SM_D" not in os.environ


def test_fallback_client_moves_on_only_when_a_provider_is_exhausted() -> None:
    from safemap.llm.client import (
        FallbackLLMClient, LLMClient, LLMResponse, MissingAPIKey, ProviderUnavailable,
        QuotaExhausted, _is_daily_quota,
    )

    class Fake(LLMClient):
        def __init__(self, behavior):
            self.behavior, self.calls = behavior, 0

        def generate(self, prompt, system_prompt=None, *, max_tokens=None, timeout=None):
            self.calls += 1
            if isinstance(self.behavior, Exception):
                raise self.behavior
            return LLMResponse(self.behavior, model=self.behavior)

    gemini = Fake(QuotaExhausted("per day"))
    nvidia = Fake(MissingAPIKey("no key"))
    groq = Fake("groq")
    client = FallbackLLMClient([gemini, nvidia, groq], ["gemini", "nvidia", "groq"])
    assert client.generate("p").model == "groq"
    assert client.generate("p").model == "groq"
    assert gemini.calls == 1  # an exhausted provider is not retried
    assert [item["to"] for item in client.switches] == ["nvidia", "groq"]

    # Ordinary errors are not a reason to switch.
    broken = FallbackLLMClient([Fake(ValueError("bad")), Fake("x")], ["a", "b"])
    try:
        broken.generate("p")
    except ValueError:
        pass
    assert broken.index == 0

    last = FallbackLLMClient([Fake(QuotaExhausted("q"))], ["only"])
    try:
        last.generate("p")
        raise AssertionError("expected ProviderUnavailable")
    except ProviderUnavailable as error:
        assert "All providers exhausted" in str(error)

    assert _is_daily_quota('{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}')
    assert _is_daily_quota("Rate limit reached on tokens per day (TPD)")
    assert not _is_daily_quota("Rate limit reached on tokens per minute (TPM)")


def test_build_client_applies_fallback_overrides() -> None:
    from safemap.config import LLMConfig
    from safemap.llm.client import FallbackLLMClient, build_client
    config = LLMConfig(model="primary", api_key_env="A", fallbacks=[
        {"model": "second", "base_url": "https://b", "api_key_env": "B"},
    ])
    client = build_client(config)
    assert isinstance(client, FallbackLLMClient)
    second = client.clients[1].config
    assert (second.model, second.base_url, second.api_key_env) == ("second", "https://b", "B")
    assert second.temperature == config.temperature and second.fallbacks == []
