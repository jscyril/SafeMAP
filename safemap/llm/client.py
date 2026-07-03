from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..config import LLMConfig


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    raw: dict | None = None


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleClient(LLMClient):
    def __init__(self, config: LLMConfig):
        self.config = config

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        key = os.getenv(self.config.api_key_env)
        if not key:
            raise RuntimeError(_missing_key_message(self.config))
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        payload = json.dumps({
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }).encode("utf-8")
        request = urllib.request.Request(
            self.config.base_url.rstrip("/") + "/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                request, timeout=self.config.timeout_seconds
            ) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as error:
            details = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                _http_error_message(error.code, details, self.config)
            ) from error
        except urllib.error.URLError as error:
            raise RuntimeError(
                "LLM request failed before receiving a response. "
                f"Provider={self.config.provider}, model={self.config.model}, "
                f"base_url={self.config.base_url}. Underlying error: {error.reason}"
            ) from error
        usage = data.get("usage", {})
        return LLMResponse(
            text=data["choices"][0]["message"]["content"],
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            model=data.get("model", self.config.model),
            raw=data,
        )


class StaticLLMClient(LLMClient):
    """Deterministic client for tests and offline experiments."""

    def __init__(self, responses: dict[str, str] | list[str]):
        self.responses = responses
        self.index = 0

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        if isinstance(self.responses, dict):
            for marker, response in self.responses.items():
                if marker in prompt:
                    return LLMResponse(response, model="static")
            raise KeyError("No static LLM response matched the prompt")
        if self.index >= len(self.responses):
            raise IndexError("Static LLM responses exhausted")
        response = self.responses[self.index]
        self.index += 1
        return LLMResponse(response, model="static")


def _missing_key_message(config: LLMConfig) -> str:
    return (
        f"Missing API key environment variable `{config.api_key_env}` for "
        f"provider `{config.provider}` model `{config.model}` at `{config.base_url}`. "
        "Add the key to your environment or .env file before running LLM modes. "
        "For local OpenAI-compatible endpoints such as Ollama, set the configured "
        "API key variable to a placeholder value such as `dummy` if the server does "
        "not enforce authentication."
    )


def _http_error_message(code: int, details: str, config: LLMConfig) -> str:
    context = (
        f"LLM request failed with HTTP {code}. Provider={config.provider}, "
        f"model={config.model}, base_url={config.base_url}. "
    )
    normalized = details.lower()
    if code == 401 or "invalid api key" in normalized or "unauthorized" in normalized:
        return context + (
            f"Authentication failed. Check `{config.api_key_env}` and make sure "
            "the key belongs to the configured provider. Response: "
            f"{_compact(details)}"
        )
    if code == 429 or "quota" in normalized or "rate limit" in normalized:
        return context + (
            "Rate limit or quota was reached. Wait for the provider quota window "
            "to reset, reduce benchmark modes, or switch to a local/provider model "
            "with available capacity. Response: "
            f"{_compact(details)}"
        )
    if code == 404 and "model" in normalized:
        return context + (
            "The configured model was not found. Check the model name and provider "
            f"base URL. Response: {_compact(details)}"
        )
    return context + f"Response: {_compact(details)}"


def _compact(text: str, limit: int = 800) -> str:
    compacted = " ".join(text.split())
    return compacted if len(compacted) <= limit else compacted[: limit - 3] + "..."
