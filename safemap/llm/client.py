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
            raise RuntimeError(
                f"Missing API key environment variable: {self.config.api_key_env}"
            )
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
            raise RuntimeError(f"LLM request failed with HTTP {error.code}: {details}") from error
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

